"""Utilities for coordinating manual scraper runs from the FastAPI service."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func, select

from app.db.models import Listing, ScrapeConfig
from app.db.session import Session, init_db
from app.scheduler import build_scrape_command
from fastAPI.redis import set_config_status


class RunInProgressError(RuntimeError):
    """Raised when a manual scrape is already running for the configuration."""


_active_runs: dict[int, asyncio.Task[None]] = {}
_lock = asyncio.Lock()


async def schedule_manual_run(config: ScrapeConfig) -> None:
    """
    Launch a manual scrape run for the supplied configuration.

    Raises:
        RunInProgressError: if a run is already active for this configuration.
    """

    config_data = _serialize_config(config)
    config_id = config_data["id"]

    async with _lock:
        if config_id in _active_runs:
            raise RunInProgressError(f"Scrape config {config_id} is already running")

        task = asyncio.create_task(_execute_manual_run(config_data), name=f"scrape-config-{config_id}")
        task.add_done_callback(lambda finished, cid=config_id: asyncio.create_task(_cleanup(cid, finished)))
        _active_runs[config_id] = task


async def _cleanup(config_id: int, task: asyncio.Task[None]) -> None:
    try:
        await task
    finally:
        async with _lock:
            _active_runs.pop(config_id, None)


def _serialize_config(config: ScrapeConfig) -> Dict[str, Any]:
    """Extract plain-Python values from a ScrapeConfig ORM instance."""
    def _normalize_list(value: Optional[list]) -> list:
        if not value:
            return []
        return list(value)

    delay_value = float(config.delay) if config.delay is not None else 1.0

    return {
        "id": config.id,
        "search_text": config.search_text,
        "categories": _normalize_list(config.categories),
        "platform_ids": _normalize_list(config.platform_ids),
        "extra_filters": _normalize_list(config.extra_filters),
        "locales": _normalize_list(config.locales),
        "extra_args": _normalize_list(config.extra_args),
        "order": config.order,
        "max_pages": int(config.max_pages) if config.max_pages is not None else 5,
        "per_page": int(config.per_page) if config.per_page is not None else 24,
        "delay": delay_value if delay_value > 0 else 1.0,
        "fetch_details": bool(config.fetch_details),
        "details_for_new_only": bool(config.details_for_new_only),
        "use_proxy": bool(config.use_proxy),
        "error_wait_minutes": config.error_wait_minutes,
        "max_retries": config.max_retries,
        "base_url": config.base_url,
        "details_strategy": config.details_strategy,
        "details_concurrency": config.details_concurrency,
        "healthcheck_ping_url": config.healthcheck_ping_url,
    }


async def _execute_manual_run(config_data: Dict[str, Any]) -> None:
    config_id = config_data["id"]

    try:
        await init_db()

        await _update_status(
            config_id,
            "running",
            message="Manual scrape triggered",
        )

        count_before = await _count_listings()
        command = build_scrape_command(
            search_text=config_data["search_text"],
            max_pages=config_data["max_pages"],
            per_page=config_data["per_page"],
            delay=config_data["delay"],
            categories=config_data["categories"] or None,
            platform_ids=config_data["platform_ids"] or None,
            fetch_details=config_data["fetch_details"],
            details_for_new_only=config_data["details_for_new_only"],
            use_proxy=config_data["use_proxy"],
            extra_filters=config_data["extra_filters"] or None,
            order=config_data["order"],
            locales=config_data["locales"] or None,
            error_wait_minutes=config_data["error_wait_minutes"],
            max_retries=config_data["max_retries"],
            base_url=config_data["base_url"],
            details_strategy=config_data["details_strategy"],
            details_concurrency=config_data["details_concurrency"],
            extra_args=config_data["extra_args"] or None,
            healthcheck_ping_url=config_data["healthcheck_ping_url"],
            config_id=config_id,
        )

        process = await asyncio.create_subprocess_shell(command)
        return_code = await process.wait()

        if return_code == 0:
            count_after = await _count_listings()
            new_items = max(count_after - count_before, 0)
            await _update_status(
                config_id,
                "success",
                items=new_items,
                message=f"Scrape completed successfully ({new_items} new items)",
            )
        else:
            await _update_status(
                config_id,
                "failed",
                message=f"Scrape command exited with code {return_code}",
            )
    except Exception as exc:  # pragma: no cover - defensive
        await _update_status(
            config_id,
            "failed",
            message=f"Scrape failed: {exc}",
        )
        raise


async def _count_listings() -> int:
    async with Session() as session:
        result = await session.execute(select(func.count()).select_from(Listing))
        return int(result.scalar() or 0)


async def _update_status(
    config_id: int,
    status: str,
    *,
    items: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    extra = {"items": items} if items is not None else None

    await set_config_status(config_id, status, message=message, extra=extra)

    async with Session() as session:
        config = await session.get(ScrapeConfig, config_id)
        if not config:
            return

        config.last_run_status = status
        config.last_run_at = datetime.now(tz=timezone.utc)
        if items is not None:
            config.last_run_items = items
        elif status in {"queued", "running"}:
            config.last_run_items = None

        await session.commit()
