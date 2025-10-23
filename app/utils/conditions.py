"""Helpers for normalising condition values against the canonical taxonomy."""
from __future__ import annotations

from app.data.taxonomy import (
    MASTER_CONDITIONS,
    CONDITION_CODE_TO_ID,
    CONDITION_LABEL_TO_ID,
)

_CONDITION_ALIAS_TO_CODE = {
    "new with tags": "new_with_tags",
    "brand new": "new",
    "new": "new",
    "like new": "like_new",
    "very good": "very_good",
    "good": "good",
    "satisfactory": "satisfactory",
    "acceptable": "satisfactory",
    "fair": "fair",
    "poor": "poor",
    "needs repair": "needs_repair",
    "for parts": "needs_repair",
    "unknown": "unknown",
    "not specified": "unknown",
}


def normalize_condition(value: str | None) -> tuple[int | None, str | None, str | None]:
    """
    Convert a raw condition string into canonical representations.

    Returns:
        Tuple of (condition_id, code, label).
    """

    if value is None:
        return None, None, None

    raw = value.strip()
    if not raw:
        return None, None, None

    lower = raw.lower()
    code = _CONDITION_ALIAS_TO_CODE.get(lower, lower.replace("-", "_"))

    if code in CONDITION_CODE_TO_ID:
        condition_id = CONDITION_CODE_TO_ID[code]
        entry = MASTER_CONDITIONS[condition_id]
        return condition_id, entry["code"], entry["label"]

    if lower in CONDITION_LABEL_TO_ID:
        condition_id = CONDITION_LABEL_TO_ID[lower]
        entry = MASTER_CONDITIONS[condition_id]
        return condition_id, entry["code"], entry["label"]

    slug = (
        lower.replace("-", " ")
        .replace("/", " ")
        .replace("_", " ")
        .replace("  ", " ")
        .strip()
    )
    slug = slug.replace(" ", "_")

    if slug in CONDITION_CODE_TO_ID:
        condition_id = CONDITION_CODE_TO_ID[slug]
        entry = MASTER_CONDITIONS[condition_id]
        return condition_id, entry["code"], entry["label"]

    fallback_label = raw.title()
    return None, slug or "unknown", fallback_label
