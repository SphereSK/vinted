import asyncio
from datetime import datetime, timezone
from typing import Optional

import sentry_sdk
import typer
from sqlalchemy import func, select

from app.db.models import Listing, ScrapeConfig
from app.db.session import Session, init_db
from app.ingest import scrape_and_store
from app.postprocess import process_language_detection, process_title_correction
from app.utils.url import build_catalog_url
from app.utils.categories import (
    list_common_categories,
    search_categories,
    list_video_game_platforms,
    search_platforms
)
from app.utils.logging import get_logger
from fastAPI.redis import set_config_status
from app.scrapy_worker.runner import run_detail_spider
import os

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


async def run_scrape_job(
    *,
    search_text: str,
    max_pages: int,
    per_page: int,
    delay: float,
    locales: list[str],
    fetch_details: bool,
    details_for_new_only: bool,
    use_proxy: bool,
    category_id: Optional[int],
    platform_ids: Optional[list[int]],
    error_wait_minutes: int,
    max_retries: int,
    extra: Optional[list[str]],
    order: Optional[str],
    base_url: Optional[str],
    details_strategy: str,
    details_concurrency: int,
    config_id: Optional[int] = None,
) -> None:
    """Execute the scrape and update status metadata when launched by a scheduled config."""

    logger = get_logger(__name__)

    await init_db()

    count_before = 0
    config_exists = False
    error_message: Optional[str] = None

    if config_id is not None:
        async with Session() as session:
            config = await session.get(ScrapeConfig, config_id)
            if config:
                config_exists = True
                config.last_run_status = "running"
                config.last_run_at = datetime.now(tz=timezone.utc)
                config.last_run_items = None
                await session.commit()

        if config_exists:
            await set_config_status(
                config_id,
                "running",
                message="Scrape in progress",
            )

            async with Session() as session:
                result = await session.execute(select(func.count()).select_from(Listing))
                count_before = int(result.scalar() or 0)

    try:
        await scrape_and_store(
            search_text=search_text,
            max_pages=max_pages,
            per_page=per_page,
            delay=delay,
            locales=locales,
            fetch_details=fetch_details,
            details_for_new_only=details_for_new_only,
            use_proxy=use_proxy,
            category_id=category_id,
            platform_ids=platform_ids,
            error_wait_minutes=error_wait_minutes,
            max_retries=max_retries,
            extra=extra,
            order=order,
            base_url=base_url,
            details_strategy=details_strategy,
            details_concurrency=details_concurrency,
            logger=logger,
        )
        success = True
    except Exception as exc:
        error_message = str(exc)
        logger.error(f"Scrape failed: {error_message}")
        success = False
    finally:
        if config_id is not None and config_exists:
            async with Session() as session:
                config = await session.get(ScrapeConfig, config_id)
                if config:
                    config.last_run_at = datetime.now(tz=timezone.utc)

                    if success:
                        result = await session.execute(select(func.count()).select_from(Listing))
                        count_after = int(result.scalar() or 0)
                        new_items = max(count_after - count_before, 0)
                        config.last_run_status = "success"
                        config.last_run_items = new_items
                        await session.commit()

                        await set_config_status(
                            config_id,
                            "success",
                            message=f"Scrape completed successfully ({new_items} new items)",
                            extra={"items": new_items},
                        )
                    else:
                        config.last_run_status = "failed"
                        config.last_run_items = None
                        await session.commit()

                        await set_config_status(
                            config_id,
                            "failed",
                            message=f"Scrape failed: {error_message}",
                        )

        if not success:
            raise

app = typer.Typer(
    help="""🛒 Vinted Scraper - Track prices and listings from Vinted marketplace

╔══════════════════════════════════════════════════════════════════════╗
║                          QUICK START                                  ║
╚══════════════════════════════════════════════════════════════════════╝

# Fast scraping (catalog only, ~24 items/min)
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --no-proxy --max-pages 10

# Without search text (filter by category/platform only)
vinted-scraper scrape -c 3026 -p 1281 --no-proxy --max-pages 10

# With newest first sorting
vinted-scraper scrape -c 3026 -p 1281 --order newest_first --no-proxy --max-pages 10

# With descriptions for English filtering (~10 items/min)
vinted-scraper scrape --search-text "nintendo" -c 3026 --fetch-details --details-for-new-only --no-proxy --max-pages 5

╔══════════════════════════════════════════════════════════════════════╗
║                      ALL SCRAPE OPTIONS                               ║
╚══════════════════════════════════════════════════════════════════════╝

SEARCH & FILTERING (at least one required):
  --search-text TEXT          Search query (e.g., "ps5", "iphone", "macbook")
                              Optional when using -c or -p filters

  -c, --category INTEGER      Category ID to filter by (repeatable)
                              Example: -c 3026 (Video Games)
                              Use: vinted-scraper categories

  -p, --platform-id INTEGER   Video game platform ID (repeatable)
                              Example: -p 1281 (PS5), -p 1280 (PS4)
                              Use: vinted-scraper platforms

  --order TEXT                Sort order for listings
                              Options: newest_first, price_low_to_high, price_high_to_low
                              Example: --order newest_first

  -e, --extra TEXT            Extra query parameters as key=value
                              Example: -e "price_to=100"

SCRAPING CONTROL:
  --max-pages INTEGER         Number of pages to scrape
                              [default: 5] (24 items per page)
                              Note: Pages may contain duplicate items

  --per-page INTEGER          Items per page (Vinted's maximum is 24)
                              [default: 24]

  --delay FLOAT               Delay in seconds between page requests
                              [default: 1.0] (minimum: 0.5)
                              Increase if you hit rate limits

  --no-proxy                  Skip proxy and connect directly (RECOMMENDED)
                              Faster and more reliable than free proxies
                              Use this flag for production!

ERROR HANDLING & RETRIES:
  --error-wait INTEGER        Minutes to wait when hitting 403/rate limits
                              [default: 30] Automatically retries after waiting

  --max-retries INTEGER       Maximum retry attempts per page on 403 errors
                              [default: 3] Skips page after max retries

DETAIL FETCHING (HTML scraping):
  --fetch-details             Fetch full HTML details for ALL items
                              Gets: description, language, photos, shipping
                              WARNING: 3x slower (~10 items/min vs 24)

  --details-for-new-only      Fetch details ONLY for new listings
                              Fast for re-scrapes, recommended!
                              Automatically enables --fetch-details

REGION OPTIONS:
  --base-url TEXT             Base Vinted catalog URL for different regions
                              [default: https://www.vinted.sk/catalog]
                              Examples:
                                https://www.vinted.com/catalog (US)
                                https://www.vinted.fr/catalog (France)
                                https://www.vinted.pl/catalog (Poland)

  --locale TEXT               Locale code for API requests
                              [default: sk]
                              Examples: en, fr, de, pl, es, it

╔══════════════════════════════════════════════════════════════════════╗
║                    WHAT DATA IS CAPTURED                              ║
╚══════════════════════════════════════════════════════════════════════╝

WITHOUT --fetch-details (FAST ~24 items/min):
  ✓ Title, price, currency
  ✓ Seller name and ID
  ✓ Brand, condition
  ✓ Category ID, platform IDs
  ✓ First photo URL
  ✓ First/last seen timestamps

WITH --fetch-details (SLOW ~10 items/min):
  ✓ Full description
  ✓ Language code (en, sk, fr, etc.)
  ✓ All photo URLs (array)
  ✓ Shipping costs

NOT AVAILABLE:
  ✗ Location (requires browser automation)

╔══════════════════════════════════════════════════════════════════════╗
║                           COMMANDS                                    ║
╚══════════════════════════════════════════════════════════════════════╝

scrape           - Scrape listings and save to database
detect-language  - Post-process listings to detect language (separate step)
categories       - List available category IDs (with --search to filter)
platforms        - List video game platform IDs (with --search to filter)
examples         - Show detailed usage examples (30+ examples)

╔══════════════════════════════════════════════════════════════════════╗
║                        WEB DASHBOARD                                  ║
╚══════════════════════════════════════════════════════════════════════╝

Start: python3 -m app.api.main
Visit: http://localhost:8000

Features:
  • View listings in grid/table view
  • Track price changes with ↑↓ arrows
  • Create scrape configurations
  • Schedule automated scraping with cron
  • View price history charts

╔══════════════════════════════════════════════════════════════════════╗
║                         MORE HELP                                     ║
╚══════════════════════════════════════════════════════════════════════╝

Detailed command help:
  vinted-scraper scrape --help
  vinted-scraper categories --help
  vinted-scraper platforms --help

Show 30+ examples:
  vinted-scraper examples

Documentation:
  📚 CLAUDE.md - Complete project docs
  📊 DATA_FIELDS_GUIDE.md - Field availability
  🔄 SCRAPER_BEHAVIOR.md - How duplicates work
"""
)

@app.command()
def scrape(
    search_text: str = typer.Option(
        None,
        help="🔍 Search query (e.g., 'ps5', 'iphone', 'macbook'). "
             "Optional when using -c or -p filters"
    ),
    category: list[int] = typer.Option(
        None,
        "-c",
        help="📂 Category ID(s) to filter by (repeatable). "
             "Example: -c 3026 for Video Games. "
             "List all: vinted-scraper categories"
    ),
    platform_id: list[int] = typer.Option(
        None,
        "-p",
        help="🎮 Video game platform ID(s) (repeatable). "
             "Example: -p 1281 (PS5), -p 1280 (PS4). "
             "List all: vinted-scraper platforms"
    ),
    extra: list[str] = typer.Option(
        None,
        "-e",
        help="➕ Extra query parameters as key=value pairs. "
             "Example: -e 'price_to=100'"
    ),
    order: str = typer.Option(
        None,
        "--order",
        help="📅 Sort order for listings. "
             "Options: 'newest_first', 'price_low_to_high', 'price_high_to_low'. "
             "Example: --order newest_first"
    ),
    max_pages: int = typer.Option(
        5,
        help="📄 Number of pages to scrape [default: 5] (24 items/page). "
             "Note: Pages may contain duplicates, so 5 pages ≠ 120 unique items"
    ),
    per_page: int = typer.Option(
        24,
        help="📊 Items per page [default: 24] (Vinted's maximum is 24)"
    ),
    delay: float = typer.Option(
        1.0,
        help="⏱️  Delay in seconds between requests [default: 1.0] (min: 0.5). "
             "Increase if you hit rate limits"
    ),

    locales: list[str] = typer.Option(
        ["sk"],
        "--locale",
        help="🗣️  Locale code(s) to scrape (repeatable). "
             "Examples: --locale sk --locale cz"
    ),
    fetch_details: bool = typer.Option(
        False,
        "--fetch-details",
        help="📝 Fetch HTML details for ALL items (description, language, photos). "
             "⚠️  WARNING: 3x slower (~10 items/min vs 24). "
             "Gets: description, language, photos, shipping"
    ),
    details_for_new_only: bool = typer.Option(
        False,
        "--details-for-new-only",
        help="📝 Fetch details ONLY for new listings (recommended for re-scrapes). "
             "Faster than --fetch-details. Auto-enables HTML fetching for new items"
    ),
    no_proxy: bool = typer.Option(
        False,
        "--no-proxy",
        help="⚡ Skip proxy and connect directly [RECOMMENDED]. "
             "Faster and more reliable. Use this in production!"
    ),
    error_wait_minutes: int = typer.Option(
        30,
        "--error-wait",
        help="⏰ Minutes to wait when hitting 403/rate limit errors [default: 30]. "
             "System will automatically retry after waiting"
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        help="🔄 Maximum retry attempts per page on 403 errors [default: 3]. "
             "After max retries, page will be skipped"
    ),
    base_url: str = typer.Option(
        None,
        "--base-url",
        help="🌐 Base Vinted catalog URL for different regions. "
             "Example: https://www.vinted.com/catalog (US)"
    ),
    details_strategy: str = typer.Option(
        "browser",
        "--details-strategy",
        help="⚙️ Strategy for fetching details. 'browser' (default) or 'http'."
    ),
    details_concurrency: int = typer.Option(
        2,
        "--details-concurrency",
        help="⚙️ Concurrency for fetching details [default: 2]."
    ),
    config_id: Optional[int] = typer.Option(
        None,
        "--config-id",
        help="Internal: scrape config identifier used by scheduled runs.",
        hidden=True,
    ),
):
    """
    🔍 Scrape Vinted listings and save to database with price tracking.

    ═══════════════════════════════════════════════════════════════
    📊 DATA CAPTURED (always, ~24 items/min):
    ═══════════════════════════════════════════════════════════════
      ✓ Title, price, currency
      ✓ Seller name and ID
      ✓ Brand, condition
      ✓ Category ID, platform IDs
      ✓ First photo URL
      ✓ First/last seen timestamps

    ═══════════════════════════════════════════════════════════════
    📝 EXTRA DATA (with --fetch-details, ~10 items/min):
    ═══════════════════════════════════════════════════════════════
      ✓ Full description
      ✓ Language code (en, sk, fr, etc.)
      ✓ All photo URLs (array)
      ✓ Shipping costs

    ═══════════════════════════════════════════════════════════════
    ⚠️  NOT AVAILABLE:
    ═══════════════════════════════════════════════════════════════
      ✗ Location (requires browser automation)

    ═══════════════════════════════════════════════════════════════
    💡 QUICK EXAMPLES:
    ═══════════════════════════════════════════════════════════════

    # Fast scraping (catalog only)
    vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --no-proxy --max-pages 10

    # With descriptions for English filtering
    vinted-scraper scrape --search-text "nintendo" -c 3026 \\
        --fetch-details --details-for-new-only --no-proxy --max-pages 5

    # Multiple platforms
    vinted-scraper scrape --search-text "playstation" -c 3026 \\
        -p 1281 -p 1280 -p 1279 --no-proxy --max-pages 20

    # With price filtering
    vinted-scraper scrape --search-text "ps5" -c 3026 \\
        -e "price_to=100" --no-proxy --max-pages 5

    ═══════════════════════════════════════════════════════════════
    View results: http://localhost:8000
    More examples: vinted-scraper examples
    ═══════════════════════════════════════════════════════════════
    """

    logger = get_logger(__name__)

    # Validate that either search_text OR category/platform is provided
    if not search_text and not category and not platform_id:
        logger.error("You must provide at least one of: --search-text, -c/--category, or -p/--platform-id")
        raise typer.Exit(code=1)

    # Automatically imply fetch_details when --details-for-new-only is set
    if details_for_new_only:
        fetch_details = True

    asyncio.run(
        run_scrape_job(
            search_text=search_text,
            max_pages=max_pages,
            per_page=per_page,
            delay=delay,
            locales=list(locales),
            fetch_details=fetch_details,
            details_for_new_only=details_for_new_only,
            use_proxy=not no_proxy,
            category_id=category[0] if category else None,
            platform_ids=list(platform_id) if platform_id else None,
            error_wait_minutes=error_wait_minutes,
            max_retries=max_retries,
            extra=list(extra) if extra else None,
            order=order,
            base_url=base_url,
            details_strategy=details_strategy,
            details_concurrency=details_concurrency,
            config_id=config_id,
        )
    )


@app.command()
def categories(
    search: str = typer.Option(None, "--search", "-s", help="Search for categories by name"),
):
    """
    List available Vinted categories with their IDs.
    """
    logger = get_logger(__name__)
    if search:
        results = search_categories(search)
        if results:
            logger.info(f"\n📂 Categories matching '{search}':\n")
            for cat_id, name in results.items():
                logger.info(f"  {cat_id:6} - {name}")
        else:
            logger.warning(f"❌ No categories found matching '{search}'")
    else:
        all_cats = list_common_categories()
        logger.info("\n📂 Common Vinted Categories:\n")
        logger.info("Electronics & Gaming:")
        for cat_id in [2994, 3026, 1953]:
            logger.info(f"  {cat_id:6} - {all_cats[cat_id]}")

        logger.info("\nFashion:")
        for cat_id in [16, 18, 12]:
            logger.info(f"  {cat_id:6} - {all_cats[cat_id]}")

        logger.info("\nHome & Lifestyle:")
        for cat_id in [1243, 5]:
            logger.info(f"  {cat_id:6} - {all_cats[cat_id]}")

        logger.info("\n💡 Use -c <ID> to filter by category in scrape command")
        logger.info("   Example: vinted-scraper scrape --search-text 'ps5' -c 3026\n")


@app.command()
def platforms(
    search: str = typer.Option(None, "--search", "-s", help="Search for platforms by name"),
):
    """
    List available video game platform IDs.
    """
    logger = get_logger(__name__)
    if search:
        results = search_platforms(search)
        if results:
            logger.info(f"\n🎮 Platforms matching '{search}':\n")
            for plat_id, name in results.items():
                logger.info(f"  {plat_id:6} - {name}")
        else:
            logger.warning(f"❌ No platforms found matching '{search}'")
    else:
        all_plats = list_video_game_platforms()
        logger.info("\n🎮 Video Game Platforms:\n")

        logger.info("PlayStation:")
        for plat_id in [1281, 1280, 1279, 1278, 1277, 1286, 1287]:
            logger.info(f"  {plat_id:6} - {all_plats[plat_id]}")

        logger.info("\nXbox:")
        for plat_id in [1282, 1283, 1284, 1285]:
            logger.info(f"  {plat_id:6} - {all_plats[plat_id]}")

        logger.info("\nNintendo:")
        for plat_id in [1288, 1289, 1290, 1291, 1292, 1293, 1294, 1295]:
            logger.info(f"  {plat_id:6} - {all_plats[plat_id]}")

        logger.info("\nOther:")
        for plat_id in [1296, 1297]:
            logger.info(f"  {plat_id:6} - {all_plats[plat_id]}")

        logger.info("\n💡 Use -p <ID> to filter by platform in scrape command")
        logger.info("   Example: vinted-scraper scrape --search-text 'ps5' -c 3026 -p 1281 -p 1280")
        logger.info("   (Filters for PS5 and PS4 games)\n")


@app.command()
def detect_language_postprocess(
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of listings to process (default: all)"
    ),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help="Filter by source (e.g., 'vinted', 'bazos')"
    ),
):
    """
    🌐 Post-process listings to detect language from HTML.

    This command fetches HTML for listings that don't have language data
    and extracts the language information. It's separate from the main
    scraping flow for better performance.

    ═══════════════════════════════════════════════════════════════
    💡 WHEN TO USE:
    ═══════════════════════════════════════════════════════════════

    1. After fast scraping without --fetch-details
    2. To fill in missing language data
    3. To avoid slowing down the main scraping flow

    ═══════════════════════════════════════════════════════════════
    📊 EXAMPLES:
    ═══════════════════════════════════════════════════════════════

    # Process all listings without language
    vinted-scraper detect-language

    # Process only 10 listings (for testing)
    vinted-scraper detect-language --limit 10

    # Process only Vinted listings
    vinted-scraper detect-language --source vinted

    # Slower scraping to avoid rate limits
    vinted-scraper detect-language --delay 2.0

    ═══════════════════════════════════════════════════════════════
    """
    logger = get_logger(__name__)
    asyncio.run(
        process_language_detection(
            limit=limit,
            source=source,
            logger=logger,
        )
    )


@app.command()
def correct_titles_postprocess(
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of listings to process (default: all)"
    ),
    delay: float = typer.Option(
        1.5,
        "--delay",
        help="Delay between requests in seconds [default: 1.5]"
    ),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help="Filter by source (e.g., 'vinted', 'bazos')"
    ),
):
    """
    📝 Post-process listings to correct and standardize titles using LLM.

    This command applies LLM-based title correction to listings that
    have not yet been corrected. It's separate from the main scraping
    flow for better performance and control.

    ═══════════════════════════════════════════════════════════════
    💡 WHEN TO USE:
    ═══════════════════════════════════════════════════════════════

    1. After scraping to standardize titles (e.g., translate to English).
    2. To correct typos and inconsistencies in titles.
    3. To avoid slowing down the main scraping flow.

    ═══════════════════════════════════════════════════════════════
    📊 EXAMPLES:
    ═══════════════════════════════════════════════════════════════

    # Process all listings needing title correction
    vinted-scraper correct-titles-postprocess

    # Process only 10 listings (for testing)
    vinted-scraper correct-titles-postprocess --limit 10

    # Process only Vinted listings
    vinted-scraper correct-titles-postprocess --source vinted

    # Slower processing to avoid rate limits on LLM API
    vinted-scraper correct-titles-postprocess --delay 2.0

    ═══════════════════════════════════════════════════════════════
    """
    logger = get_logger(__name__)
    asyncio.run(
        process_title_correction(
            limit=limit,
            delay=delay,
            source=source,
            logger=logger,
        )
    )


@app.command("scrape-details")
def scrape_details(
    batch_size: int = typer.Option(100, help="Number of listings to process."),
    source: Optional[str] = typer.Option(None, help="Filter listings by source code."),
    limit: Optional[int] = typer.Option(
        None, help="Maximum listings to crawl (defaults to batch_size)."
    ),
    locale: str = typer.Option("sk", help="Locale used for warmup requests."),
    warmup: bool = typer.Option(True, help="Warm up Vinted session before crawling."),
    download_delay: Optional[float] = typer.Option(
        None,
        min=0,
        help="Override Scrapy download delay (seconds).",
    ),
    concurrent_requests: Optional[int] = typer.Option(
        None,
        min=1,
        help="Override Scrapy concurrent requests.",
    ),
    log_level: Optional[str] = typer.Option(
        None,
        help="Scrapy log level override (e.g., DEBUG, INFO).",
    ),
) -> None:
    """Run the Scrapy detail worker to backfill missing listing fields."""

    run_detail_spider(
        batch_size=batch_size,
        source=source,
        limit=limit,
        locale=locale,
        warmup=warmup,
        download_delay=download_delay,
        concurrent_requests=concurrent_requests,
        log_level=log_level,
    )


@app.command("verify-status")
def verify_status(
    batch_size: int = typer.Option(
        100,
        "--batch-size",
        "-b",
        help="Number of items to verify (default: 100)"
    ),
    hours: int = typer.Option(
        24,
        "--hours",
        "-h",
        help="Check items not seen in this many hours (default: 24)"
    ),
    delay: float = typer.Option(
        2.0,
        "--delay",
        "-d",
        help="Delay between requests in seconds (default: 2.0)"
    ),
    check_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Check ALL items (active and inactive), not just active ones"
    ),
):
    """
    🔍 Verify status of tracked items (sold/removed/still available).

    Checks items not seen recently by fetching detail pages and updating
    is_visible, is_active, is_sold. Run daily to catch sold items.

    EXAMPLES:

        vinted-scraper verify-status              # 100 items, 24h (default)
        vinted-scraper verify-status --all        # Check inactive items too
        vinted-scraper verify-status -b 50 -h 12  # 50 items, 12 hours
        vinted-scraper verify-status -d 3.0       # Slower (avoid 403)

    PERFORMANCE: ~2-3 sec/item | 100 items = ~5-8 min
    """
    from app.verify_status import verify_tracked_items

    logger = get_logger(__name__)
    asyncio.run(
        verify_tracked_items(
            batch_size=batch_size,
            hours_since_last_seen=hours,
            delay=delay,
            check_all=check_all,
            logger=logger,
        )
    )


@app.command()
def examples():
    """
    Show detailed usage examples with all common flag combinations.
    """
    typer.echo("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         VINTED SCRAPER EXAMPLES                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1. BASIC SCRAPING (Fastest - ~24 items/min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Search for PS5 games, 10 pages
vinted-scraper scrape --search-text "ps5" --no-proxy --max-pages 10

# Search in specific category (Video Games = 3026)
vinted-scraper scrape --search-text "ps5" -c 3026 --no-proxy --max-pages 10

# Multiple categories (Electronics + Video Games)
vinted-scraper scrape --search-text "console" -c 2994 -c 3026 --no-proxy --max-pages 5

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 2. PLATFORM FILTERING (Video Games)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PS5 games only
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 --no-proxy --max-pages 10

# PS5 games without search text (all PS5 games in category)
vinted-scraper scrape -c 3026 -p 1281 --no-proxy --max-pages 10

# Both PS5 and PS4 games
vinted-scraper scrape --search-text "playstation" -c 3026 -p 1281 -p 1280 --no-proxy --max-pages 15

# Nintendo Switch games
vinted-scraper scrape --search-text "nintendo" -c 3026 -p 1288 --no-proxy --max-pages 10

# All PlayStation platforms (PS1-PS5)
vinted-scraper scrape --search-text "playstation" -c 3026 \\
  -p 1281 -p 1280 -p 1279 -p 1278 -p 1277 --no-proxy --max-pages 20

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 3. WITH DESCRIPTIONS (Slower - ~10 items/min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Fetch ALL details (description, language, photos)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --fetch-details --no-proxy --max-pages 5

# Fetch details ONLY for new listings (recommended)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --details-for-new-only --no-proxy --max-pages 10

# Find English game descriptions
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 \\
  --fetch-details --no-proxy --max-pages 5
# Then query: SELECT * FROM listings WHERE language = 'en'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 4. SORTING & ORDERING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Get newest listings first
vinted-scraper scrape -c 3026 -p 1281 --order newest_first --no-proxy --max-pages 10

# Sort by price (low to high)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --order price_low_to_high --no-proxy --max-pages 10

# Sort by price (high to low)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --order price_high_to_low --no-proxy --max-pages 10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 5. ADVANCED OPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Slower scraping to avoid rate limits
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --delay 2.0 --no-proxy --max-pages 10

# Custom number of items per page
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --per-page 24 --no-proxy --max-pages 10

# Different region (French Vinted)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --base-url "https://www.vinted.fr/catalog" \\
  --locale fr --no-proxy --max-pages 5

# Extra query parameters (price filtering)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  -e "price_to=100" --no-proxy --max-pages 10

# Custom 403 error handling (wait 15 mins, 5 retries)
vinted-scraper scrape --search-text "ps5" -c 3026 \\
  --error-wait 15 --max-retries 5 --no-proxy --max-pages 50

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 6. PRODUCTION USE CASES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Daily price tracking (fast, no details, newest first)
vinted-scraper scrape -c 3026 -p 1281 --order newest_first \\
  --no-proxy --max-pages 20 --delay 1.5

# Weekly detailed scraping (descriptions for analysis)
vinted-scraper scrape --search-text "ps5" -c 3026 -p 1281 \\
  --details-for-new-only --no-proxy --max-pages 30

# Scrape 1000+ items (large dataset)
vinted-scraper scrape --search-text "playstation" -c 3026 \\
  --no-proxy --max-pages 50 --delay 1.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 7. COMMON FLAG REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SEARCH & FILTERING (at least one required):
  --search-text TEXT           Search query (e.g., "ps5", "iphone")
                               Optional when using -c or -p

  -c, --category INTEGER       Category ID (repeatable)
  -p, --platform-id INTEGER    Platform ID (repeatable, video games only)
  --order TEXT                 Sort order (newest_first, price_low_to_high, price_high_to_low)
  -e, --extra TEXT             Extra query params (key=value)

SCRAPING:
  --max-pages INTEGER         Pages to scrape [default: 5]
  --per-page INTEGER          Items per page [default: 24]
  --delay FLOAT               Delay between requests [default: 1.0]
  --no-proxy                  Skip proxy (recommended!)

ERROR HANDLING:
  --error-wait INTEGER        Minutes to wait on 403 errors [default: 30]
  --max-retries INTEGER       Max retry attempts per page [default: 3]

DETAILS:
  --fetch-details             Fetch HTML details for ALL items (slow)
  --details-for-new-only      Fetch details only for new items (fast)

REGION:
  --base-url TEXT             Vinted URL [default: vinted.sk]
  --locale TEXT               Locale code [default: sk]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 8. HELPER COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# List all categories
vinted-scraper categories

# Search for specific category
vinted-scraper categories --search "video"
vinted-scraper categories --search "electronics"

# List all platforms
vinted-scraper platforms

# Search for specific platform
vinted-scraper platforms --search "playstation"
vinted-scraper platforms --search "nintendo"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 9. WHAT DATA IS CAPTURED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALWAYS (catalog API, fast ~24 items/min):
  ✓ Title, price, currency
  ✓ Seller name and ID
  ✓ Brand, condition
  ✓ Category ID, platform IDs
  ✓ First photo URL
  ✓ First/last seen timestamps

WITH --fetch-details (HTML, slow ~10 items/min):
  ✓ Full description
  ✓ Language code (en, sk, fr, etc.)
  ✓ All photo URLs
  ✓ Shipping costs

NOT AVAILABLE:
  ✗ Location (requires browser automation)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 10. WEB DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start API server:
  python3 -m app.api.main

Open in browser:
  http://localhost:8000

Features:
  • View listings in grid or table view
  • See price changes with ↑↓ arrows
  • Create scrape configurations
  • Schedule automated scraping with cron
  • View price history charts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TIP: Always use --no-proxy for faster and more reliable scraping!
📚 Documentation: See CLAUDE.md, DATA_FIELDS_GUIDE.md, SCRAPER_BEHAVIOR.md
🌐 Dashboard: http://localhost:8000

"""
)


if __name__ == "__main__":
    app()
