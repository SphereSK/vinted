import asyncio
import datetime as dt
import random
import requests
import time

from vinted_api_kit import VintedApi
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import Listing, PriceHistory
from app.db.session import Session, init_db
from app.scraper.parse_header import parse_catalog_page
from app.scraper.parse_detail import parse_detail_html
from app.utils.url import with_page
from app.utils.language import detect_language_from_item
from app.scraper.session_warmup import warmup_vinted_session


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


# -----------------------------------------------------
# Database Helpers
# -----------------------------------------------------
async def upsert_listing(session, data: dict):
    """Insert or update a listing based on URL (unique key)."""
    stmt = pg_insert(Listing).values(**data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["url"],
        set_={
            "title": stmt.excluded.title,
            "description": stmt.excluded.description,
            "language": stmt.excluded.language,
            "currency": stmt.excluded.currency,
            "price_cents": stmt.excluded.price_cents,
            "shipping_cents": stmt.excluded.shipping_cents,
            "total_cents": stmt.excluded.total_cents,
            "brand": stmt.excluded.brand,
            "size": stmt.excluded.size,
            "condition": stmt.excluded.condition,
            "location": stmt.excluded.location,
            "seller_id": stmt.excluded.seller_id,
            "seller_name": stmt.excluded.seller_name,
            "photo": stmt.excluded.photo,
            "photos": stmt.excluded.photos,
            "category_id": stmt.excluded.category_id,
            "platform_ids": stmt.excluded.platform_ids,
            "last_seen_at": func.now(),
            "is_active": True,
        },
    ).returning(Listing)
    res = await session.execute(stmt)
    return res.scalar_one()


async def insert_price_if_changed(session, listing_id, new_price_cents):
    """Insert a new PriceHistory record only if the price changed.

    Also checks that we haven't recorded the same price within the last 24 hours
    to avoid duplicate observations from the same scrape session.
    """
    # Get the most recent price observation
    result = await session.execute(
        select(PriceHistory.price_cents, PriceHistory.observed_at)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.observed_at.desc())
        .limit(1)
    )
    last_record = result.first()

    # Insert if:
    # 1. No previous record exists (first time seeing this listing)
    # 2. Price has changed from the last recorded price
    # 3. Last observation was more than 24 hours ago (daily price tracking)
    should_insert = False

    if last_record is None:
        # First time seeing this listing
        should_insert = True
    else:
        last_price, last_observed = last_record
        # Use timezone-aware datetime for comparison
        now = dt.datetime.now(dt.timezone.utc)
        time_diff = now - last_observed

        if last_price != new_price_cents:
            # Price changed
            should_insert = True
        elif time_diff.total_seconds() > 86400:  # 24 hours
            # Same price but last recorded more than 24 hours ago
            should_insert = True

    if should_insert and new_price_cents is not None:
        session.add(
            PriceHistory(
                listing_id=listing_id,
                observed_at=dt.datetime.now(dt.timezone.utc),
                price_cents=new_price_cents,
            )
        )


async def is_listing_new(session, url: str) -> bool:
    """Check if a listing already exists in the database."""
    result = await session.scalar(
        select(func.count()).select_from(Listing).where(Listing.url == url)
    )
    return result == 0


async def mark_old_listings_inactive(session, hours_threshold: int = 48):
    """
    Mark listings as inactive if they haven't been seen in the last N hours.

    This keeps historical data but marks items that are no longer available on Vinted.
    Sold, removed, or expired listings will be marked as is_active=False.

    Args:
        session: Database session
        hours_threshold: Number of hours since last_seen_at before marking inactive (default: 48)
    """
    from sqlalchemy import update

    # Use timezone-aware datetime to match database column (timezone=True)
    cutoff_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours_threshold)

    # Find items that haven't been seen recently and are still marked as active
    stmt = (
        update(Listing)
        .where(Listing.last_seen_at < cutoff_time)
        .where(Listing.is_active == True)
        .values(is_active=False)
    )

    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount


# -----------------------------------------------------
# Main Scraper Logic
# -----------------------------------------------------
async def scrape_and_store(
    start_url: str,
    max_pages: int = 5,
    per_page: int = 24,
    delay: float = 1.0,
    locale: str = "sk",
    fetch_details: bool = False,
    details_for_new_only: bool = False,
    use_proxy: bool = True,
    category_id: int = None,
    platform_ids: list = None,
):
    """Fetch catalog items from Vinted, enrich with HTML details, and store in DB."""
    await init_db()

    # --- Warm up session (direct connection only) ---
    print("🔄 Warming up session with headers only...")
    try:
        warmup_vinted_session(locale=locale, use_proxy=False)
    except Exception as e:
        print(f"⚠️  Warmup failed: {e}, continuing anyway...")

    # --- Start scraping session ---
    async with VintedApi(
        locale=locale,
        proxies=None,
        persist_cookies=True,
    ) as v, Session() as session:

        # --- Main scrape loop ---
        total = 0
        start_time = time.time()
        page_times = []

        for page in range(1, max_pages + 1):
            page_start = time.time()
            url = with_page(start_url, page)

            # Calculate progress and ETA
            if page > 1 and page_times:
                avg_page_time = sum(page_times) / len(page_times)
                remaining_pages = max_pages - page + 1
                eta_seconds = avg_page_time * remaining_pages
                eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                elapsed = time.time() - start_time
                elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
                print(f"\n=== Page {page}/{max_pages} === [{total} items, {elapsed_str} elapsed, ~{eta_str} remaining]")
            else:
                print(f"\n=== Page {page}/{max_pages} ===")

            try:
                items = await v.search_items(url=url, per_page=per_page)
            except Exception as e:
                print(f"  ! Failed to load page {page}: {e}")
                continue

            if not items:
                print(f"Page {page}: no items found, stopping.")
                break

            page_item_count = 0

            parsed_headers = parse_catalog_page(items)

            for item in parsed_headers:
                try:
                    fetch_item_details = False
                    if fetch_details or details_for_new_only:
                        if details_for_new_only:
                            is_new = await is_listing_new(session, item["url"])
                            fetch_item_details = is_new
                        else:
                            fetch_item_details = True

                    details = {}
                    if fetch_item_details:
                        try:
                            html = requests.get(item["url"], headers=HEADERS, timeout=30).text
                            details = parse_detail_html(html)
                        except Exception as e:
                            print(f"  ! Error fetching details for {item['url']}: {e}")

                    # Detect language from title and description
                    detected_lang = detect_language_from_item(
                        title=item.get("title", ""),
                        description=details.get("description") or item.get("description", "")
                    )

                    merged = {
                        **item,
                        **details,
                        "price_cents": int(float(item["price"]) * 100)
                        if item.get("price")
                        else None,
                        "total_cents": int(float(item["price"]) * 100)
                        if item.get("price")
                        else None,
                        "language": detected_lang,
                        "category_id": category_id,
                        "platform_ids": platform_ids,
                    }

                    valid_cols = {col.name for col in Listing.__table__.columns}
                    clean_data = {k: v for k, v in merged.items() if k in valid_cols}

                    listing = await upsert_listing(session, clean_data)
                    await insert_price_if_changed(session, listing.id, clean_data.get("price_cents"))
                    await session.commit()  # Commit after each item to prevent losing all items on error
                    print(f"- saved: {item.get('title')} | {item.get('price')} {item.get('currency')}")
                    total += 1
                    page_item_count += 1

                except Exception as e:
                    print(f"  ! DB error for {item.get('url')}: {e}")
                    await session.rollback()  # Reset transaction state to continue processing other items

                await asyncio.sleep(delay + random.uniform(0, 0.5))

            # Track page timing
            page_elapsed = time.time() - page_start
            page_times.append(page_elapsed)
            print(f"  ✓ Page {page} complete: {page_item_count} items in {page_elapsed:.1f}s")

            await asyncio.sleep(delay)

        # Mark old listings as inactive (not seen in last 48 hours)
        print("\n🔄 Marking old listings as inactive...")
        inactive_count = await mark_old_listings_inactive(session, hours_threshold=48)
        if inactive_count > 0:
            print(f"   Marked {inactive_count} listing(s) as inactive (not seen in 48+ hours)")
        else:
            print(f"   All listings are up to date")

        total_time = time.time() - start_time
        print(f"\n✅ Done. Processed {total} listings in {int(total_time // 60)}m {int(total_time % 60)}s")
