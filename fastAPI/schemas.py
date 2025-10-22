"""Additional response models specific to the FastAPI service."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import settings
from app.scheduler import (
    sanitize_extra_arguments,
    sanitize_locales,
    validate_base_url,
    validate_cron_expression,
    validate_details_strategy,
    validate_order,
    validate_positive_int,
)


class RuntimeStatusResponse(BaseModel):
    config_id: int
    status: str
    message: Optional[str] = None
    updated_at: datetime
    items: Optional[int] = None


class CronCommandRequest(BaseModel):
    """Payload describing a scrape cron job."""

    model_config = ConfigDict(populate_by_name=True)

    schedule: Optional[str] = Field(
        None,
        description="Cron expression (five-part) that will schedule the job.",
        max_length=128,
    )
    search_text: str = Field(..., min_length=1, max_length=256)
    max_pages: int = Field(default=settings.max_pages, ge=1, le=1000)
    per_page: int = Field(default=settings.per_page, ge=1, le=200)
    delay: float = Field(default=settings.request_delay, ge=0.0, le=30.0)
    categories: Optional[list[int]] = None
    platform_ids: Optional[list[int]] = None
    fetch_details: bool = False
    details_for_new_only: bool = False
    use_proxy: Optional[bool] = None
    order: Optional[str] = Field(
        default=None,
        description="Sort order passed to the CLI (e.g., newest_first).",
        max_length=64,
    )
    extra_filters: Optional[list[str]] = Field(
        default=None,
        alias="extra",
        description="Extra query parameters passed via repeated -e flags.",
    )
    locales: Optional[list[str]] = Field(
        default=None,
        description="Locales to scrape; mapped to repeated --locale flags.",
    )
    error_wait_minutes: Optional[int] = Field(
        default=None,
        description="Minutes to wait when encountering 403/rate limits.",
        ge=0,
        le=240,
    )
    max_retries: Optional[int] = Field(
        default=None,
        description="Maximum retries per page on 403 errors.",
        ge=0,
        le=10,
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Override the base catalog URL (must be http/https).",
        max_length=512,
    )
    details_strategy: Optional[str] = Field(
        default=None,
        description="Detail fetching strategy (browser/http).",
        max_length=32,
    )
    details_concurrency: Optional[int] = Field(
        default=None,
        description="Detail fetching concurrency when using --fetch-details.",
        ge=1,
        le=16,
    )
    extra_args: Optional[list[str]] = Field(
        default=None,
        description="Additional CLI arguments appended to the scraper command.",
    )
    workdir: Optional[str] = Field(
        default=None,
        description="Override working directory used when composing the command.",
    )
    healthcheck_ping_url: Optional[str] = Field(
        default=None,
        description="Healthchecks.io base ping URL; /start and /fail are appended automatically.",
        max_length=512,
    )

    @field_validator("schedule")
    @classmethod
    def _validate_schedule(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return validate_cron_expression(value)

    @field_validator("order")
    @classmethod
    def _validate_order(cls, value: Optional[str]) -> Optional[str]:
        return validate_order(value)

    @field_validator("extra_filters", mode="before")
    @classmethod
    def _validate_extra_filters(cls, value):
        if value is None:
            return None
        sanitized = sanitize_extra_arguments(value)
        return sanitized or None

    @field_validator("locales", mode="before")
    @classmethod
    def _validate_locales(cls, value):
        if value is None:
            return None
        sanitized = sanitize_locales(value)
        return sanitized or None

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_base_url(value)

    @field_validator("details_strategy")
    @classmethod
    def _validate_details_strategy(cls, value: Optional[str]) -> Optional[str]:
        return validate_details_strategy(value)

    @field_validator("error_wait_minutes")
    @classmethod
    def _validate_error_wait(cls, value: Optional[int]) -> Optional[int]:
        return validate_positive_int(value, "error_wait_minutes", minimum=0)

    @field_validator("max_retries")
    @classmethod
    def _validate_max_retries(cls, value: Optional[int]) -> Optional[int]:
        return validate_positive_int(value, "max_retries", minimum=0)

    @field_validator("details_concurrency")
    @classmethod
    def _validate_details_concurrency(cls, value: Optional[int]) -> Optional[int]:
        return validate_positive_int(value, "details_concurrency", minimum=1)

    @field_validator("extra_args", mode="before")
    @classmethod
    def _validate_extra_args(cls, value):
        if value is None:
            return None
        sanitized = sanitize_extra_arguments(value)
        return sanitized or None

    @field_validator("healthcheck_ping_url")
    @classmethod
    def _validate_healthcheck(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return validate_base_url(value)


class CronCommandResponse(BaseModel):
    """Result of building a cron job command."""

    command: str
    schedule: Optional[str] = None
