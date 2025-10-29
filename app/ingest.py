import asyncio
import datetime as dt
import random
import os
import time
import requests
from typing import Optional
from app.scraper.browser import get_html_with_browser, init_driver
from vinted_api_kit import VintedApi
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.models import Listing, PriceHistory, ConditionOption, SourceOption, CategoryOption, PlatformOption
from app.db.session import Session, init_db
from app.scraper.parse_header import parse_catalog_page
from app.scraper.parse_detail import parse_detail_html
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from app.utils.language import detect_language_from_item
from app.scraper.session_warmup import warmup_vinted_session
from app.utils.retry import retry_with_backoff
from app.utils.clean import standardize_brand

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
from app.utils.title_corrector import correct_title_with_llm


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
async def get_or_create_condition_option(session, condition_name: str) -> Optional[int]:
    """Find a condition by name or create it if it doesn't exist."""
    if not condition_name:
        return None

    # Check if the condition option already exists
    res = await session.execute(
        select(ConditionOption).where(func.lower(ConditionOption.label) == func.lower(condition_name))
    )
    condition_option = res.scalar_one_or_none()

    if condition_option:
        return condition_option.id
    else:
        # Create a new one if it doesn't exist
        # Generate a URL-friendly code from the name
        code = condition_name.lower().replace(" ", "-").strip()
        new_option = ConditionOption(code=code, label=condition_name)
        session.add(new_option)
        await session.flush()  # Flush to get the new ID
        return new_option.id


async def get_or_create_category_option(session, category_name: str) -> Optional[int]:
    """Find a category by name or create it if it doesn't exist."""
    if not category_name:
        return None

    res = await session.execute(
        select(CategoryOption).where(func.lower(CategoryOption.name) == func.lower(category_name))
    )
    category_option = res.scalar_one_or_none()

    if category_option:
        return category_option.id
    else:
        new_option = CategoryOption(name=category_name)
        session.add(new_option)
        await session.flush()
        return new_option.id


async def get_or_create_platform_option(session, platform_name: str) -> Optional[int]:
    """Find a platform by name or create it if it doesn't exist."""
    if not platform_name:
        return None

    res = await session.execute(
        select(PlatformOption).where(func.lower(PlatformOption.name) == func.lower(platform_name))
    )
    platform_option = res.scalar_one_or_none()

    if platform_option:
        return platform_option.id
    else:
        new_option = PlatformOption(name=platform_name)
        session.add(new_option)
        await session.flush()
        return new_option.id


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
            "original_title": func.coalesce(Listing.original_title, stmt.excluded.title),
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
            "details_scraped": stmt.excluded.details_scraped,
            "last_seen_at": func.now(),
            # Mark as active if item is visible, inactive if not visible
            "is_active": stmt.excluded.is_visible,
            "is_visible": stmt.excluded.is_visible,
            # Auto-detect sold: if item was visible and now is not, likely sold
            # But preserve existing is_sold=True status (don't revert)
            "is_sold": func.coalesce(
                stmt.excluded.is_sold,  # From HTML if available
                Listing.is_sold,  # Keep existing sold status
                False  # Default to False
            ),
            "vinted_id": stmt.excluded.vinted_id,
            "condition_option_id": stmt.excluded.condition_option_id,
            "source_option_id": stmt.excluded.source_option_id,
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


async def mark_old_listings_inactive(session, logger, hours_threshold: int = 48):
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

    if result.rowcount > 0:
        logger.info(f"Marked {result.rowcount} listing(s) as non-active.", extra={"status": "non-active"})

    return result.rowcount


# -----------------------------------------------------
# Main Scraper Logic
# -----------------------------------------------------
async def search_items_with_retry(v: VintedApi, url: str, per_page: int):
    return await v.search_items(url=url, per_page=per_page)

@retry_with_backoff()
async def get_html_with_requests(url: str):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

async def get_html_with_retry(url: str, driver=None):
    return await get_html_with_browser(url, driver=driver)

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
    logger,
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
    base_url: str = None,
    details_strategy: str = "browser",
    details_concurrency: int = 2,
    use_llm_for_title_correction: bool = False,
):
    """Fetch catalog items from Vinted, enrich with HTML details, and store in DB.

    Args:
        error_wait_minutes: Minutes to wait when hitting 403/rate limit errors (default: 30)
        max_retries: Maximum number of retries per page on 403 errors (default: 3)
    """
    for locale in locales:
        logger.info(f"Scraping locale: {locale}")

        if base_url:
            current_base_url = base_url
        else:
            current_base_url = f"https://www.vinted.{locale}/catalog"

        start_url = build_catalog_url(
            base_url=current_base_url,
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
            details_strategy=details_strategy,
            details_concurrency=details_concurrency,
            logger=logger,
            use_llm_for_title_correction=use_llm_for_title_correction,
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
    details_strategy: str,
    details_concurrency: int,
    logger,
    use_llm_for_title_correction: bool = False,
):
    await init_db()

    # --- Config with env fallbacks ---
    strategy = details_strategy or os.getenv("DETAILS_STRATEGY", "browser")
    concurrency = details_concurrency or int(os.getenv("DETAILS_CONCURRENCY", 2))

    logger.info(f"Details strategy: {strategy}, Concurrency: {concurrency}")

    # --- Warm up session (direct connection only) ---
    logger.info("Warming up session with headers only...")
    try:
        warmup_vinted_session(locale=locale, use_proxy=use_proxy)
    except Exception as e:
        logger.warning(f"Warmup failed: {e}, continuing anyway...")

    # --- Start scraping session ---
    proxies = {"http": os.environ.get("HTTP_PROXY"), "https": os.environ.get("HTTPS_PROXY")} if use_proxy else None
    driver = None
    if fetch_details and strategy == "browser":
        try:
            driver = await init_driver()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return

    async with VintedApi(
        locale=locale,
        proxies=proxies,
        persist_cookies=True,
    ) as v, Session() as session:

        # Dynamically create retry functions with current parameters
        search_items_with_current_retry = retry_with_backoff(
            retries=max_retries,
            initial_delay=error_wait_minutes * 60 / 5, # Convert minutes to seconds, then divide for initial delay
            backoff_factor=2
        )(v.search_items)

        # --- Main scrape loop ---
        total = 0
        new_items = 0
        updated_items = 0
        start_time = time.time()
        page_times = []
        detail_metrics = {'success': 0, 'failed': 0, 'total_time': 0}
        scraped_successfully = False # Flag to track if any items were scraped successfully
        consecutive_empty_pages = 0 # Track pages with 0 new items
        max_consecutive_empty = 3 # Stop after 3 pages with no new items

        semaphore = asyncio.Semaphore(details_concurrency)

        async def fetch_details_with_semaphore(item_url):
            async with semaphore:
                if strategy == 'browser':
                    return await get_html_with_retry(item_url, driver=driver)
                else: # http
                    return await get_html_with_requests(item_url)

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
                logger.info(f"Page {page}/{max_pages} - {total} items, {elapsed_str} elapsed, ~{eta_str} remaining")
            else:
                logger.info(f"Page {page}/{max_pages}")

            items = None
            try:
                items = await search_items_with_current_retry(url=url, per_page=per_page, page=page)
            except Exception as e:
                logger.error(f"Failed to load page {page} after multiple retries: {e}")

            if not items:
                logger.warning("No items found on page, stopping.")
                break
            else:
                scraped_successfully = True # Mark as successful if at least one page returns items

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
                            if details_strategy == 'browser':
                                html = await fetch_details_with_semaphore(item["url"])
                                details = parse_detail_html(html)
                            else: # http
                                detail_item = await v.item_details(url=item["url"])
                                if detail_item:
                                    details = detail_item.dict()
                        except Exception as e:
                            logger.error(f"Error fetching details for {item['url']}: {e}")

                    # Capture original title
                    original_title = item.get("title", "")
                    item["title"] = original_title # Ensure the item's title remains original for now

                    condition_option_id = await get_or_create_condition_option(
                        session, item.get("condition")
                    )
                    # Assuming 'vinted' source has ID 1 in SourceOption table
                    source_option_id = 1 # Directly set source_option_id to 1

                    # Determine category_id
                    final_category_id = category_id
                    if not final_category_id and item.get("category"):
                        final_category_id = await get_or_create_category_option(session, item.get("category"))

                    # Determine platform_ids
                    final_platform_ids = platform_ids
                    if not final_platform_ids and item.get("platform_names"):
                        platform_names_from_item = item.get("platform_names", [])
                        platform_ids_from_item = []
                        for p_name in platform_names_from_item:
                            p_id = await get_or_create_platform_option(session, p_name)
                            if p_id: # Ensure ID is not None
                                platform_ids_from_item.append(p_id)
                        final_platform_ids = platform_ids_from_item

                    merged = {
                        **item,
                        **details,
                        "original_title": original_title, # Store original title
                        "price_cents": int(float(item["price"]) * 100)
                        if item.get("price")
                        else None,
                        "total_cents": int(float(item["price"]) * 100)
                        if item.get("price")
                        else None,
                        # "language": detected_lang, # Language detection moved to post-processing
                        "category_id": final_category_id,
                        "platform_ids": final_platform_ids,
                        "brand": standardize_brand(item.get("brand")),
                        "condition_option_id": condition_option_id,
                        "source_option_id": source_option_id,
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
                        logger.info(f"{item.get('title')} | {item.get('price')} {item.get('currency')}", extra={"status": "new"})
                    else:
                        updated_items += 1
                        page_updated_count += 1
                        logger.info(f"{item.get('title')} | {item.get('price')} {item.get('currency')}", extra={"status": "updated"})

                    total += 1
                    page_item_count += 1
                except Exception as e:
                    logger.error(f"DB error for {item.get('url')}: {e}")
                    await session.rollback()  # Reset transaction state to continue processing other items

                await asyncio.sleep(float(delay) + random.uniform(0, 0.5))

            # Track page timing
            page_elapsed = time.time() - page_start
            page_times.append(page_elapsed)
            logger.info(f"Page {page} complete: {page_item_count} items ({page_new_count} new, {page_updated_count} updated) in {page_elapsed:.1f}s")

            # Early exit if we hit consecutive pages with no new items
            if page_new_count == 0:
                consecutive_empty_pages += 1
                logger.info(f"No new items on page {page} ({consecutive_empty_pages}/{max_consecutive_empty} consecutive empty pages)")
                if consecutive_empty_pages >= max_consecutive_empty:
                    logger.info(f"Stopping early: {consecutive_empty_pages} consecutive pages with no new items")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter when we find new items

            await asyncio.sleep(delay)

    if driver:
        driver.quit()

    if scraped_successfully: # Only mark inactive if some items were scraped
        # Mark old listings as inactive (not seen in last 48 hours)
        logger.info("Marking old listings as inactive...")
        async with Session() as session:
            inactive_count = await mark_old_listings_inactive(session, logger, hours_threshold=48)
            if inactive_count > 0:
                logger.info(f"Marked {inactive_count} listing(s) as inactive (not seen in 48+ hours)")
            else:
                logger.info("All listings are up to date")

    # Get final database stats
    async with Session() as session:
        total_in_db = await session.scalar(
            select(func.count()).select_from(Listing).where(Listing.is_active == True)
        )

    total_time = time.time() - start_time
    logger.info("Scraping Complete!")
    logger.info(f"Time: {int(total_time // 60)}m {int(total_time % 60)}s")
    logger.info(f"Processed: {total} items")
    if total > 0:
        logger.info(f"New: {new_items} ({new_items/total*100:.1f}%)")
        logger.info(f"Updated: {updated_items} ({updated_items/total*100:.1f}%)")
    else:
        logger.info("New: 0 (0.0%)")
        logger.info("Updated: 0 (0.0%)")
    if detail_metrics['success'] > 0:
        avg_detail_time = detail_metrics['total_time'] / detail_metrics['success']
        logger.info(f"Fetched details for {detail_metrics['success']} items (avg: {avg_detail_time:.2f}s/item)")
    if detail_metrics['failed'] > 0:
        logger.warning(f"Failed to fetch details for {detail_metrics['failed']} items")
    logger.info(f"Total in DB: {total_in_db} active listings")
