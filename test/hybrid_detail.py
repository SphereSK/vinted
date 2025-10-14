# hybrid_detail.py
import asyncio, time, random, requests
from vinted_api_kit import VintedApi, CatalogItem
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Referer": "https://www.vinted.fr/"}

def fetch_detail_requests(url):
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
        wait = 1.5 * (2 ** attempt) + random.uniform(0, 0.5)
        print(f"HTTP {r.status_code}; retrying in {wait:.1f}s")
        time.sleep(wait)
    return None


async def main():
    cookies_path = Path("./cookies")

    async with VintedApi(locale="fr", cookies_dir=cookies_path, persist_cookies=True) as v:
        items: list[CatalogItem] = await v.search_items(
            url="https://www.vinted.fr/catalog?search_text=adidas",
            per_page=3,
        )

        for it in items:
            print(f"🔹 {it.title} - {it.price} {it.currency}")
            html = fetch_detail_requests(it.url)
            if html:
                print(f"  ➜ detail len={len(html)} chars\n")
            else:
                print("  ⚠️ detail fetch failed\n")

if __name__ == "__main__":
    asyncio.run(main())
