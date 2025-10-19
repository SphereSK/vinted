import asyncio
import datetime as dt
import random
from app.scraper.browser import get_html_with_browser
import time

from vinted_api_kit import VintedApi
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import Listing, PriceHistory
from app.db.session import Session, init_db
from app.scraper.parse_header import parse_catalog_page
from app.scraper.parse_detail import parse_detail_html
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

def build_catalog_url(base_url: str, search_text: str = None, category=None, platform_id=None, extra=None, order=None) -> str:
    """
    Construct a valid Vinted catalog URL with query parameters.
    Supports multiple categories and platform IDs.
    search_text is optional - can filter by category/platform only.
    Example output:
        https://www.vinted.sk/catalog?search_text=ps5&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first
    """
    params = {}
    if search_text:
        params["search_text"] = search_text

    if category:
        # Append multiple catalog[] params
        if isinstance(category, list):
            for i, c in enumerate(category):
                params[f"catalog[{i}]"] = c
        else:
            params["catalog[0]"] = category

    if platform_id:
        # Append multiple platform IDs
        if isinstance(platform_id, list):
            for i, p in enumerate(platform_id):
                params[f"video_game_platform_ids[{i}]"] = p
        else:
            params["video_game_platform_ids[0]"] = platform_id

    if order:
        params["order"] = order

    if extra:
        for e in extra:
            if "=" in e:
                k, v = e.split("=", 1)
                params[k] = v

    query_string = urlencode(params, doseq=True)
    return f"{base_url}?{query_string}"
from app.utils.language import detect_language_from_item
from app.scraper.session_warmup import warmup_vinted_session
from app.utils.retry import retry_with_backoff


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
    """Insert or update a listing based on URL (unique key).

    Returns:
        tuple: (listing, was_new) where was_new is True if inserted, False if updated
    """
    # Check if listing already exists by vinted_id (Vinted's unique identifier)
    vinted_id = data.get("vinted_id")
    if vinted_id:
        existing = await session.scalar(
            select(Listing.id).where(Listing.vinted_id == vinted_id)
        )
    else:
        # Fallback to URL if vinted_id not available
        existing = await session.scalar(
            select(Listing.id).where(Listing.url == data["url"])
        )
    was_new = existing is None  # True if doesn't exist = new insert

    # Perform upsert
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
            "source": stmt.excluded.source,
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
    listing = res.scalar_one()

    return listing, was_new


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
@retry_with_backoff(retries=5, initial_delay=5, backoff_factor=2)
async def search_items_with_retry(v: VintedApi, url: str, per_page: int):
    return await v.search_items(url=url, per_page=per_page)

@retry_with_backoff(retries=3, initial_delay=2, backoff_factor=2)
async def get_html_with_retry(url: str):
    return get_html_with_browser(url)

def with_page(url: str, page: int) -> str:
    """
    Append or replace the 'page' query parameter in a given URL.
    """
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    q["page"] = [str(page)]
    new_query = urlencode(q, doseq=True)
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url


async def scrape_and_store(
    search_text: str,
    max_pages: int = 5,
    per_page: int = 24,
    delay: float = 1.0,
    locales: list[str] = ["sk"],
    fetch_details: bool = False,
    details_for_new_only: bool = False,
    use_proxy: bool = True,
    category_id: int = None,
    platform_ids: list = None,
    error_wait_minutes: int = 30,
    max_retries: int = 3,
    extra: list[str] = None,
    order: str = None,
):
    """Fetch catalog items from Vinted, enrich with HTML details, and store in DB.

    Args:
        error_wait_minutes: Minutes to wait when hitting 403/rate limit errors (default: 30)
        max_retries: Maximum number of retries per page on 403 errors (default: 3)
    """
    for locale in locales:
        print(f"\n\n{'='*60}")
        print(f"Scraping locale: {locale}")
        print(f"{'='*60}")

        base_url = f"https://www.vinted.{locale}/catalog"
        start_url = build_catalog_url(
            base_url=base_url,
            search_text=search_text,
            category=category_id,
            platform_id=platform_ids,
            extra=extra,
            order=order,
        )

        await _scrape_and_store_locale(
            start_url=start_url,
            max_pages=max_pages,
            per_page=per_page,
            delay=delay,
            locale=locale,
            fetch_details=fetch_details,
            details_for_new_only=details_for_new_only,
            use_proxy=use_proxy,
            category_id=category_id,
            platform_ids=platform_ids,
            error_wait_minutes=error_wait_minutes,
            max_retries=max_retries,
        )

async def _scrape_and_store_locale(
    start_url: str,
    max_pages: int,
    per_page: int,
    delay: float,
    locale: str,
    fetch_details: bool,
    details_for_new_only: bool,
    use_proxy: bool,
    category_id: int,
    platform_ids: list,
    error_wait_minutes: int,
    max_retries: int,
):
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
        new_items = 0
        updated_items = 0
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
                print(f"\n=== Page {page}/{max_pages} === ")

            items = None
            try:
                items = await search_items_with_retry(v, url=url, per_page=per_page)
            except Exception as e:
                print(f"  ! Failed to load page {page} after multiple retries: {e}")

            if not items:
                print(f"Page {page}: no items found, stopping.")
                break

            page_item_count = 0
            page_new_count = 0
            page_updated_count = 0

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
                            html = await get_html_with_retry(item["url"])
                            details = parse_detail_html(html)
                        except Exception as e:
                            print(f"  ! Error fetching details for {item['url']}: {e}")

                    # Detect language from title and description
                    detected_lang = detect_language_from_item(
                        title=item.get("title", ""),
                        description=details.get("description") or item.get("description", "")
                    )

from app.utils.clean import standardize_brand

# ... (rest of the file)

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
                        "source": "vinted",
                        "category_id": category_id,
                        "platform_ids": platform_ids,
                        "brand": standardize_brand(item.get("brand")),
                    }

                    valid_cols = {col.name for col in Listing.__table__.columns}
                    clean_data = {k: v for k, v in merged.items() if k in valid_cols}

                    listing, was_new = await upsert_listing(session, clean_data)
                    await insert_price_if_changed(session, listing.id, clean_data.get("price_cents"))
                    await session.commit()  # Commit after each item to prevent losing all items on error

                    # Track statistics
                    if was_new:
                        new_items += 1
                        page_new_count += 1
                        status_icon = "✨"
                    else:
                        updated_items += 1
                        page_updated_count += 1
                        status_icon = "🔄"

                    print(f"{status_icon} {item.get('title')} | {item.get('price')} {item.get('currency')}")
                    total += 1
                    page_item_count += 1

                except Exception as e:
                    print(f"  ! DB error for {item.get('url')}: {e}")
                    await session.rollback()  # Reset transaction state to continue processing other items

                await asyncio.sleep(delay + random.uniform(0, 0.5))

            # Track page timing
            page_elapsed = time.time() - page_start
            page_times.append(page_elapsed)
            print(f"  ✓ Page {page} complete: {page_item_count} items ({page_new_count} new, {page_updated_count} updated) in {page_elapsed:.1f}s")

            await asyncio.sleep(delay)

        # Mark old listings as inactive (not seen in last 48 hours)
        print("\n🔄 Marking old listings as inactive...")
        inactive_count = await mark_old_listings_inactive(session, hours_threshold=48)
        if inactive_count > 0:
            print(f"   Marked {inactive_count} listing(s) as inactive (not seen in 48+ hours)")
        else:
            print(f"   All listings are up to date")

        # Get final database stats
        total_in_db = await session.scalar(
            select(func.count()).select_from(Listing).where(Listing.is_active == True)
        )

        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Scraping Complete!")
        print(f"{ '='*60}")
        print(f"⏱️  Time: {int(total_time // 60)}m {int(total_time % 60)}s")
        print(f"📊 Processed: {total} items")
        print(f"   ✨ New: {new_items} ({new_items/total*100:.1f}%)\n")
        print(f"   🔄 Updated: {updated_items} ({updated_items/total*100:.1f}%)\n")
        print(f"💾 Total in DB: {total_in_db} active listings")
        print(f"{ '='*60}")