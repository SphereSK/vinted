"""Utility helpers for determining detail scrape completeness."""
from __future__ import annotations

from typing import Iterable, Mapping, Optional


REQUIRED_DETAIL_FIELDS = ("shipping_cents", "brand", "location", "description", "photos")


def _non_empty_string(value: Optional[str]) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _has_photos(value: object) -> bool:
    if isinstance(value, (list, tuple)):
        return any(bool(photo) for photo in value)
    return False


def compute_details_scraped_flag(data: Mapping[str, object]) -> bool:
    """
    Determine if a listing has successfully captured the required detail fields.

    Args:
        data: Mapping of listing attributes to inspect.
    """
    shipping_present = data.get("shipping_cents") is not None
    brand_present = _non_empty_string(data.get("brand"))  # type: ignore[arg-type]
    location_present = _non_empty_string(data.get("location"))  # type: ignore[arg-type]
    description_present = _non_empty_string(data.get("description"))  # type: ignore[arg-type]
    photos_present = _has_photos(data.get("photos"))

    return all(
        (
            shipping_present,
            brand_present,
            location_present,
            photos_present,
            description_present,
        )
    )


def missing_detail_fields(data: Mapping[str, object]) -> Iterable[str]:
    """Yield the detail fields that are currently missing."""
    if data.get("shipping_cents") is None:
        yield "shipping_cents"
    if not _non_empty_string(data.get("brand")):  # type: ignore[arg-type]
        yield "brand"
    if not _non_empty_string(data.get("location")):  # type: ignore[arg-type]
        yield "location"
    if not _non_empty_string(data.get("description")):  # type: ignore[arg-type]
        yield "description"
    if not _has_photos(data.get("photos")):
        yield "photos"
