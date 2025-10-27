"""Stats endpoints."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import StatsResponse
from app.db.models import Listing, ScrapeConfig, PriceHistory, SourceOption
from fastAPI.dependencies import get_db, require_api_key

router = APIRouter(prefix="/api", tags=["stats"], dependencies=[Depends(require_api_key)])


@router.get("/stats", response_model=StatsResponse)
async def read_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    """Return aggregated dashboard statistics."""
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)

        total_listings = (
            await db.execute(select(func.count()).select_from(Listing))
        ).scalar()

        active_listings = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(Listing.is_active.is_(True))
            )
        ).scalar()

        total_scraped_today = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) == today)
            )
        ).scalar()

        active_configs = (
            await db.execute(
                select(func.count())
                .select_from(ScrapeConfig)
                .where(ScrapeConfig.is_active.is_(True))
            )
        ).scalar()

        avg_price_cents = (
            await db.execute(
                select(func.avg(Listing.price_cents)).where(
                    and_(Listing.is_active.is_(True), Listing.price_cents.isnot(None))
                )
            )
        ).scalar()

        min_price_cents = (
            await db.execute(
                select(func.min(Listing.price_cents)).where(
                    and_(Listing.is_active.is_(True), Listing.price_cents.isnot(None))
                )
            )
        ).scalar()

        max_price_cents = (
            await db.execute(
                select(func.max(Listing.price_cents)).where(
                    and_(Listing.is_active.is_(True), Listing.price_cents.isnot(None))
                )
            )
        ).scalar()

        total_scraped_last_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) >= seven_days_ago)
            )
        ).scalar()

        total_scraped_last_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) >= thirty_days_ago)
            )
        ).scalar()

        active_listings_last_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(True),
                        func.date(Listing.first_seen_at) >= seven_days_ago,
                    )
                )
            )
        ).scalar()

        active_listings_last_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(True),
                        func.date(Listing.first_seen_at) >= thirty_days_ago,
                    )
                )
            )
        ).scalar()

        inactive_listings_today = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) == today,
                    )
                )
            )
        ).scalar()

        inactive_listings_last_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) >= seven_days_ago,
                    )
                )
            )
        ).scalar()

        inactive_listings_last_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) >= thirty_days_ago,
                    )
                )
            )
        ).scalar()

        # Price change calculations using PriceHistory
        # Subquery to get ranked prices for each listing
        ranked_prices_subquery = (
            select(
                PriceHistory.listing_id,
                PriceHistory.price_cents,
                func.row_number()
                .over(
                    partition_by=PriceHistory.listing_id,
                    order_by=PriceHistory.observed_at.desc(),
                )
                .label("rn"),
            )
            .filter(PriceHistory.price_cents.isnot(None))
            .subquery("ranked_prices")
        )

        # Subquery to get current and previous prices for each listing
        current_and_previous_prices_subquery = (
            select(
                ranked_prices_subquery.c.listing_id,
                func.max(case((ranked_prices_subquery.c.rn == 1, ranked_prices_subquery.c.price_cents), else_=None)).label("current_price"),
                func.max(case((ranked_prices_subquery.c.rn == 2, ranked_prices_subquery.c.price_cents), else_=None)).label("previous_price"),
            )
            .group_by(ranked_prices_subquery.c.listing_id)
            .having(func.count(ranked_prices_subquery.c.price_cents) > 1) # Only consider listings with at least two price entries
            .subquery("current_and_previous_prices")
        )

        price_increase_count = (
            await db.execute(
                select(func.count())
                .select_from(current_and_previous_prices_subquery)
                .where(
                    current_and_previous_prices_subquery.c.current_price > current_and_previous_prices_subquery.c.previous_price
                )
            )
        ).scalar()

        price_decrease_count = (
            await db.execute(
                select(func.count())
                .select_from(current_and_previous_prices_subquery)
                .where(
                    current_and_previous_prices_subquery.c.current_price < current_and_previous_prices_subquery.c.previous_price
                )
            )
        ).scalar()

        price_unchanged_count = (
            await db.execute(
                select(func.count())
                .select_from(current_and_previous_prices_subquery)
                .where(
                    current_and_previous_prices_subquery.c.current_price == current_and_previous_prices_subquery.c.previous_price
                )
            )
        ).scalar()

        total_listings_previous_day = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) == yesterday)
            )
        ).scalar()

        total_listings_previous_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) < seven_days_ago,
                        func.date(Listing.first_seen_at) >= seven_days_ago - timedelta(days=7),
                    )
                )
            )
        ).scalar()

        total_listings_previous_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) < thirty_days_ago,
                        func.date(Listing.first_seen_at) >= thirty_days_ago - timedelta(days=30),
                    )
                )
            )
        ).scalar()

        source_stats_query = await db.execute(
            select(
                SourceOption.label,
                func.count().label("total_items"),
                func.count().filter(Listing.is_active.is_(True)).label("active_items"),
                func.count().filter(Listing.is_active.is_(False)).label("inactive_items"),
            )
            .join(SourceOption, Listing.source_option_id == SourceOption.id)
            .group_by(SourceOption.label)
        )
        source_stats_results = source_stats_query.all()

        source_stats_dict = {
            row.label: {
                "total_items": row.total_items,
                "active_items": row.active_items,
                "inactive_items": row.inactive_items,
            }
            for row in source_stats_results
            if row.label is not None
        }
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StatsResponse(
        total_listings=total_listings or 0,
        active_listings=active_listings or 0,
        total_scraped_today=total_scraped_today or 0,
        total_scraped_last_7_days=total_scraped_last_7_days or 0,
        total_scraped_last_30_days=total_scraped_last_30_days or 0,
        active_listings_last_7_days=active_listings_last_7_days or 0,
        active_listings_last_30_days=active_listings_last_30_days or 0,
        inactive_listings_today=inactive_listings_today or 0,
        inactive_listings_last_7_days=inactive_listings_last_7_days or 0,
        inactive_listings_last_30_days=inactive_listings_last_30_days or 0,
        active_configs=active_configs or 0,
        avg_price_cents=float(avg_price_cents) if avg_price_cents else None,
        min_price_cents=min_price_cents or None,
        max_price_cents=max_price_cents or None,
        price_increase_count=price_increase_count or 0,
        price_decrease_count=price_decrease_count or 0,
        price_unchanged_count=price_unchanged_count or 0,
        total_listings_previous_day=total_listings_previous_day or 0,
        total_listings_previous_7_days=total_listings_previous_7_days or 0,
        total_listings_previous_30_days=total_listings_previous_30_days or 0,
        source_stats=source_stats_dict,
    )
