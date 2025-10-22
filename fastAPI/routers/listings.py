"""Listings endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ListingDetail,
    ListingListResponse,
    ListingResponse,
    PriceHistoryResponse,
)
from app.db.models import Listing, PriceHistory
from fastAPI.dependencies import get_db, require_api_key

router = APIRouter(
    prefix="/api",
    tags=["listings"],
    dependencies=[Depends(require_api_key)],
)

SORTABLE_FIELDS = {
    "last_seen_at": Listing.last_seen_at,
    "first_seen_at": Listing.first_seen_at,
    "price": Listing.price_cents,
    "title": Listing.title,
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
    db: AsyncSession = Depends(get_db),
) -> ListingListResponse:
    """Return listings with optional search and pagination."""
    offset = (page - 1) * page_size

    filters = []
    if active_only:
        filters.append(Listing.is_active.is_(True))
    if search:
        filters.append(Listing.title.ilike(f"%{search}%"))
    if currency:
        filters.append(Listing.currency == currency)

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

    currency_stmt = select(Listing.currency).distinct()
    if filters:
        currency_stmt = currency_stmt.where(*filters)
    currency_rows = await db.execute(currency_stmt.order_by(Listing.currency.asc()))
    available_currencies = sorted({row[0] for row in currency_rows if row[0]})

    enriched: list[ListingResponse] = []
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

    return ListingListResponse(
        items=enriched,
        total=int(total),
        page=page,
        page_size=page_size,
        has_next=has_next,
        available_currencies=available_currencies,
    )


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
