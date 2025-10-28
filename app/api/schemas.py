"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.scheduler import (
    sanitize_extra_arguments,
    sanitize_locales,
    validate_base_url,
    validate_cron_expression,
    validate_details_strategy,
    validate_order,
    validate_positive_int,
)


# Listing schemas
class ListingBase(BaseModel):
    title: Optional[str] = None
    url: str
    price_cents: Optional[int] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    seller_name: Optional[str] = None
    photo: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None  # Source marketplace (vinted, bazos, etc.)
    category_id: Optional[int] = None
    platform_ids: Optional[list] = None
    details_scraped: bool = False


class ListingResponse(ListingBase):
    id: int
    vinted_id: Optional[int] = None
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    is_visible: bool  # From Vinted catalog API - tracks if item is visible on marketplace
    is_sold: bool
    previous_price_cents: Optional[int] = None
    price_change: Optional[str] = None  # "up", "down", "same"
    category_name: Optional[str] = None
    platform_names: Optional[list[str]] = None
    condition_option_id: Optional[int] = None
    condition_code: Optional[str] = None
    condition_label: Optional[str] = None
    source_option_id: Optional[int] = None
    source_label: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ListingDetail(ListingResponse):
    photos: Optional[list] = None
    price_history: list = Field(default_factory=list)


class ListingListResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    available_currencies: list[str] = Field(default_factory=list)
    available_conditions: list["ConditionResponse"] = Field(default_factory=list)
    available_categories: list["CategoryResponse"] = Field(default_factory=list)
    available_platforms: list["PlatformResponse"] = Field(default_factory=list)
    available_sources: list["SourceResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Price history schemas
class PriceHistoryResponse(BaseModel):
    id: int
    observed_at: datetime
    price_cents: Optional[int] = None
    currency: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Scrape config schemas
class ScrapeConfigCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=128)
    search_text: str = Field(..., min_length=1, max_length=256)
    categories: Optional[list[int]] = None
    platform_ids: Optional[list[int]] = None
    order: Optional[str] = Field(None, max_length=64)
    extra_filters: Optional[list[str]] = Field(
        default=None,
        alias="extra",
        description="Extra query parameters passed via repeated -e flags.",
    )
    locales: Optional[list[str]] = Field(
        default=None,
        description="Locales to scrape; mapped to repeated --locale flags.",
    )
    extra_args: Optional[list[str]] = Field(
        default=None,
        description="Additional CLI arguments appended to scheduled scrape commands.",
    )
    max_pages: int = Field(default=5, ge=1, le=1000)
    per_page: int = Field(default=24, ge=1, le=100)
    delay: float = Field(default=1.0, ge=0.1, le=10.0)
    fetch_details: bool = False
    details_for_new_only: bool = False
    use_proxy: bool = True
    error_wait_minutes: int = Field(default=30, ge=0)
    max_retries: int = Field(default=3, ge=0)
    base_url: Optional[str] = Field(None, max_length=512)
    details_strategy: str = Field(default="browser", max_length=32)
    details_concurrency: int = Field(default=2, ge=1, le=16)
    cron_schedule: Optional[str] = Field(None, max_length=128)
    is_active: bool = True
    healthcheck_ping_url: Optional[str] = Field(
        default=None,
        max_length=512,
        description="Healthchecks.io ping URL; append /start and /fail automatically.",
    )

    @field_validator("cron_schedule")
    @classmethod
    def _validate_cron_schedule(cls, value: Optional[str]) -> Optional[str]:
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

    @field_validator("extra_args", mode="before")
    @classmethod
    def _validate_extra_args(cls, value):
        if value is None:
            return None
        sanitized = sanitize_extra_arguments(value)
        return sanitized or None

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_base_url(value)

    @field_validator("details_strategy")
    @classmethod
    def _validate_details_strategy(cls, value: str) -> str:
        validated = validate_details_strategy(value)
        return validated or "browser"

    @field_validator("error_wait_minutes")
    @classmethod
    def _validate_error_wait(cls, value: int) -> int:
        validated = validate_positive_int(value, "error_wait_minutes", minimum=0)
        assert validated is not None
        return validated

    @field_validator("max_retries")
    @classmethod
    def _validate_max_retries(cls, value: int) -> int:
        validated = validate_positive_int(value, "max_retries", minimum=0)
        assert validated is not None
        return validated

    @field_validator("details_concurrency")
    @classmethod
    def _validate_details_concurrency(cls, value: int) -> int:
        validated = validate_positive_int(value, "details_concurrency", minimum=1)
        assert validated is not None
        return validated

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("healthcheck_ping_url")
    @classmethod
    def _validate_healthcheck(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return validate_base_url(value)


class ScrapeConfigUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    search_text: Optional[str] = Field(None, min_length=1, max_length=256)
    categories: Optional[list[int]] = None
    platform_ids: Optional[list[int]] = None
    order: Optional[str] = Field(None, max_length=64)
    extra_filters: Optional[list[str]] = Field(
        default=None,
        alias="extra",
        description="Extra query parameters passed via repeated -e flags.",
    )
    locales: Optional[list[str]] = None
    extra_args: Optional[list[str]] = Field(
        default=None,
        description="Additional CLI arguments appended to scheduled scrape commands.",
    )
    max_pages: Optional[int] = Field(None, ge=1, le=1000)
    per_page: Optional[int] = Field(None, ge=1, le=100)
    delay: Optional[float] = Field(None, ge=0.1, le=10.0)
    fetch_details: Optional[bool] = None
    details_for_new_only: Optional[bool] = None
    use_proxy: Optional[bool] = None
    error_wait_minutes: Optional[int] = Field(None, ge=0)
    max_retries: Optional[int] = Field(None, ge=0)
    base_url: Optional[str] = Field(None, max_length=512)
    details_strategy: Optional[str] = Field(None, max_length=32)
    details_concurrency: Optional[int] = Field(None, ge=1, le=16)
    cron_schedule: Optional[str] = Field(None, max_length=128)
    is_active: Optional[bool] = None
    healthcheck_ping_url: Optional[str] = Field(None, max_length=512)

    @field_validator("cron_schedule")
    @classmethod
    def _validate_cron_schedule(cls, value: Optional[str]) -> Optional[str]:
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

    @field_validator("extra_args", mode="before")
    @classmethod
    def _validate_extra_args(cls, value):
        if value is None:
            return None
        sanitized = sanitize_extra_arguments(value)
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

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("healthcheck_ping_url")
    @classmethod
    def _validate_healthcheck(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return validate_base_url(value)


class ScrapeConfigResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    name: str
    search_text: str
    categories: Optional[list] = None
    platform_ids: Optional[list] = None
    order: Optional[str] = None
    extra_filters: Optional[list[str]] = Field(default=None, alias="extra")
    locales: Optional[list[str]] = None
    extra_args: Optional[list[str]] = None
    max_pages: int
    per_page: int
    delay: float
    fetch_details: bool
    details_for_new_only: bool
    use_proxy: bool
    error_wait_minutes: Optional[int] = None
    max_retries: Optional[int] = None
    base_url: Optional[str] = None
    details_strategy: Optional[str] = None
    details_concurrency: Optional[int] = None
    cron_schedule: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_items: Optional[int] = None
    healthcheck_ping_url: Optional[str] = None


# Category schemas
class CategoryResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None


class PlatformResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None


class ConditionResponse(BaseModel):
    id: int
    code: str
    label: str
    color: Optional[str] = None


class SourceResponse(BaseModel):
    id: int
    code: str
    label: str
    color: Optional[str] = None


# Stats schemas
class StatsResponse(BaseModel):
    total_listings: int
    active_listings: int
    total_scraped_today: int
    total_scraped_last_7_days: int
    total_scraped_last_30_days: int
    active_listings_last_7_days: int
    active_listings_last_30_days: int
    inactive_listings_today: int
    inactive_listings_last_7_days: int
    inactive_listings_last_30_days: int
    active_listings_day_before_previous: int
    total_scraped_last_7_days_day_before_previous: int
    total_scraped_last_30_days_day_before_previous: int
    active_listings_last_7_days_day_before_previous: int
    active_listings_last_30_days_day_before_previous: int
    inactive_listings_day_before_previous: int
    inactive_listings_last_7_days_day_before_previous: int
    inactive_listings_last_30_days_day_before_previous: int
    active_configs: int
    avg_price_cents: Optional[float] = None
    min_price_cents: Optional[int] = None
    max_price_cents: Optional[int] = None
    price_increase_count: int
    price_decrease_count: int
    price_unchanged_count: int
    total_listings_previous_day: int
    total_listings_previous_7_days: int
    total_listings_previous_30_days: int
    total_listings_day_before_previous: int
    total_scraped_previous_day: int
    total_scraped_previous_7_days: int
    total_scraped_previous_30_days: int
    source_stats: dict[str, dict[str, int]] = Field(default_factory=dict)

class ListingsByPeriod(BaseModel):
    period: str
    new_listings: int
    total_listings: int

class ListingsByPeriodResponse(BaseModel):
    items: list[ListingsByPeriod]
