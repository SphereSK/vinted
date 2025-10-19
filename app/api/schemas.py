"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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


class ListingResponse(ListingBase):
    id: int
    vinted_id: Optional[int] = None
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    previous_price_cents: Optional[int] = None
    price_change: Optional[str] = None  # "up", "down", "same"

    class Config:
        from_attributes = True


class ListingDetail(ListingResponse):
    photos: Optional[list] = None
    price_history: list = []


# Price history schemas
class PriceHistoryResponse(BaseModel):
    id: int
    observed_at: datetime
    price_cents: Optional[int] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


# Scrape config schemas
class ScrapeConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    search_text: str = Field(..., min_length=1, max_length=256)
    categories: Optional[list[int]] = None
    platform_ids: Optional[list[int]] = None
    max_pages: int = Field(default=5, ge=1, le=1000)
    per_page: int = Field(default=24, ge=1, le=100)
    delay: float = Field(default=1.0, ge=0.1, le=10.0)
    fetch_details: bool = False
    cron_schedule: Optional[str] = Field(None, max_length=128)
    is_active: bool = True


class ScrapeConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    search_text: Optional[str] = Field(None, min_length=1, max_length=256)
    categories: Optional[list[int]] = None
    platform_ids: Optional[list[int]] = None
    max_pages: Optional[int] = Field(None, ge=1, le=1000)
    per_page: Optional[int] = Field(None, ge=1, le=100)
    delay: Optional[float] = Field(None, ge=0.1, le=10.0)
    fetch_details: Optional[bool] = None
    cron_schedule: Optional[str] = Field(None, max_length=128)
    is_active: Optional[bool] = None


class ScrapeConfigResponse(BaseModel):
    id: int
    name: str
    search_text: str
    categories: Optional[list] = None
    platform_ids: Optional[list] = None
    max_pages: int
    per_page: int
    delay: float
    fetch_details: bool
    cron_schedule: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_items: Optional[int] = None

    class Config:
        from_attributes = True


# Category schemas
class CategoryResponse(BaseModel):
    id: int
    name: str


# Stats schemas
class StatsResponse(BaseModel):
    total_listings: int
    active_listings: int
    total_scraped_today: int
    active_configs: int
    avg_price_cents: Optional[float] = None
