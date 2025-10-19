# app/postprocess.py
import asyncio
import requests
import time
import random
from sqlalchemy import select, update
from app.db.models import Listing
from app.db.session import Session, init_db
from app.scraper.parse_detail import parse_detail_html
from app.utils.language import detect_language_from_item


# -----------------------------------------------------
# HTTP Settings
# -----------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def process_language_detection(
    limit: int = None,
    delay: float = 1.5,
    source: str = None,
):
    """
    Post-process existing listings to detect language.

    Fetches HTML for listings without language data and extracts language info.
    This is separate from the main scraping flow for better performance.

    Args:
        limit: Maximum number of listings to process (None = all)
        delay: Delay between requests in seconds (default: 1.5)
        source: Filter by source (e.g., 'vinted', 'bazos')
    """
    await init_db()

    async with Session() as session:
        # Find listings without language
        query = select(Listing).where(
            Listing.language.is_(None),
            Listing.is_active == True
        )

        if source:
            query = query.where(Listing.source == source)

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        listings = result.scalars().all()

        if not listings:
            print("✅ No listings need language detection")
            return

        total = len(listings)
        print(f"📝 Processing {total} listing(s) for language detection...")

        processed = 0
        errors = 0
        start_time = time.time()

        for idx, listing in enumerate(listings, 1):
            try:
                # Calculate ETA
                if idx > 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx - 1)
                    remaining = total - idx + 1
                    eta_seconds = avg_time * remaining
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                    print(f"\n[{idx}/{total}] ~{eta_str} remaining")
                else:
                    print(f"\n[{idx}/{total}]")

                print(f"  Fetching: {listing.url}")

                # Fetch HTML
                response = requests.get(
                    listing.url,
                    headers=HEADERS,
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"  ⚠️  HTTP {response.status_code}, skipping")
                    errors += 1
                    continue

                # Parse HTML for details
                details = parse_detail_html(response.text)

                # Detect language
                detected_lang = detect_language_from_item(
                    title=listing.title or "",
                    description=details.get("description") or listing.description or ""
                )

                # Update listing
                if detected_lang:
                    stmt = (
                        update(Listing)
                        .where(Listing.id == listing.id)
                        .values(
                            language=detected_lang,
                            description=details.get("description") or listing.description
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

                    print(f"  ✓ Language: {detected_lang}")
                    processed += 1
                else:
                    print(f"  ⚠️  Could not detect language")
                    errors += 1

                # Delay between requests
                await asyncio.sleep(delay + random.uniform(0, 0.5))

            except Exception as e:
                print(f"  ❌ Error: {e}")
                errors += 1
                await session.rollback()
                continue

        elapsed = time.time() - start_time
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        print(f"\n{'='*60}")
        print(f"✅ Completed in {elapsed_str}")
        print(f"   Processed: {processed}")
        print(f"   Errors: {errors}")
        print(f"   Total: {total}")
        print(f"{'='*60}")
