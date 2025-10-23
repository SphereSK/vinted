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
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Listing,
    PriceHistory,
    ScrapeConfig,
    CategoryOption,
    PlatformOption,
    ConditionOption,
    SourceOption,
)
from app.utils.conditions import normalize_condition
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
    "condition": Listing.condition_option_id,
    "category_id": Listing.category_id,
    "source": Listing.source_option_id,
    "platform_ids": Listing.platform_ids,
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
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    condition_id: Optional[int] = Query(None, ge=1),
    condition: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None, ge=1),
    platform_id: Optional[int] = Query(None, ge=1),
    source_id: Optional[int] = Query(None, ge=1),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get list of listings with pagination, search, sorting, and currency filters."""
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
            filters.append(Listing.platform_ids.cast(postgresql.JSONB).contains([platform_id]))
        else:
            filters.append(Listing.platform_ids.contains([platform_id]))
    if source_id is not None:
        filters.append(Listing.source_option_id == source_id)
    elif source:
        normalized_source = source.strip().lower()
        if normalized_source:
            filters.append(func.lower(Listing.source) == normalized_source)

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

    available_category_ids = sorted(category_lookup.keys())
    available_platform_ids = sorted(platform_lookup.keys())

    enriched = []
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

        listing_dict = listing.__dict__.copy()
        listing_dict['previous_price_cents'] = None
        listing_dict['price_change'] = None
        listing_dict['category_name'] = category_lookup.get(listing.category_id)

        platform_names: list[str] = []
        platform_ids_value = listing.platform_ids if isinstance(listing.platform_ids, list) else []
        for platform in platform_ids_value:
            if isinstance(platform, int):
                name = platform_lookup.get(platform)
                if name:
                    platform_names.append(name)
        listing_dict['platform_names'] = platform_names or None

        condition_option_id = listing.condition_option_id
        condition_code = None
        condition_label = None
        if condition_option_id and condition_option_id in condition_lookup:
            entry = condition_lookup[condition_option_id]
            condition_code = entry['code']
            condition_label = entry['label']
            active_condition_ids.add(condition_option_id)
        else:
            norm_id, norm_code, norm_label = normalize_condition(listing.condition)
            resolved_id = (
                norm_id
                or condition_code_lookup.get((norm_code or '').lower())
                or condition_label_lookup.get((norm_label or '').strip().lower())
            )
            if resolved_id and resolved_id in condition_lookup:
                entry = condition_lookup[resolved_id]
                condition_option_id = resolved_id
                condition_code = entry['code']
                condition_label = entry['label']
                active_condition_ids.add(condition_option_id)
            else:
                condition_code = norm_code
                condition_label = norm_label

        source_option_id = listing.source_option_id
        source_code = None
        source_label = None
        if source_option_id and source_option_id in source_lookup:
            entry = source_lookup[source_option_id]
            source_code = entry['code']
            source_label = entry['label']
            active_source_ids.add(source_option_id)
        else:
            raw_source = (listing.source or '').strip().lower()
            resolved_id = source_code_lookup.get(raw_source) or source_label_lookup.get(raw_source)
            if resolved_id and resolved_id in source_lookup:
                entry = source_lookup[resolved_id]
                source_option_id = resolved_id
                source_code = entry['code']
                source_label = entry['label']
                active_source_ids.add(source_option_id)
            else:
                source_code = raw_source or 'unknown'
                source_label = listing.source or 'Unknown'

        listing_dict['condition_option_id'] = condition_option_id
        listing_dict['condition_code'] = condition_code
        listing_dict['condition_label'] = condition_label
        listing_dict['source_option_id'] = source_option_id
        listing_dict['source'] = source_code
        listing_dict['source_label'] = source_label

        if len(prices) >= 2:
            current, previous = prices[0], prices[1]
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
        available_conditions=[
            ConditionResponse(id=row[0], code=row[1], label=row[2])
            for row in condition_records
            if not active_condition_ids or row[0] in active_condition_ids
        ],
        available_category_ids=available_category_ids,
        available_platform_ids=sorted(available_platform_ids),
        available_sources=[
            SourceResponse(id=row[0], code=row[1], label=row[2])
            for row in source_records
            if not active_source_ids or row[0] in active_source_ids
        ],
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
