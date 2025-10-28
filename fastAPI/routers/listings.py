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
import math

from app.api.schemas import (
    ListingDetail,
    ListingListResponse,
    ListingResponse,
    PriceHistoryResponse,
    ConditionResponse,
    SourceResponse,
    CategoryResponse,
    PlatformResponse,
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
    "price_change": "price_change",
}



async def load_listings_to_cache(db: AsyncSession, redis):
    logger.info("Clearing listings cache...")
    keys = await redis.keys("listings:*")
    if keys:
        await redis.delete(*keys)

    logger.info("Loading listings to cache...")
    listings_query = select(Listing).options(selectinload(Listing.prices))
    listings_result = await db.execute(listings_query)
    listings = listings_result.scalars().all()
    logger.info(f"Found {len(listings)} listings to load into cache.")

    # Load master data for lookups
    category_records = (await db.execute(select(CategoryOption.id, CategoryOption.name, CategoryOption.color))).all()
    categories_map = {row.id: row.name for row in category_records}
    await redis.set("categories", json.dumps([row._asdict() for row in category_records]), ex=3600)

    platform_records = (await db.execute(select(PlatformOption.id, PlatformOption.name, PlatformOption.color))).all()
    platforms = [row._asdict() for row in platform_records]
    platforms_map = {row.id: row.name for row in platform_records}
    await redis.set("platforms", json.dumps([row._asdict() for row in platform_records]), ex=3600)

    condition_records = (await db.execute(select(ConditionOption.id, ConditionOption.code, ConditionOption.label, ConditionOption.color))).all()
    conditions_map = {row.id: row for row in condition_records}
    await redis.set("conditions", json.dumps([row._asdict() for row in condition_records]), ex=3600)

    source_records = (await db.execute(select(SourceOption.id, SourceOption.code, SourceOption.label, SourceOption.color))).all()
    sources_map = {row.id: row for row in source_records}
    await redis.set("sources", json.dumps([row._asdict() for row in source_records]), ex=3600)

    enriched_listings = []
    for listing in listings:
        logger.debug(f"Processing listing ID: {listing.id}")
        logger.debug(f"Listing condition_option: {listing.condition_option}")
        logger.debug(f"Listing source_option: {listing.source_option}")
        logger.debug(f"Listing platform_ids: {listing.platform_ids}")
        logger.debug(f"Listing price_cents: {listing.price_cents}")
        logger.debug(f"Listing is_sold: {listing.is_sold}")

        listing_data = {
            "id": listing.id,
            "url": listing.url,
            "first_seen_at": listing.first_seen_at,
            "last_seen_at": listing.last_seen_at,
            "is_active": listing.is_active,
            "is_visible": listing.is_visible,
            "is_sold": listing.is_sold,
            "details_scraped": listing.details_scraped,
            "title": listing.title,
            "price_cents": listing.price_cents,
            "currency": listing.currency,
            "brand": listing.brand,
            "condition": listing.condition,
            "location": listing.location,
            "seller_name": listing.seller_name,
            "photo": listing.photo,
            "description": listing.description,
            "language": listing.language,
            "source": listing.source,
            "category_id": listing.category_id,
            "platform_ids": list(listing.platform_ids) if listing.platform_ids is not None else None,
            "vinted_id": listing.vinted_id,
            "condition_option_id": listing.condition_option_id,
            "source_option_id": listing.source_option_id,
        }
        listing_dict = ListingResponse(**listing_data).model_dump()

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
            listing_dict["source_option_id"] = source_obj.id
        elif listing.source:
            # Fallback: try to find source by code if source_option is not loaded
            source_map_by_code = {s.code: s for s in sources_map.values()}
            found_source = source_map_by_code.get(listing.source)
            if found_source:
                listing_dict["source_label"] = found_source.label
                listing_dict["source_code"] = found_source.code
                listing_dict["source_option_id"] = found_source.id
            else:
                listing_dict["source_label"] = None
                listing_dict["source_code"] = None
                listing_dict["source_option_id"] = None
        else:
            listing_dict["source_label"] = None
            listing_dict["source_code"] = None
            listing_dict["source_option_id"] = None

        # Populate category_name
        if listing.category_id and listing.category_id in categories_map:
            listing_dict["category_name"] = categories_map[listing.category_id]
        else:
            listing_dict["category_name"] = None

        # Populate platform_names
        if listing.platform_ids:
            platform_names = []
            for p_id in listing.platform_ids:
                found_platform = next((p for p in platforms if p["id"] == p_id), None)
                if found_platform:
                    platform_names.append(found_platform["name"])
            listing_dict["platform_names"] = platform_names
        else:
            listing_dict["platform_names"] = None

        # Convert datetime objects to ISO 8601 strings for JSON serialization
        for key, value in listing_dict.items():
            if isinstance(value, datetime):
                listing_dict[key] = value.isoformat()

        logger.debug(f"Final JSON for listing ID {listing.id}: {json.dumps(listing_dict)}")
        enriched_listings.append(listing_dict)

    await redis.set("listings", json.dumps(enriched_listings), ex=3600)
    logger.info(f"Cached {len(enriched_listings)} listings.")


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
    is_sold: Optional[bool] = Query(None),
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
    cache_key = f"listings:{search}:{active_only}:{sort_field}:{sort_order}:{currency}:{price_min}:{price_max}:{condition_id}:{condition}:{category_id}:{platform_id}:{source_id}:{source}:{is_sold}:{page}:{page_size}"

    # Try to fetch the specific paginated/filtered data from the cache first
    logger.info(f"Attempting to fetch specific query from cache with key: {cache_key}")
    cached_data = await redis.get(cache_key)
    if cached_data:
        logger.info("Serving specific query from cache")
        logger.debug(f"Cached data content: {cached_data[:500]}...")
        return json.loads(cached_data)

    logger.info("Specific query not in cache, loading all listings from main cache or DB.")

    # Load all enriched listings from the main cache
    all_listings_json = await redis.get("listings")
    if not all_listings_json:
        logger.info("Main 'listings' cache is empty, loading from database via load_listings_to_cache...")
        await load_listings_to_cache(db, redis)
        all_listings_json = await redis.get("listings") # Re-fetch after loading
        if not all_listings_json:
            raise HTTPException(status_code=500, detail="Failed to load listings into cache.")
        logger.info("Main 'listings' cache populated.")

    all_listings = json.loads(all_listings_json)
    logger.info(f"Loaded {len(all_listings)} listings from main cache.")

    # Load master data for lookups (these should also be cached by load_listings_to_cache)
    categories_data = await redis.get("categories")
    categories = json.loads(categories_data) if categories_data else []
    platforms_data = await redis.get("platforms")
    platforms = json.loads(platforms_data) if platforms_data else []
    conditions_data = await redis.get("conditions")
    conditions = json.loads(conditions_data) if conditions_data else []
    sources_data = await redis.get("sources")
    sources = json.loads(sources_data) if sources_data else []

    # Create maps for quick lookup
    categories_map = {c["id"]: c["name"] for c in categories}
    sources_map = {s["code"]: s for s in sources}
    conditions_map = {c["id"]: c for c in conditions} # For condition filtering by code/label

    # Apply filters in-memory
    filtered_listings = []
    for listing in all_listings:
        if active_only and not listing.get("is_active"):
            continue
        if search and search.lower() not in listing.get("title", "").lower():
            continue
        if currency and listing.get("currency") != currency:
            continue
        if price_min is not None and listing.get("price_cents", 0) < price_min:
            continue
        if price_max is not None and listing.get("price_cents", 0) > price_max:
            continue
        if condition_id is not None and listing.get("condition_option_id") != condition_id:
            continue
        if condition:
            # Normalize the query condition for comparison
            _, query_condition_code, query_condition_label = normalize_condition(condition)
            listing_condition_code = listing.get("condition_code")
            listing_condition_label = listing.get("condition_label")

            if not (listing_condition_code == query_condition_code or listing_condition_label == query_condition_label):
                continue
        if category_id is not None and listing.get("category_id") != category_id:
            continue
        if platform_id is not None and listing.get("platform_ids") and platform_id not in listing["platform_ids"]:
            continue
        if source_id is not None and listing.get("source_option_id") != source_id:
            continue
        if source:
            listing_source_code = listing.get("source_code")
            if not (listing_source_code and listing_source_code == source):
                continue
        if is_sold is not None and listing.get("is_sold") != is_sold:
            continue

        filtered_listings.append(listing)

    logger.info(f"After filtering, {len(filtered_listings)} listings remain.")

    # Apply sorting in-memory
    if sort_field in SORTABLE_FIELDS:
        if sort_field == "price_change":
            # Define a custom order for price_change
            # 'down' (price decreased) is generally more interesting for 'desc' sort
            # 'up' (price increased) is generally more interesting for 'asc' sort
            price_change_order = {"down": 1, "same": 2, "up": 3, None: 4}
            if sort_order == "asc":
                price_change_order = {"up": 1, "same": 2, "down": 3, None: 4}

            filtered_listings.sort(key=lambda item: price_change_order.get(item.get("price_change"), 4), reverse=False) # Reverse is handled by custom order
        else:
            # Determine the actual key to sort by in the dictionary
            actual_sort_key = SORTABLE_FIELDS[sort_field]

            # Handle potential missing keys or None values during sorting
            def get_sort_value(item):
                value = item.get(actual_sort_key)
                # Convert datetime strings back to datetime objects for proper sorting if needed
                if isinstance(value, str) and ('_at' in actual_sort_key or 'seen_at' in actual_sort_key):
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        pass # Fallback to string comparison if parsing fails
                return value

            filtered_listings.sort(key=get_sort_value, reverse=(sort_order == "desc"))
    else:
        logger.warning(f"Invalid sort_field: {sort_field}. Skipping sorting.")

    # Apply pagination in-memory
    total = len(filtered_listings)
    if limit:
        paginated_listings = filtered_listings[:limit]
        page = 1 # When limit is used, page and page_size are effectively overridden
        page_size = limit
    else:
        offset = (page - 1) * page_size
        paginated_listings = filtered_listings[offset : offset + page_size]

    total_pages = int(math.ceil(total / page_size)) if page_size > 0 else 1

    # Prepare the response
    # Extract unique values from all_listings for available filters
    unique_currencies = sorted(list(set(l["currency"] for l in all_listings if l["currency"])))
    unique_condition_ids = set(l["condition_option_id"] for l in all_listings if l.get("condition_option_id"))
    unique_category_ids = set(l["category_id"] for l in all_listings if l.get("category_id"))
    unique_platform_ids_flat = set()
    for l in all_listings:
        if l.get("platform_ids"):
            unique_platform_ids_flat.update(l["platform_ids"])
    unique_source_ids = set(l["source_option_id"] for l in all_listings if l.get("source_option_id"))

    filtered_available_conditions = [ConditionResponse(**c) for c in conditions if c["id"] in unique_condition_ids]
    filtered_available_categories = [CategoryResponse(**c) for c in categories if c["id"] in unique_category_ids]
    filtered_available_platforms = [PlatformResponse(**p) for p in platforms if p["id"] in unique_platform_ids_flat]
    filtered_available_sources = [SourceResponse(**s) for s in sources if s["id"] in unique_source_ids]

    response = ListingListResponse(
        items=paginated_listings,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=(page * page_size) < total,
        available_currencies=unique_currencies,
        available_conditions=filtered_available_conditions,
        available_categories=filtered_available_categories,
        available_platforms=filtered_available_platforms,
        available_sources=filtered_available_sources,
    )

    # Cache the response for this specific query
    await redis.set(cache_key, response.model_dump_json(), ex=3600)
    logger.info(f"Cached specific query result for key: {cache_key}")

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
