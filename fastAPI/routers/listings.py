"""Listings endpoints."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

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
    "last_seen_at": Listing.last_seen_at,
    "first_seen_at": Listing.first_seen_at,
    "price": Listing.price_cents,
    "title": Listing.title,
    "condition": Listing.condition_option_id,
    "category_id": Listing.category_id,
    "source": Listing.source_option_id,
    "platform_ids": Listing.platform_ids,
}


@router.get("/listings", response_model=ListingListResponse)
async def list_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
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
    db: AsyncSession = Depends(get_db),
) -> ListingListResponse:
    """Return listings with optional search and pagination."""
    redis = get_redis()
    cache_key = f"listings:{page}:{page_size}:{search}:{active_only}:{sort_field}:{sort_order}:{currency}:{price_min}:{price_max}:{condition_id}:{condition}:{category_id}:{platform_id}:{source_id}:{source}"

    if redis:
        cached_data = await redis.get(cache_key)
        if cached_data:
            logger.info("Serving from cache")
            return ListingListResponse.parse_raw(cached_data)

    logger.info("Serving from database")
    offset = (page - 1) * page_size

    if (
        price_min is not None
        and price_max is not None
        and price_min > price_max
    ):
        raise HTTPException(status_code=400, detail="price_min cannot exceed price_max")

    filters = []
    if active_only:
        filters.append(Listing.is_active.is_(True))
    if search:
        filters.append(Listing.title.ilike(f"%{search}%"))
    if currency:
        filters.append(Listing.currency == currency)
    if price_min is not None:
        filters.append(Listing.price_cents.isnot(None))
        filters.append(Listing.price_cents >= price_min)
    if price_max is not None:
        filters.append(Listing.price_cents.isnot(None))
        filters.append(Listing.price_cents <= price_max)
    if condition_id is not None:
        filters.append(Listing.condition_option_id == condition_id)
    elif condition:
        norm_id, norm_code, norm_label = normalize_condition(condition)
        variants = {
            condition.strip().lower(),
            (norm_code or "").replace("_", " ").replace("-", " ") if norm_code else "",
            (norm_label or "").strip().lower() if norm_label else "",
        }
        variants = {value for value in variants if value}
        if variants:
            filters.append(func.lower(Listing.condition).in_(variants))
    if category_id is not None:
        filters.append(Listing.category_id == category_id)
    if platform_id is not None:
        if Listing.__table__.columns.platform_ids.type.__class__.__module__.startswith(
            "sqlalchemy.dialects.postgresql"
        ):
            filters.append(
                Listing.platform_ids.cast(postgresql.JSONB).contains([platform_id])
            )
        else:
            filters.append(Listing.platform_ids.contains([platform_id]))
    if source_id is not None:
        filters.append(Listing.source_option_id == source_id)
    elif source:
        normalized_source = source.strip().lower()
        if normalized_source:
            filters.append(func.lower(Listing.source) == normalized_source)

    sort_field_key = sort_field.lower()
    if sort_field_key not in SORTABLE_FIELDS:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    sort_order_normalized = sort_order.lower()
    if sort_order_normalized not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    sort_column = SORTABLE_FIELDS[sort_field_key]
    if sort_order_normalized == "desc":
        order_clause = sort_column.desc().nullslast()
    else:
        order_clause = sort_column.asc().nullsfirst()

    base_query = select(Listing)
    if filters:
        base_query = base_query.where(*filters)

    query = base_query.order_by(order_clause).offset(offset).limit(page_size)
    result = await db.execute(query)
    listings = result.scalars().all()

    count_stmt = select(func.count()).select_from(Listing)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Load master data lookups
    category_records = (
        await db.execute(select(CategoryOption.id, CategoryOption.name))
    ).all()
    category_lookup = {row[0]: row[1] for row in category_records}

    platform_records = (
        await db.execute(select(PlatformOption.id, PlatformOption.name))
    ).all()
    platform_lookup = {row[0]: row[1] for row in platform_records}

    condition_records = (
        await db.execute(
            select(ConditionOption.id, ConditionOption.code, ConditionOption.label)
        )
    ).all()
    condition_lookup = {
        row[0]: {"code": row[1], "label": row[2]}
        for row in condition_records
    }
    condition_code_lookup = {row[1]: row[0] for row in condition_records}
    condition_label_lookup = {row[2].lower(): row[0] for row in condition_records}

    source_records = (
        await db.execute(
            select(SourceOption.id, SourceOption.code, SourceOption.label)
        )
    ).all()
    source_lookup = {
        row[0]: {"code": row[1], "label": row[2]}
        for row in source_records
    }
    source_code_lookup = {row[1]: row[0] for row in source_records}
    source_label_lookup = {row[2].lower(): row[0] for row in source_records}

    currency_stmt = select(Listing.currency).distinct()
    if filters:
        currency_stmt = currency_stmt.where(*filters)
    currency_rows = await db.execute(currency_stmt.order_by(Listing.currency.asc()))
    available_currencies = sorted({row[0] for row in currency_rows if row[0]})

    available_conditions = [
        ConditionResponse(id=row[0], code=row[1], label=row[2])
        for row in condition_records
    ]
    available_category_ids = sorted(category_lookup.keys())
    available_platform_ids = sorted(platform_lookup.keys())
    available_sources = [
        SourceResponse(id=row[0], code=row[1], label=row[2])
        for row in source_records
    ]

    enriched: list[ListingResponse] = []
    active_condition_ids: set[int] = set()
    active_source_ids: set[int] = set()
    for listing in listings:
        price_result = await db.execute(
            select(PriceHistory.price_cents)
            .where(PriceHistory.listing_id == listing.id)
            .order_by(PriceHistory.observed_at.desc())
            .limit(2)
        )
        prices = price_result.scalars().all()

        listing_dict = dict(listing.__dict__)
        listing_dict.pop("_sa_instance_state", None)
        listing_dict["previous_price_cents"] = None
        listing_dict["price_change"] = None
        listing_dict["category_name"] = category_lookup.get(listing.category_id)

        platform_names: list[str] = []
        platform_ids_value = listing.platform_ids if isinstance(listing.platform_ids, list) else []
        for platform in platform_ids_value:
            if isinstance(platform, int):
                name = platform_lookup.get(platform)
                if name:
                    platform_names.append(name)
        listing_dict["platform_names"] = platform_names or None

        condition_option_id = listing.condition_option_id
        condition_code = None
        condition_label = None
        if condition_option_id and condition_option_id in condition_lookup:
            entry = condition_lookup[condition_option_id]
            condition_code = entry["code"]
            condition_label = entry["label"]
            active_condition_ids.add(condition_option_id)
        else:
            norm_id, norm_code, norm_label = normalize_condition(listing.condition)
            if norm_id and norm_id in condition_lookup:
                entry = condition_lookup[norm_id]
                condition_option_id = norm_id
                condition_code = entry["code"]
                condition_label = entry["label"]
                active_condition_ids.add(condition_option_id)
            else:
                condition_code = norm_code
                condition_label = norm_label

        listing_dict["condition_option_id"] = condition_option_id
        listing_dict["condition_code"] = condition_code
        listing_dict["condition_label"] = condition_label

        source_option_id = listing.source_option_id
        source_code = None
        source_label = None
        if source_option_id and source_option_id in source_lookup:
            entry = source_lookup[source_option_id]
            source_code = entry["code"]
            source_label = entry["label"]
            active_source_ids.add(source_option_id)
        else:
            raw_source = (listing.source or "").strip().lower()
            resolved_id = source_code_lookup.get(raw_source) or source_label_lookup.get(raw_source)
            if resolved_id and resolved_id in source_lookup:
                entry = source_lookup[resolved_id]
                source_option_id = resolved_id
                source_code = entry["code"]
                source_label = entry["label"]
                active_source_ids.add(source_option_id)
            else:
                source_code = raw_source or "unknown"
                source_label = listing.source or "Unknown"

        listing_dict["source_option_id"] = source_option_id
        listing_dict["source"] = source_code
        listing_dict["source_label"] = source_label

        if len(prices) >= 2:
            current, previous = prices[0], prices[1]
            listing_dict["previous_price_cents"] = previous

            if current is not None and previous is not None:
                if current > previous:
                    listing_dict["price_change"] = "up"
                elif current < previous:
                    listing_dict["price_change"] = "down"
                else:
                    listing_dict["price_change"] = "same"

        enriched.append(ListingResponse(**listing_dict))

    has_next = offset + len(enriched) < total

    response = ListingListResponse(
        items=enriched,
        total=int(total),
        page=page,
        page_size=page_size,
        has_next=has_next,
        available_currencies=available_currencies,
        available_conditions=[
            ConditionResponse(id=row[0], code=row[1], label=row[2])
            for row in condition_records
            if not active_condition_ids or row[0] in active_condition_ids
        ],
        available_category_ids=available_category_ids,
        available_platform_ids=available_platform_ids,
        available_sources=[
            SourceResponse(id=row[0], code=row[1], label=row[2])
            for row in source_records
            if not active_source_ids or row[0] in active_source_ids
        ],
    )

    if redis:
        await redis.set(cache_key, response.json(), ex=3600)  # Cache for 1 hour

    return response


@router.post("/listings/cache/clear")
async def clear_listings_cache():
    """Clear the Redis cache for listings."""
    redis = get_redis()
    if redis:
        count = 0
        async for key in redis.scan_iter("listings:*"):
            await redis.delete(key)
            count += 1
        logger.info(f"Cleared {count} listing cache keys.")
        return {"message": f"Cleared {count} listing cache keys."}
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
