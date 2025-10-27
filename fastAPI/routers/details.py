"""Endpoints for managing the detail scraping worker."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from fastAPI.dependencies import require_api_key
from fastAPI.redis import get_detail_status
from fastAPI.schemas import DetailRunRequest, DetailStatusResponse
from fastAPI.services.details import (
    DetailRunConfig,
    DetailRunInProgressError,
    schedule_detail_run,
)

router = APIRouter(
    prefix="/api/details",
    tags=["details"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/run")
async def trigger_detail_run(payload: DetailRunRequest) -> dict[str, str]:
    """Queue a detail scraping run."""
    config = DetailRunConfig(
        batch_size=payload.batch_size,
        source=payload.source,
        limit=payload.limit,
        locale=payload.locale,
        warmup=payload.warmup,
        download_delay=payload.download_delay,
        concurrent_requests=payload.concurrent_requests,
        log_level=payload.log_level,
    )

    try:
        await schedule_detail_run(config)
    except DetailRunInProgressError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"message": "Detail scrape queued"}


@router.get("/status", response_model=Optional[DetailStatusResponse])
async def get_detail_run_status() -> Optional[DetailStatusResponse]:
    """Return the latest status emitted by the detail scraper."""
    status = await get_detail_status()
    if not status:
        return None

    updated_at_str = status.get("updated_at")
    updated_at = (
        datetime.fromisoformat(updated_at_str)
        if isinstance(updated_at_str, str)
        else datetime.now(tz=timezone.utc)
    )

    def _to_int(value: object) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return DetailStatusResponse(
        status=status.get("status", "unknown"),
        message=status.get("message"),
        updated_at=updated_at,
        processed=_to_int(status.get("processed")),
        remaining_after=_to_int(status.get("remaining_after")),
        remaining_before=_to_int(status.get("remaining_before")),
        batch_size=_to_int(status.get("batch_size")),
        source=status.get("source"),
    )
