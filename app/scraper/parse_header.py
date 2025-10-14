# app/scraper/parse_header.py
from typing import Any, Dict, List, Optional
from vinted_api_kit.models import CatalogItem

def parse_catalog_item(it: CatalogItem) -> Dict[str, Any]:
    """
    Parse data from a catalog listing into a flat dict
    usable for DB insertion. Extracts available metadata from catalog API.
    """
    def safe_attr(obj, name, default=None):
        return getattr(obj, name, default)

    title = safe_attr(it, "title")
    price = safe_attr(it, "price")
    currency = safe_attr(it, "currency")
    url = safe_attr(it, "url")
    item_id = safe_attr(it, "id") or safe_attr(it, "item_id")
    photo = None

    # Extract best-effort photo
    for key in ("photo", "photo_url", "image", "image_url", "cover_photo_url"):
        val = safe_attr(it, key)
        if isinstance(val, str):
            photo = val
            break
        elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], str):
            photo = val[0]
            break

    # Extract seller name and ID from catalog API (available in raw_data)
    seller_name = None
    seller_id = None
    raw_data = safe_attr(it, "raw_data", {})
    if raw_data and isinstance(raw_data, dict):
        user_data = raw_data.get("user", {})
        if user_data:
            seller_name = user_data.get("login") or user_data.get("name") or user_data.get("username")
            # Convert seller_id to string for database VARCHAR column
            sid = user_data.get("id")
            seller_id = str(sid) if sid is not None else None

        # Extract condition from raw_data
        condition = raw_data.get("status")

        # Extract brand, size if available
        brand = raw_data.get("brand_title")
        size = raw_data.get("size_title")
    else:
        # Fallback to direct attributes
        brand = safe_attr(it, "brand_title")
        size = safe_attr(it, "size_title")
        condition = safe_attr(it, "status")

    # Location is NOT available in catalog API - must fetch HTML details

    return {
        "vinted_id": item_id,
        "url": url,
        "title": title,
        "currency": currency,
        "price": float(price) if price is not None else None,
        "photo": photo,
        "seller_name": seller_name,
        "seller_id": seller_id,
        "brand": brand,
        "size": size,
        "condition": condition,
    }

def parse_catalog_page(items: List[CatalogItem]) -> List[Dict[str, Any]]:
    """Parse all items on one catalog page."""
    return [parse_catalog_item(it) for it in items]
