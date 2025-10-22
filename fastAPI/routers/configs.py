"""Scrape configuration endpoints."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ScrapeConfigCreate,
    ScrapeConfigResponse,
    ScrapeConfigUpdate,
)
from app.db.models import ScrapeConfig
from app.scheduler import sync_crontab
from fastAPI.dependencies import get_db, require_api_key
from fastAPI.redis import get_config_status, set_config_status
from fastAPI.services.scraper import RunInProgressError, schedule_manual_run
from fastAPI.schemas import RuntimeStatusResponse

router = APIRouter(
    prefix="/api/configs",
    tags=["configs"],
    dependencies=[Depends(require_api_key)],
)

SYNC_CRON_FIELDS = {
    "cron_schedule",
    "search_text",
    "categories",
    "platform_ids",
    "max_pages",
    "per_page",
    "delay",
    "fetch_details",
    "details_for_new_only",
    "use_proxy",
    "order",
    "locales",
    "extra_filters",
    "error_wait_minutes",
    "max_retries",
    "base_url",
    "details_strategy",
    "details_concurrency",
    "is_active",
    "extra_args",
    "healthcheck_ping_url",
}


@router.get("", response_model=list[ScrapeConfigResponse])
async def list_configs(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list[ScrapeConfigResponse]:
    """Return scrape configurations."""
    query = select(ScrapeConfig)
    if active_only:
        query = query.where(ScrapeConfig.is_active.is_(True))

    query = query.order_by(ScrapeConfig.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ScrapeConfigResponse, status_code=201)
async def create_config(
    payload: ScrapeConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> ScrapeConfigResponse:
    """Create a new scrape configuration."""
    payload_data = payload.model_dump(exclude_none=True)
    db_config = ScrapeConfig(**payload_data)
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    if db_config.cron_schedule:
        try:
            await sync_crontab()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=f"Failed to sync cron: {exc}") from exc

    return db_config


@router.get("/{config_id}", response_model=ScrapeConfigResponse)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
) -> ScrapeConfigResponse:
    """Fetch a specific scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config


@router.put("/{config_id}", response_model=ScrapeConfigResponse)
async def update_config(
    config_id: int,
    payload: ScrapeConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScrapeConfigResponse:
    """Update a scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    payload_data = payload.model_dump(exclude_unset=True)
    for key, value in payload_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)

    if payload_data.keys() & SYNC_CRON_FIELDS:
        try:
            await sync_crontab()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"Failed to sync cron: {exc}") from exc

    return config


@router.delete("/{config_id}", status_code=204)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a scrape configuration."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    await db.delete(config)
    await db.commit()

    try:
        await sync_crontab()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Failed to sync cron: {exc}") from exc


@router.post("/{config_id}/run")
async def trigger_config_run(
    config_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """Trigger an on-demand scrape run."""
    result = await db.execute(
        select(ScrapeConfig).where(ScrapeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    config.last_run_status = "queued"
    config.last_run_at = datetime.now(tz=timezone.utc)
    config.last_run_items = None
    await db.commit()

    await set_config_status(config.id, "queued", message="Scrape queued (manual)")

    try:
        await schedule_manual_run(config)
    except RunInProgressError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"config_id": config.id, "message": "Scrape queued"}


@router.get("/{config_id}/status", response_model=Optional[RuntimeStatusResponse])
async def get_config_runtime_status(config_id: int) -> Optional[RuntimeStatusResponse]:
    """Return runtime status for a configuration from Redis."""
    status = await get_config_status(config_id)
    if not status:
        return None

    updated_at_str = status.get("updated_at")
    updated_at = (
        datetime.fromisoformat(updated_at_str)
        if isinstance(updated_at_str, str)
        else datetime.now(tz=timezone.utc)
    )

    items = status.get("items")
    if isinstance(items, str) and items.isdigit():
        items_value = int(items)
    elif isinstance(items, (int, float)):
        items_value = int(items)
    else:
        items_value = None

    return RuntimeStatusResponse(
        config_id=status.get("config_id", config_id),
        status=status.get("status", "unknown"),
        message=status.get("message"),
        updated_at=updated_at,
        items=items_value,
    )
