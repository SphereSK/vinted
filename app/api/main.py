"""FastAPI application for Vinted scraper management."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Listing, PriceHistory, ScrapeConfig
from app.db.session import Session, init_db
from app.api.schemas import (
    ListingResponse,
    ListingDetail,
    ListingListResponse,
    PriceHistoryResponse,
    ScrapeConfigCreate,
    ScrapeConfigUpdate,
    ScrapeConfigResponse,
    CategoryResponse,
    StatsResponse,
)
from app.utils.categories import list_common_categories, list_video_game_platforms
from app.ingest import scrape_and_store
from app.utils.url import build_catalog_url
from app.scheduler import sync_crontab, list_scheduled_jobs

app = FastAPI(
    title="Vinted Scraper API",
    description="API for managing Vinted product scraping and price tracking",
    version="1.0.0",
)

# Get frontend path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db():
    """Dependency for database session."""
    await init_db()
    async with Session() as session:
        yield session


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


# ==================== Listings Endpoints ====================

SORTABLE_LISTING_FIELDS = {
    "last_seen_at": Listing.last_seen_at,
    "first_seen_at": Listing.first_seen_at,
    "price": Listing.price_cents,
    "title": Listing.title,
}


@app.get("/api/listings", response_model=ListingListResponse)
async def get_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    active_only: bool = True,
    sort_field: str = Query("last_seen_at"),
    sort_order: str = Query("desc"),
    currency: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get list of listings with pagination, search, sorting, and currency filters."""
    offset = (page - 1) * page_size

    filters = []
    if active_only:
        filters.append(Listing.is_active.is_(True))
    if search:
        filters.append(Listing.title.ilike(f"%{search}%"))
    if currency:
        filters.append(Listing.currency == currency)

    sort_key = sort_field.lower()
    if sort_key not in SORTABLE_LISTING_FIELDS:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    sort_direction = sort_order.lower()
    if sort_direction not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    order_column = SORTABLE_LISTING_FIELDS[sort_key]
    if sort_direction == "desc":
        order_clause = order_column.desc().nullslast()
    else:
        order_clause = order_column.asc().nullsfirst()

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

    enriched = []
    for listing in listings:
        price_result = await db.execute(
            select(PriceHistory.price_cents)
            .where(PriceHistory.listing_id == listing.id)
            .order_by(PriceHistory.observed_at.desc())
            .limit(2)
        )
        prices = price_result.scalars().all()

        listing_dict = listing.__dict__.copy()
        listing_dict['previous_price_cents'] = None
        listing_dict['price_change'] = None

        if len(prices) >= 2:
            current = prices[0]
            previous = prices[1]
            listing_dict['previous_price_cents'] = previous

            if current is not None and previous is not None:
                if current > previous:
                    listing_dict['price_change'] = 'up'
                elif current < previous:
                    listing_dict['price_change'] = 'down'
                else:
                    listing_dict['price_change'] = 'same'

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


@app.get("/api/listings/{listing_id}", response_model=ListingDetail)
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed listing with price history."""
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Get price history
    price_result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.observed_at.desc())
    )
    prices = price_result.scalars().all()

    return ListingDetail(
        **listing.__dict__,
        price_history=[
            PriceHistoryResponse.model_validate(p) for p in prices
        ]
    )


# ==================== Scrape Config Endpoints ====================

@app.get("/api/configs", response_model=list[ScrapeConfigResponse])
async def get_configs(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get all scrape configurations."""
    query = select(ScrapeConfig)
    if active_only:
        query = query.where(ScrapeConfig.is_active == True)

    query = query.order_by(ScrapeConfig.created_at.desc())
    result = await db.execute(query)
    configs = result.scalars().all()
    return configs


@app.post("/api/configs", response_model=ScrapeConfigResponse)
async def create_config(
    config: ScrapeConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new scrape configuration."""
    db_config = ScrapeConfig(**config.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    # Sync crontab if schedule is set
    if db_config.cron_schedule:
        try:
            await sync_crontab()
        except Exception as e:
            print(f"Warning: Failed to sync crontab: {e}")

    return db_config


@app.get("/api/configs/{config_id}", response_model=ScrapeConfigResponse)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config


@app.put("/api/configs/{config_id}", response_model=ScrapeConfigResponse)
async def update_config(
    config_id: int,
    config_update: ScrapeConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Update fields
    for key, value in config_update.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


@app.delete("/api/configs/{config_id}")
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Delete scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    await db.delete(config)
    await db.commit()

    # Sync crontab
    try:
        await sync_crontab()
    except Exception as e:
        print(f"Warning: Failed to sync crontab: {e}")

    return {"message": "Configuration deleted"}


@app.post("/api/configs/{config_id}/run")
async def run_config(config_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger immediate scrape for a configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Build URL
    start_url = build_catalog_url(
        base_url="https://www.vinted.sk/catalog",
        search_text=config.search_text,
        category=config.categories,
        platform_id=config.platform_ids,
    )

    # Update status
    config.last_run_status = "running"
    config.last_run_at = datetime.utcnow()
    await db.commit()

    # Run scraper in background
    try:
        # Note: In production, use Celery or similar for background tasks
        asyncio.create_task(
            run_scraper_task(config_id, start_url, config)
        )
        return {"message": "Scrape started", "config_id": config_id}
    except Exception as e:
        config.last_run_status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


async def run_scraper_task(config_id: int, start_url: str, config: ScrapeConfig):
    """Background task to run scraper."""
    async with Session() as db:
        try:
            # Get initial count
            result = await db.execute(select(func.count()).select_from(Listing))
            count_before = result.scalar()

            # Run scraper
            await scrape_and_store(
                start_url=start_url,
                max_pages=config.max_pages,
                per_page=config.per_page,
                delay=config.delay,
                fetch_details=config.fetch_details,
                use_proxy=False,
            )

            # Get final count
            result = await db.execute(select(func.count()).select_from(Listing))
            count_after = result.scalar()

            # Update config
            result = await db.execute(
                select(ScrapeConfig).where(ScrapeConfig.id == config_id)
            )
            config = result.scalar_one()
            config.last_run_status = "success"
            config.last_run_items = count_after - count_before
            await db.commit()

        except Exception as e:
            result = await db.execute(
                select(ScrapeConfig).where(ScrapeConfig.id == config_id)
            )
            config = result.scalar_one()
            config.last_run_status = "failed"
            await db.commit()
            print(f"Scraper task failed: {e}")


# ==================== Categories Endpoints ====================

@app.get("/api/categories", response_model=list[CategoryResponse])
async def get_categories():
    """Get available Vinted categories."""
    categories = list_common_categories()
    return [
        CategoryResponse(id=cat_id, name=name)
        for cat_id, name in categories.items()
    ]


@app.get("/api/platforms", response_model=list[CategoryResponse])
async def get_platforms():
    """Get available video game platforms."""
    platforms = list_video_game_platforms()
    return [
        CategoryResponse(id=plat_id, name=name)
        for plat_id, name in platforms.items()
    ]


# ==================== Stats Endpoints ====================

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    # Total listings
    result = await db.execute(select(func.count()).select_from(Listing))
    total_listings = result.scalar()

    # Active listings
    result = await db.execute(
        select(func.count()).select_from(Listing).where(Listing.is_active == True)
    )
    active_listings = result.scalar()

    # Today's scrapes
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count())
        .select_from(Listing)
        .where(func.date(Listing.first_seen_at) == today)
    )
    total_scraped_today = result.scalar()

    # Active configs
    result = await db.execute(
        select(func.count())
        .select_from(ScrapeConfig)
        .where(ScrapeConfig.is_active == True)
    )
    active_configs = result.scalar()

    # Average price
    result = await db.execute(
        select(func.avg(Listing.price_cents))
        .where(and_(Listing.is_active == True, Listing.price_cents.isnot(None)))
    )
    avg_price_cents = result.scalar()

    return StatsResponse(
        total_listings=total_listings,
        active_listings=active_listings,
        total_scraped_today=total_scraped_today,
        active_configs=active_configs,
        avg_price_cents=float(avg_price_cents) if avg_price_cents else None,
    )


@app.get("/api/cron/jobs")
async def get_cron_jobs():
    """Get all scheduled cron jobs."""
    try:
        jobs = await list_scheduled_jobs()
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cron/sync")
async def sync_cron():
    """Manually sync configurations to crontab."""
    try:
        await sync_crontab()
        return {"message": "Crontab synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Serve frontend."""
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
