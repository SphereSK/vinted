"""API router modules for the FastAPI service."""

from . import configs, cron, details, listings, stats, taxonomy  # noqa: F401

__all__ = [
    "configs",
    "cron",
    "details",
    "listings",
    "stats",
    "taxonomy",
]
