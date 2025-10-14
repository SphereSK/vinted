from __future__ import annotations
from typing import Optional, List
from vinted_api_kit import VintedApi, CatalogItem, DetailedItem

def cents_from_price(price: Optional[float | int]) -> Optional[int]:
    if price is None:
        return None
    try:
        return int(round(float(price) * 100))
    except Exception:
        return None

async def fetch_page_items(v: VintedApi, url: str, per_page: int) -> list[CatalogItem]:
    return await v.search_items(url=url, per_page=per_page)

async def fetch_detail(v: VintedApi, item_url: str) -> Optional[DetailedItem]:
    try:
        return await v.item_details(url=item_url)
    except Exception:
        return None

def photos_from_catalog_item(it: CatalogItem) -> Optional[list]:
    """
    Try to get at least one image from catalog item without hitting details.
    The library fields can vary; we defensively probe common names.
    """
    candidates = []
    # very common naming variants
    for attr in (
        "photo", "photo_url", "image", "image_url", "thumbnail_url",
        "image_small_url", "image_big_url", "cover_photo_url",
        "images", "photos",
    ):
        val = getattr(it, attr, None)
        if not val:
            continue
        if isinstance(val, str):
            candidates.append(val)
        elif isinstance(val, list):
            for x in val:
                if isinstance(x, str):
                    candidates.append(x)
                elif isinstance(x, dict):
                    # look for url-ish keys
                    for k in ("url", "full", "original", "large", "small"):
                        if k in x and isinstance(x[k], str):
                            candidates.append(x[k])
                            break
        elif isinstance(val, dict):
            for k in ("url", "full", "original", "large", "small"):
                if k in val and isinstance(val[k], str):
                    candidates.append(val[k])
                    break

    # de-dup while preserving order
    seen = set()
    out = []
    for u in candidates:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out or None

def photos_from_detail(detail: DetailedItem) -> Optional[list]:
    raw = getattr(detail, "photos", None)
    if not isinstance(raw, list):
        return None
    out = []
    for p in raw:
        if isinstance(p, str):
            out.append(p)
        elif isinstance(p, dict):
            for k in ("url", "full", "original", "large", "small"):
                if k in p and isinstance(p[k], str):
                    out.append(p[k]); break
    # de-dup
    seen = set()
    uniq = []
    for u in out:
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq or None
