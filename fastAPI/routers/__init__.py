"""API router modules for the FastAPI service."""

from . import cron, listings, stats, configs, taxonomy  # noqa: F401

__all__ = [
    "cron",
    "listings",
    "stats",
    "configs",
    "taxonomy",
]
