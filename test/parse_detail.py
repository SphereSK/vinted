# app/scraper/parse_detail.py
from typing import Any, Dict, Optional, List
from bs4 import BeautifulSoup

def parse_detail_html(html: str) -> Dict[str, Any]:
    """
    Parse useful item details from raw HTML page.
    Returns a dict with keys: brand, size, condition,
    location, seller_name, photos.
    """
    soup = BeautifulSoup(html, "html.parser")
    data: Dict[str, Any] = {}

    def text_or_none(sel: str) -> Optional[str]:
        el = soup.select_one(sel)
        return el.get_text(strip=True) if el else None

    # Brand
    data["brand"] = text_or_none('[data-testid="brand_link"], a[href*="/brand/"]')

    # Size
    data["size"] = text_or_none('[data-testid="size"], [class*="size"]')

    # Condition
    data["condition"] = text_or_none('[data-testid="item_condition"], [class*="condition"]')

    # Location
    data["location"] = text_or_none('[data-testid="location"], [class*="item-location"]')

    # Seller name
    data["seller_name"] = text_or_none('[data-testid="user_link"], [class*="UserInfo"] a')

    # Photos (collect all image srcs from data-testid or og:image)
    imgs: List[str] = []
    for img in soup.select('img[data-testid="item-photo"], meta[property="og:image"]'):
        src = img.get("content") if img.name == "meta" else img.get("src")
        if src and src not in imgs:
            imgs.append(src)
    data["photos"] = imgs or None

    return data
