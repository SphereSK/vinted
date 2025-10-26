"""Listings endpoints."""
import json
from typing import Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import (
    ListingDetail,
    ListingListResponse,
    ListingResponse,
    PriceHistoryResponse,
    ConditionResponse,
    SourceResponse,
)
from app.db.models import (
    Listing,
    PriceHistory,
    CategoryOption,
    PlatformOption,
    ConditionOption,
    SourceOption,
)
from app.utils.conditions import normalize_condition
from app.utils.logging import get_logger
from fastAPI.dependencies import get_db, require_api_key
from fastAPI.redis import get_redis

router = APIRouter(
    prefix="/api",
    tags=["listings"],
    dependencies=[Depends(require_api_key)],
)

logger = get_logger(__name__)

SORTABLE_FIELDS = {
    "last_seen_at": "last_seen_at",
    "first_seen_at": "first_seen_at",
    "price": "price_cents",
    "title": "title",
    "condition": "condition_option_id",
    "category_id": "category_id",
    "source": "source_option_id",
    "platform_ids": "platform_ids",
}



async def load_listings_to_cache(db: AsyncSession, redis):
    logger.info("Clearing listings cache...")
    keys = await redis.keys("listings:*")
    if keys:
        await redis.delete(*keys)

    logger.info("Loading listings to cache...")
    listings_query = select(Listing).options(selectinload(Listing.prices)).where(Listing.is_active.is_(True))
    listings_result = await db.execute(listings_query)
    listings = listings_result.scalars().all()

    # Load master data for lookups
    category_records = (await db.execute(select(CategoryOption.id, CategoryOption.name))).all()
    categories_map = {row.id: row.name for row in category_records}
    await redis.set("categories", json.dumps([row._asdict() for row in category_records]), ex=3600)

    platform_records = (await db.execute(select(PlatformOption.id, PlatformOption.name))).all()
    platforms_map = {row.id: row.name for row in platform_records}
    await redis.set("platforms", json.dumps([row._asdict() for row in platform_records]), ex=3600)

    condition_records = (await db.execute(select(ConditionOption.id, ConditionOption.code, ConditionOption.label))).all()
    conditions_map = {row.id: row for row in condition_records}
    await redis.set("conditions", json.dumps([row._asdict() for row in condition_records]), ex=3600)

    source_records = (await db.execute(select(SourceOption.id, SourceOption.code, SourceOption.label))).all()
    sources_map = {row.id: row for row in source_records}
    await redis.set("sources", json.dumps([row._asdict() for row in source_records]), ex=3600)

    enriched_listings = []
    for listing in listings:
        logger.debug(f"Processing listing ID: {listing.id}")
        logger.debug(f"Listing condition_option: {listing.condition_option}")
        logger.debug(f"Listing source_option: {listing.source_option}")
        logger.debug(f"Listing platform_ids: {listing.platform_ids}")
        logger.debug(f"Listing price_cents: {listing.price_cents}")

        listing_dict = ListingResponse.from_orm(listing).model_dump()

        # Calculate price_change from PriceHistory
        previous_price_cents = None
        if listing.prices:
            # Sort prices by observed_at descending
            sorted_prices = sorted(listing.prices, key=lambda p: p.observed_at, reverse=True)
            for price_entry in sorted_prices:
                if price_entry.price_cents is not None and price_entry.price_cents != listing.price_cents:
                    previous_price_cents = price_entry.price_cents
                    break

        if listing.price_cents is not None and previous_price_cents is not None:
            if listing.price_cents > previous_price_cents:
                listing_dict["price_change"] = "up"
            elif listing.price_cents < previous_price_cents:
                listing_dict["price_change"] = "down"
            else:
                listing_dict["price_change"] = "same"
            listing_dict["previous_price_cents"] = previous_price_cents
        else:
            listing_dict["price_change"] = None
            listing_dict["previous_price_cents"] = None

        # Populate condition_label and condition_code
        if listing.condition_option:
            condition_obj = listing.condition_option
            listing_dict["condition_label"] = condition_obj.label
            listing_dict["condition_code"] = condition_obj.code
        elif listing.condition:
            _, listing_dict["condition_code"], listing_dict["condition_label"] = normalize_condition(listing.condition)
        else:
            listing_dict["condition_label"] = None
            listing_dict["condition_code"] = None

        # Populate source_label and source_code
        if listing.source_option:
            source_obj = listing.source_option
            listing_dict["source_label"] = source_obj.label
            listing_dict["source_code"] = source_obj.code
        else:
            listing_dict["source_label"] = None
            listing_dict["source_code"] = None

        # Populate platform_names
        if listing.platform_ids:
            listing_dict["platform_names"] = [
                platforms_map.get(pid, f"#{pid}") for pid in listing.platform_ids
            ]
        else:
            listing_dict["platform_names"] = []

        # Populate category_name
        if listing.category_id and listing.category_id in categories_map:
            listing_dict["category_name"] = categories_map[listing.category_id]
        else:
            listing_dict["category_name"] = None

        # Convert datetime objects to ISO 8601 strings for JSON serialization
        for key, value in listing_dict.items():
            if isinstance(value, datetime):
                listing_dict[key] = value.isoformat()

        final_json_listing = json.dumps(listing_dict)
        logger.debug(f"Final JSON for listing ID {listing.id}: {final_json_listing}")
        enriched_listings.append(final_json_listing)

    await redis.set("listings", json.dumps(enriched_listings), ex=3600)
    logger.info("Listings loaded to cache.")


@router.post("/listings/load")
async def load_listings_endpoint(db: AsyncSession = Depends(get_db)):
    redis = get_redis()
    if not redis:
        raise HTTPException(status_code=500, detail="Redis not available.")
    await load_listings_to_cache(db, redis)
    return {"message": "Listings loaded to cache."}


@router.get("/listings", response_model=ListingListResponse)
async def list_listings(
    search: Optional[str] = None,
    active_only: bool = True,
    sort_field: str = Query("last_seen_at"),
    sort_order: str = Query("desc"),
    currency: Optional[str] = None,
    price_min: Optional[int] = Query(None, ge=0, description="Minimum price in cents"),
    price_max: Optional[int] = Query(None, ge=0, description="Maximum price in cents"),
    condition_id: Optional[int] = Query(None, ge=1),
    condition: Optional[str] = Query(
        None, description="Filter by condition label or code"
    ),
    category_id: Optional[int] = Query(None, ge=1),
    platform_id: Optional[int] = Query(None, ge=1),
    source_id: Optional[int] = Query(None, ge=1),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> ListingListResponse:
    """Return listings with optional search and pagination."""
    redis = get_redis()
    if not redis:
        raise HTTPException(status_code=500, detail="Redis not available.")

    # Construct a cache key based on the query parameters
    cache_key = f"listings:{search}:{active_only}:{sort_field}:{sort_order}:{currency}:{price_min}:{price_max}:{condition_id}:{condition}:{category_id}:{platform_id}:{source_id}:{source}:{page}:{page_size}"

    # Try to fetch the data from the cache
    cached_data = await redis.get(cache_key)
    if cached_data:
        logger.info("Serving from cache")
        return json.loads(cached_data)

    logger.info("Serving from database")

    # Build the query
    query = select(Listing).options(selectinload(Listing.prices))

    if active_only:
        query = query.where(Listing.is_active.is_(True))
    if search:
        query = query.where(Listing.title.ilike(f"%{search}%"))
    if currency:
        query = query.where(Listing.currency == currency)
    if price_min is not None:
        query = query.where(Listing.price_cents >= price_min)
    if price_max is not None:
        query = query.where(Listing.price_cents <= price_max)
    if condition_id is not None:
        query = query.where(Listing.condition_option_id == condition_id)
    if category_id is not None:
        query = query.where(Listing.category_id == category_id)
    if platform_id is not None:
        query = query.where(Listing.platform_ids.contains([platform_id]))
    if source_id is not None:
        query = query.where(Listing.source_option_id == source_id)

    # Sorting
    sort_column = SORTABLE_FIELDS.get(sort_field.lower())
    if sort_column:
        if sort_order == "desc":
            query = query.order_by(getattr(Listing, sort_column).desc())
        else:
            query = query.order_by(getattr(Listing, sort_column).asc())

    # Pagination
    if limit:
        query = query.limit(limit)
        total = limit
        page = 1
        page_size = limit
    else:
        # Count the total number of items
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

    # Execute the query
    listings_result = await db.execute(query)
    listings = listings_result.scalars().all()

    # Enrich the listings with related data
    enriched_listings = []
    for listing in listings:
        listing_dict = ListingResponse.from_orm(listing).model_dump()

        # Calculate price_change from PriceHistory
        previous_price_cents = None
        if listing.prices:
            sorted_prices = sorted(listing.prices, key=lambda p: p.observed_at, reverse=True)
            for price_entry in sorted_prices:
                if price_entry.price_cents is not None and price_entry.price_cents != listing.price_cents:
                    previous_price_cents = price_entry.price_cents
                    break

        if listing.price_cents is not None and previous_price_cents is not None:
            if listing.price_cents > previous_price_cents:
                listing_dict["price_change"] = "up"
            elif listing.price_cents < previous_price_cents:
                listing_dict["price_change"] = "down"
            else:
                listing_dict["price_change"] = "same"
            listing_dict["previous_price_cents"] = previous_price_cents
        else:
            listing_dict["price_change"] = None
            listing_dict["previous_price_cents"] = None

        # Populate condition_label and condition_code
        if listing.condition_option:
            condition_obj = listing.condition_option
            listing_dict["condition_label"] = condition_obj.label
            listing_dict["condition_code"] = condition_obj.code
        elif listing.condition:
            _, listing_dict["condition_code"], listing_dict["condition_label"] = normalize_condition(listing.condition)
        else:
            listing_dict["condition_label"] = None
            listing_dict["condition_code"] = None

        # Populate source_label and source_code
        if listing.source_option:
            source_obj = listing.source_option
            listing_dict["source_label"] = source_obj.label
            listing_dict["source_code"] = source_obj.code
        else:
            listing_dict["source_label"] = None
            listing_dict["source_code"] = None

        # Populate platform_names
        if listing.platform_ids:
            platform_records = (await db.execute(select(PlatformOption.id, PlatformOption.name).where(PlatformOption.id.in_(listing.platform_ids)))).all()
            platforms_map = {row.id: row.name for row in platform_records}
            listing_dict["platform_names"] = [
                platforms_map.get(pid, f"#{pid}") for pid in listing.platform_ids
            ]
        else:
            listing_dict["platform_names"] = []

        # Populate category_name
        if listing.category_id:
            category_record = (await db.execute(select(CategoryOption.name).where(CategoryOption.id == listing.category_id))).scalar_one_or_none()
            listing_dict["category_name"] = category_record
        else:
            listing_dict["category_name"] = None

        # Convert datetime objects to ISO 8601 strings for JSON serialization
        for key, value in listing_dict.items():
            if isinstance(value, datetime):
                listing_dict[key] = value.isoformat()

        enriched_listings.append(listing_dict)

    # Master data
    categories = json.loads(await redis.get("categories") or "[]")
    platforms = json.loads(await redis.get("platforms") or "[]")
    conditions = json.loads(await redis.get("conditions") or "[]")
    sources = json.loads(await redis.get("sources") or "[]")

    response = ListingListResponse(
        items=enriched_listings,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        available_currencies=sorted(list(set(l["currency"] for l in enriched_listings if l["currency"]))),
        available_conditions=[ConditionResponse(**c) for c in conditions],
        available_category_ids=[c["id"] for c in categories],
        available_platform_ids=[p["id"] for p in platforms],
        available_sources=[SourceResponse(**s) for s in sources],
    )

    # Cache the response
    await redis.set(cache_key, response.model_dump_json(), ex=3600)

    return response

@router.post("/listings/cache/clear")
async def clear_listings_cache():
    """Clear the Redis cache for listings."""
    redis = get_redis()
    if redis:
        await redis.delete("listings", "categories", "platforms", "conditions", "sources")
        logger.info("Cleared listings cache.")
        return {"message": "Cleared listings cache."}
    return {"message": "Redis not available."}


@router.get("/listings/{listing_id}", response_model=ListingDetail)
async def get_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
) -> ListingDetail:
    """Return a single listing with price history entries."""
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    price_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.observed_at.desc())
    )
    prices = price_result.scalars().all()

    listing_dict = dict(listing.__dict__)
    listing_dict.pop("_sa_instance_state", None)

    return ListingDetail(
        **listing_dict,
        price_history=[
            PriceHistoryResponse.model_validate(p) for p in prices
        ],
    )
