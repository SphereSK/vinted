# app/db/models.py
import datetime as dt
from typing import Optional, List
from sqlalchemy import (
    String, Integer, BigInteger, DateTime, Boolean, JSON, Numeric, Index,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from ..config import settings


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    vinted_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Basic info
    title: Mapped[Optional[str]] = mapped_column(String(512))
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

    # Relationships
    prices: Mapped[List["PriceHistory"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("url", name="uq_listings_url"),
        Index("ix_listings_vinted_id", "vinted_id"),
        Index("ix_listings_category_id", "category_id"),
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

    # Scraping parameters
    max_pages: Mapped[int] = mapped_column(Integer, default=5)
    per_page: Mapped[int] = mapped_column(Integer, default=24)
    delay: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)
    fetch_details: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cron schedule
    cron_schedule: Mapped[Optional[str]] = mapped_column(String(128))  # e.g., "0 */6 * * *"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    last_run_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(64))  # "success", "failed", "running"
    last_run_items: Mapped[Optional[int]] = mapped_column(Integer)  # Number of items scraped

    __table_args__ = (
        Index("ix_scrape_configs_active", "is_active"),
        {"schema": settings.schema} if settings.database_url.startswith("postgresql") else {}
    )
