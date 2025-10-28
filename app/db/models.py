# app/db/models.py
import datetime as dt
from typing import Optional, List
from sqlalchemy import (
    String, Integer, BigInteger, DateTime, Boolean, JSON, Numeric, Index,
    ForeignKey, UniqueConstraint, func, false
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from ..config import settings


class Base(DeclarativeBase):
    pass


class CategoryOption(Base):
    __tablename__ = "category_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))

    __table_args__ = (
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {},
    )


class PlatformOption(Base):
    __tablename__ = "platform_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))

    __table_args__ = (
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {},
    )


class ConditionOption(Base):
    __tablename__ = "condition_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7))

    __table_args__ = (
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {},
    )


class SourceOption(Base):
    __tablename__ = "source_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7))

    __table_args__ = (
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {},
    )


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    vinted_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Basic info
    title: Mapped[Optional[str]] = mapped_column(String(512))
    original_title: Mapped[Optional[str]] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(String(4096))
    language: Mapped[Optional[str]] = mapped_column(String(12))
    currency: Mapped[Optional[str]] = mapped_column(String(12))
    price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    shipping_cents: Mapped[Optional[int]] = mapped_column(Integer)
    total_cents: Mapped[Optional[int]] = mapped_column(Integer)

    # 🌐 Source tracking (vinted, bazos, etc.)
    source: Mapped[Optional[str]] = mapped_column(String(64), default="vinted")

    # Extended fields
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    size: Mapped[Optional[str]] = mapped_column(String(64))
    condition: Mapped[Optional[str]] = mapped_column(String(128))
    location: Mapped[Optional[str]] = mapped_column(String(128))
    seller_id: Mapped[Optional[str]] = mapped_column(String(128))

    # 🧍‍♂️ new field: seller name
    seller_name: Mapped[Optional[str]] = mapped_column(String(128))

    # 🖼️ new field: main photo (first image)
    photo: Mapped[Optional[str]] = mapped_column(String(512))

    # JSON of all photos
    photos: Mapped[Optional[list]] = mapped_column(JSON)

    # 🎮 Category and platform tracking
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    platform_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Array of platform IDs

    # Bookkeeping
    first_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)  # From Vinted catalog API
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    details_scraped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    # Relationships
    prices: Mapped[List["PriceHistory"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    condition_option_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            f"{settings.schema}.condition_options.id"
            if settings.database_url.startswith("postgresql")
            else "condition_options.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    source_option_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            f"{settings.schema}.source_options.id"
            if settings.database_url.startswith("postgresql")
            else "source_options.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    condition_option: Mapped[Optional[ConditionOption]] = relationship(lazy="joined")
    source_option: Mapped[Optional[SourceOption]] = relationship(lazy="joined")

    __table_args__ = (
        UniqueConstraint("url", name="uq_listings_url"),
        Index("ix_listings_vinted_id", "vinted_id"),
        Index("ix_listings_category_id", "category_id"),
        Index("ix_listings_details_scraped", "details_scraped"),
        Index("ix_listings_is_visible", "is_visible"),
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {}
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.schema}.listings.id" if settings.database_url.startswith("postgresql") else "listings.id", ondelete="CASCADE")
    )
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    shipping_cents: Mapped[Optional[int]] = mapped_column(Integer)
    total_cents: Mapped[Optional[int]] = mapped_column(Integer)
    currency: Mapped[Optional[str]] = mapped_column(String(12))

    listing: Mapped[Listing] = relationship(back_populates="prices")

    __table_args__ = (
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {},
    )


class ScrapeConfig(Base):
    __tablename__ = "scrape_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Configuration details
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    search_text: Mapped[str] = mapped_column(String(256), nullable=False)
    categories: Mapped[Optional[list]] = mapped_column(JSON)  # List of category IDs
    platform_ids: Mapped[Optional[list]] = mapped_column(JSON)  # List of platform IDs
    extra_filters: Mapped[Optional[list]] = mapped_column(JSON)  # Additional query parameters (-e)
    locales: Mapped[Optional[list]] = mapped_column(JSON)  # Locales to scrape (maps to --locale)
    order: Mapped[Optional[str]] = mapped_column(String(64))
    fetch_details: Mapped[bool] = mapped_column(Boolean, default=False)
    details_for_new_only: Mapped[bool] = mapped_column(Boolean, default=False)
    use_proxy: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_args: Mapped[Optional[list]] = mapped_column(JSON)  # Additional CLI arguments appended verbatim
    error_wait_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    max_retries: Mapped[Optional[int]] = mapped_column(Integer, default=3)
    base_url: Mapped[Optional[str]] = mapped_column(String(512))
    details_strategy: Mapped[Optional[str]] = mapped_column(String(32), default="browser")
    details_concurrency: Mapped[Optional[int]] = mapped_column(Integer, default=2)
    healthcheck_ping_url: Mapped[Optional[str]] = mapped_column(String(512))

    # Scraping parameters
    max_pages: Mapped[int] = mapped_column(Integer, default=5)
    per_page: Mapped[int] = mapped_column(Integer, default=24)
    delay: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)

    # Cron schedule
    cron_schedule: Mapped[Optional[str]] = mapped_column(String(128))  # e.g., "0 */6 * * *"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    last_run_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(64))  # "success", "failed", "running"
    last_run_items: Mapped[Optional[int]] = mapped_column(Integer)  # Number of items scraped
    last_health_status: Mapped[Optional[str]] = mapped_column(String(64))  # "ok", "fail"
    last_health_check_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_scrape_configs_active", "is_active"),
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {}
    )
