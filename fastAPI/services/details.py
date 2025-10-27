"""Service helpers for running the Scrapy detail worker."""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select

from app.db.models import Listing
from app.db.session import Session
from fastAPI.redis import set_detail_status


class DetailRunInProgressError(RuntimeError):
    """Raised when a detail run is already active."""


@dataclass(frozen=True)
class DetailRunConfig:
    batch_size: int = 100
    source: Optional[str] = None
    limit: Optional[int] = None
    locale: str = "sk"
    warmup: bool = True
    download_delay: Optional[float] = None
    concurrent_requests: Optional[int] = None
    log_level: Optional[str] = None


_active_detail_task: Optional[asyncio.Task[None]] = None
_detail_lock = asyncio.Lock()


async def schedule_detail_run(config: DetailRunConfig) -> None:
    """Schedule a detail scrape run if no other run is active."""
    global _active_detail_task

    async with _detail_lock:
        if _active_detail_task and not _active_detail_task.done():
            raise DetailRunInProgressError("Detail scraper already running.")

        await set_detail_status(
            "queued",
            message="Detail scrape queued",
            extra={"source": config.source or "all", "batch_size": config.batch_size},
        )

        task = asyncio.create_task(_run_detail_subprocess(config))
        task.add_done_callback(lambda finished: _clear_task(finished))
        _active_detail_task = task


def _clear_task(task: asyncio.Task[None]) -> None:
    global _active_detail_task
    if task.done() and task.exception():
        # Handled downstream; we just ensure the reference is cleared.
        pass
    _active_detail_task = None


async def _run_detail_subprocess(config: DetailRunConfig) -> None:
    remaining_before = await _count_remaining(config.source)
    await set_detail_status(
        "running",
        message="Detail scrape in progress",
        extra={
            "batch_size": config.batch_size,
            "source": config.source or "all",
            "remaining_before": remaining_before,
        },
    )

    command = _build_detail_command(config)
    process = await asyncio.create_subprocess_exec(*command)

    return_code = await process.wait()
    if return_code != 0:
        await set_detail_status(
            "failed",
            message=f"Detail scraper exited with code {return_code}",
            extra={"batch_size": config.batch_size, "source": config.source or "all"},
        )
        return

    remaining_after = await _count_remaining(config.source)
    processed = max(remaining_before - remaining_after, 0)
    await set_detail_status(
        "success",
        message=f"Detail scrape complete ({processed} updated)",
        extra={
            "processed": processed,
            "remaining_after": remaining_after,
            "source": config.source or "all",
        },
    )


def _build_detail_command(config: DetailRunConfig) -> list[str]:
    command = [sys.executable, "-m", "app.cli", "scrape-details", "--batch-size", str(config.batch_size)]
    if config.source:
        command.extend(["--source", config.source])
    if config.limit:
        command.extend(["--limit", str(config.limit)])
    if config.locale:
        command.extend(["--locale", config.locale])
    if not config.warmup:
        command.append("--no-warmup")
    if config.download_delay is not None:
        command.extend(["--download-delay", str(config.download_delay)])
    if config.concurrent_requests is not None:
        command.extend(["--concurrent-requests", str(config.concurrent_requests)])
    if config.log_level:
        command.extend(["--log-level", config.log_level])
    return command


async def _count_remaining(source: Optional[str]) -> int:
    filters = [Listing.is_active.is_(True), Listing.details_scraped.is_(False)]
    if source:
        filters.append(Listing.source == source)

    async with Session() as session:
        result = await session.execute(select(func.count()).select_from(Listing).where(*filters))
        return int(result.scalar() or 0)
