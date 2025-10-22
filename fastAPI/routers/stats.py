"""Stats endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import StatsResponse
from app.db.models import Listing, ScrapeConfig
from fastAPI.dependencies import get_db, require_api_key

router = APIRouter(prefix="/api", tags=["stats"], dependencies=[Depends(require_api_key)])


@router.get("/stats", response_model=StatsResponse)
async def read_stats(db: AsyncSession = Depends(get_db)) -> StatsResponse:
    """Return aggregated dashboard statistics."""
    try:
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

        today = datetime.utcnow().date()
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
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StatsResponse(
        total_listings=total_listings or 0,
        active_listings=active_listings or 0,
        total_scraped_today=total_scraped_today or 0,
        active_configs=active_configs or 0,
        avg_price_cents=float(avg_price_cents) if avg_price_cents else None,
    )
