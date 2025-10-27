"""Stats endpoints."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, case, literal_column, or_, DATE
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ListingsByPeriod, ListingsByPeriodResponse, StatsResponse
from app.db.models import Listing, ScrapeConfig, PriceHistory, SourceOption
from fastAPI.dependencies import get_db, require_api_key

router = APIRouter(prefix="/api", tags=["stats"], dependencies=[Depends(require_api_key)])


@router.get("/stats", response_model=StatsResponse)
async def read_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    """Return aggregated dashboard statistics."""
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = today - timedelta(days=2)
        day_before_previous_seven_days_ago = today - timedelta(days=9) # 7 days before day_before_yesterday
        day_before_previous_thirty_days_ago = today - timedelta(days=60) # 30 days before day_before_yesterday
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

        total_scraped_previous_day = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) == yesterday)
            )
        ).scalar()

        total_scraped_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) == day_before_yesterday)
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

        total_scraped_previous_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) >= seven_days_ago - timedelta(days=7),
                        func.date(Listing.first_seen_at) < seven_days_ago,
                    )
                )
            )
        ).scalar()

        total_scraped_previous_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) >= thirty_days_ago - timedelta(days=30),
                        func.date(Listing.first_seen_at) < thirty_days_ago,
                    )
                )
            )
        ).scalar()

        # New metrics for day_before_previous
        total_scraped_last_7_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) >= day_before_previous_seven_days_ago)
            )
        ).scalar()

        total_scraped_last_30_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(func.date(Listing.first_seen_at) >= day_before_previous_thirty_days_ago)
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

        active_listings_last_7_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(True),
                        func.date(Listing.first_seen_at) >= day_before_previous_seven_days_ago,
                    )
                )
            )
        ).scalar()

        active_listings_last_30_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(True),
                        func.date(Listing.first_seen_at) >= day_before_previous_thirty_days_ago,
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

        inactive_listings_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) == day_before_yesterday,
                    )
                )
            )
        ).scalar()

        inactive_listings_last_7_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) >= day_before_previous_seven_days_ago,
                    )
                )
            )
        ).scalar()

        inactive_listings_last_30_days_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(False),
                        func.date(Listing.first_seen_at) >= day_before_previous_thirty_days_ago,
                    )
                )
            )
        ).scalar()

        active_listings_day_before_previous = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        Listing.is_active.is_(True),
                        func.date(Listing.first_seen_at) == day_before_yesterday,
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

        total_scraped_previous_7_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) >= seven_days_ago - timedelta(days=7),
                        func.date(Listing.first_seen_at) < seven_days_ago,
                    )
                )
            )
        ).scalar()

        total_scraped_previous_30_days = (
            await db.execute(
                select(func.count())
                .select_from(Listing)
                .where(
                    and_(
                        func.date(Listing.first_seen_at) >= thirty_days_ago - timedelta(days=30),
                        func.date(Listing.first_seen_at) < thirty_days_ago,
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
        total_scraped_previous_day=total_scraped_previous_day or 0,
        total_scraped_day_before_previous=total_scraped_day_before_previous or 0,
        total_scraped_last_7_days=total_scraped_last_7_days or 0,
        total_scraped_last_30_days=total_scraped_last_30_days or 0,
        active_listings_last_7_days=active_listings_last_7_days or 0,
        active_listings_last_30_days=active_listings_last_30_days or 0,
        inactive_listings_today=inactive_listings_today or 0,
        inactive_listings_last_7_days=inactive_listings_last_7_days or 0,
        inactive_listings_last_30_days=inactive_listings_last_30_days or 0,
        active_listings_day_before_previous=active_listings_day_before_previous or 0,
        total_scraped_last_7_days_day_before_previous=total_scraped_last_7_days_day_before_previous or 0,
        total_scraped_last_30_days_day_before_previous=total_scraped_last_30_days_day_before_previous or 0,
        active_listings_last_7_days_day_before_previous=active_listings_last_7_days_day_before_previous or 0,
        active_listings_last_30_days_day_before_previous=active_listings_last_30_days_day_before_previous or 0,
        inactive_listings_day_before_previous=inactive_listings_day_before_previous or 0,
        inactive_listings_last_7_days_day_before_previous=inactive_listings_last_7_days_day_before_previous or 0,
        inactive_listings_last_30_days_day_before_previous=inactive_listings_last_30_days_day_before_previous or 0,
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
        total_scraped_previous_7_days=total_scraped_previous_7_days or 0,
        total_scraped_previous_30_days=total_scraped_previous_30_days or 0,
        source_stats=source_stats_dict,
    )


@router.get("/stats/listings_by_period", response_model=ListingsByPeriodResponse)
async def read_listings_by_period(
    period: str, db: AsyncSession = Depends(get_db)
) -> ListingsByPeriodResponse:
    """Return the number of new and total listings by period (daily, weekly, monthly)."""
    try:
        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid period. Must be 'daily', 'weekly', or 'monthly'.")

        today = datetime.utcnow().date()
        
        # Define time frame and period iteration logic
        if period == "daily":
            time_frame_days = 30
            period_delta = timedelta(days=1)
            date_format_str = "%Y-%m-%d"
            get_period_key = lambda d: d.strftime(date_format_str)
            get_period_start_date = lambda d: d
            get_period_end_date = lambda d: d
        elif period == "weekly":
            time_frame_days = 12 * 7 # 12 weeks
            period_delta = timedelta(weeks=1)
            date_format_str = "%Y-%m-%d" # For week start date key
            get_period_key = lambda d: (d - timedelta(days=d.weekday())).strftime(date_format_str)
            get_period_start_date = lambda d: d - timedelta(days=d.weekday())
            get_period_end_date = lambda d: d - timedelta(days=d.weekday()) + timedelta(days=6)
        else: # monthly
            time_frame_days = 12 * 30 # 12 months approx
            period_delta = timedelta(days=30) # For iteration, roughly a month
            date_format_str = "%Y-%m"
            get_period_key = lambda d: d.strftime(date_format_str)
            get_period_start_date = lambda d: d.replace(day=1)
            get_period_end_date = lambda d: (d.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1) # Last day of month

        overall_start_date = today - timedelta(days=time_frame_days)

        # Fetch all listings with their first_seen_at and is_active status
        # We only need listings that were "seen" within our overall timeframe
        all_listings_query = select(
            Listing.first_seen_at,
            Listing.last_seen_at,
            Listing.is_active
        ).where(
            Listing.first_seen_at >= overall_start_date
        )
        all_listings = (await db.execute(all_listings_query)).all()

        # Prepare data structures for results
        new_listings_counts: dict[str, int] = {}
        
        # Initialize all periods with zero counts
        current_period_iter = get_period_start_date(overall_start_date)
        while current_period_iter <= today:
            key = get_period_key(current_period_iter)
            new_listings_counts[key] = 0
            
            if period == "daily":
                current_period_iter += timedelta(days=1)
            elif period == "weekly":
                current_period_iter += timedelta(weeks=1)
            else: # monthly
                current_period_iter = (current_period_iter.replace(day=1) + timedelta(days=32)).replace(day=1)

        # Populate new_listings_counts
        for listing in all_listings:
            if listing.first_seen_at:
                period_key = get_period_key(listing.first_seen_at.date())
                if period_key in new_listings_counts:
                    new_listings_counts[period_key] += 1

        # Calculate cumulative_total_listings (all listings ever seen up to that period)
        response_items: list[ListingsByPeriod] = []
        sorted_period_keys = sorted(new_listings_counts.keys())

        for period_key in sorted_period_keys:
            period_end_date_for_cumulative: datetime.date
            if period == "daily":
                period_end_date_for_cumulative = datetime.strptime(period_key, date_format_str).date()
            elif period == "weekly":
                period_end_date_for_cumulative = datetime.strptime(period_key, date_format_str).date() + timedelta(days=6)
            else: # monthly
                temp_date = datetime.strptime(period_key, date_format_str).date()
                period_end_date_for_cumulative = (temp_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Count ALL listings whose first_seen_at is <= period_end_date_for_cumulative
            cumulative_total_query = select(func.count()).select_from(Listing).where(
                Listing.first_seen_at.cast(DATE) <= period_end_date_for_cumulative
            )
            cumulative_total_count = (await db.execute(cumulative_total_query)).scalar() or 0

            response_items.append(
                ListingsByPeriod(
                    period=period_key,
                    new_listings=new_listings_counts.get(period_key, 0),
                    total_listings=cumulative_total_count
                )
            )

        return ListingsByPeriodResponse(items=response_items)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error in read_listings_by_period: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
