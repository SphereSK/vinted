"""Cron scheduling endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.scheduler import build_scrape_command, list_scheduled_jobs, sync_crontab
from fastAPI.dependencies import require_api_key
from fastAPI.schemas import CronCommandRequest, CronCommandResponse

router = APIRouter(
    prefix="/api/cron",
    tags=["cron"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/jobs")
async def list_jobs() -> dict:
    """Return configured cron jobs."""
    try:
        jobs = await list_scheduled_jobs()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"jobs": jobs}


@router.post("/sync")
async def sync_jobs() -> dict:
    """Trigger cron synchronization."""
    try:
        await sync_crontab()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"message": "Crontab synced successfully"}


@router.post("/build", response_model=CronCommandResponse)
async def build_job_command(payload: CronCommandRequest) -> CronCommandResponse:
    """Return the CLI command a cron job would execute for the supplied payload."""
    try:
        command = build_scrape_command(
            search_text=payload.search_text,
            max_pages=payload.max_pages,
            per_page=payload.per_page,
            delay=payload.delay,
            categories=payload.categories,
            platform_ids=payload.platform_ids,
            fetch_details=payload.fetch_details,
            details_for_new_only=payload.details_for_new_only,
            use_proxy=payload.use_proxy,
            extra_filters=payload.extra_filters,
            order=payload.order,
            locales=payload.locales,
            error_wait_minutes=payload.error_wait_minutes,
            max_retries=payload.max_retries,
            base_url=payload.base_url,
            details_strategy=payload.details_strategy,
            details_concurrency=payload.details_concurrency,
            extra_args=payload.extra_args,
            workdir=payload.workdir,
            healthcheck_ping_url=payload.healthcheck_ping_url,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CronCommandResponse(command=command, schedule=payload.schedule)
