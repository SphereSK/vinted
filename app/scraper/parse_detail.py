# app/scraper/parse_detail.py
from typing import Any, Dict, Optional, List
from bs4 import BeautifulSoup
import json
import re

def parse_detail_html(html: str) -> Dict[str, Any]:
    """
    Parse useful item details from raw HTML page.
    Returns a dict with keys: brand, size, condition, location, seller_name, photos, description, language.
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

    # Description
    data["description"] = text_or_none('[data-testid="item_description"], [class*="ItemDescription"], [itemprop="description"]')

    # Language (from meta or html tag)
    lang = soup.find("html", {"lang": True})
    data["language"] = lang.get("lang", None) if lang else None

    # Photos (from <img> or meta)
    imgs: List[str] = []
    for img in soup.select('img[data-testid="item-photo"], meta[property="og:image"], img[src]'):
        src = img.get("content") if img.name == "meta" else img.get("src")
        if src and src not in imgs:
            imgs.append(src)
    data["photos"] = imgs or None

    # Try to extract JSON inside <script> tags for shipping info
    json_data = None
    for script in soup.find_all("script", string=re.compile("window.__PRELOADED_STATE__")):
        try:
            match = re.search(r"window.__PRELOADED_STATE__\s*=\s*(\{.*?\});", script.string, re.S)
            if match:
                json_data = json.loads(match.group(1))
                break
        except Exception:
            continue

    if json_data:
        item_data = json_data.get("item", {})

        # Extract shipping price
        shipping = item_data.get("shipping_price", None)
        data["shipping_cents"] = int(float(shipping) * 100) if shipping else None

        # Extract location from user data in JSON
        user_data = item_data.get("user", {})
        if user_data:
            city = user_data.get("city")
            country = user_data.get("country_title") or user_data.get("country")
            if city and country:
                data["location"] = f"{city}, {country}"
            elif country:
                data["location"] = country
            elif city:
                data["location"] = city

    # Fallback: Extract shipping from visible HTML text if JSON not available
    if "shipping_cents" not in data or data["shipping_cents"] is None:
        shipping_elem = soup.select_one('[data-testid*="shipping"], [class*="shipping"]')
        if shipping_elem:
            shipping_text = shipping_elem.get_text(strip=True)
            # Look for patterns like "od 3,65 €" or "from 3.65 €"
            match = re.search(r'od\s+([\d,]+)\s*€', shipping_text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    data["shipping_cents"] = int(float(price_str) * 100)
                except (ValueError, TypeError):
                    pass

    return data
