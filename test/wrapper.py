# wrapper.py
import asyncio
import random
from pathlib import Path

from vinted_api_kit import VintedApi, CatalogItem, DetailedItem
from curl_cffi.requests.exceptions import HTTPError  # for precise 403 catch

async def get_item_details_safe(v: VintedApi, url: str, *, tries: int = 4, base_delay: float = 1.2):
    """
    Try to fetch item details with exponential backoff + jitter.
    Returns DetailedItem or None on persistent 403/other errors.
    """
    for attempt in range(tries):
        try:
            return await v.item_details(url=url)
        except HTTPError as e:
            # If it's a 403, back off harder
            if getattr(e, "response", None) and e.response.status_code == 403:
                wait = base_delay * (2 ** attempt) + random.uniform(0.2, 0.6)
                print(f"[detail] 403 blocked; retrying in {wait:.1f}s (try {attempt+1}/{tries})")
                await asyncio.sleep(wait)
                continue
            # Other HTTP errors: brief wait + continue
            wait = 0.7 + random.uniform(0, 0.5)
            print(f"[detail] HTTP error {getattr(e, 'response', None)}; retrying in {wait:.1f}s")
            await asyncio.sleep(wait)
        except Exception as e:
            # Network/parse etc.
            wait = 0.7 + random.uniform(0, 0.5)
            print(f"[detail] error {e}; retrying in {wait:.1f}s")
            await asyncio.sleep(wait)
    return None

async def main():
    cookies_path = Path("./cookies")  # make sure this dir is writable

    async with VintedApi(
        locale="sk",               # match vinted.fr
        cookies_dir=cookies_path,  # must be a Path
        persist_cookies=True,      # reuse cookies across runs
    ) as vinted:

        # 1) Warm up cookies/session with a cheap catalog query
        print("warming up session…")
        warm_items: list[CatalogItem] = await vinted.search_items(
            url="https://www.vinted.sk/catalog?search_text=adidas",
            per_page=3,
        )
        await asyncio.sleep(1.0 + random.uniform(0, 0.5))  # small human-ish pause

        # 2) Try item details with backoff (will return None on persistent 403)
        item_url = "https://www.vinted.fr/items/922704975-adidas-x-15"
        detail: DetailedItem | None = await get_item_details_safe(vinted, item_url)

        if detail:
            print(f"📦 {detail.title}")
            print(f"💰 {detail.price}\n")
        else:
            print("⚠️ Could not fetch item details (403). Skipping details.\n")

        # 3) Do a search and print basic info (catalog is less restricted)
        items: list[CatalogItem] = await vinted.search_items(
            url="https://www.vinted.fr/catalog?search_text=adidas",
            per_page=5,
        )
        print("🔍 Search results:")
        for item in items:
            title = getattr(item, "title", None)
            price = getattr(item, "price", None)
            currency = getattr(item, "currency", None)
            print(f"  • {title} - {price} {currency}")

if __name__ == "__main__":
    asyncio.run(main())
