"""Entry point helpers for running the Scrapy detail worker."""
from __future__ import annotations

from typing import Optional

from dotenv import find_dotenv, load_dotenv
from scrapy.crawler import CrawlerProcess

from app.scrapy_worker.settings import build_scrapy_settings
from app.scrapy_worker.spiders.details_spider import ListingDetailSpider

load_dotenv(find_dotenv())


def run_detail_spider(
    *,
    batch_size: int = 100,
    source: Optional[str] = None,
    limit: Optional[int] = None,
    locale: str = "sk",
    warmup: bool = True,
    download_delay: Optional[float] = None,
    concurrent_requests: Optional[int] = None,
    log_level: Optional[str] = None,
) -> None:
    """Run the ListingDetailSpider with optional runtime overrides."""
    overrides: dict = {}
    if download_delay is not None:
        overrides["DOWNLOAD_DELAY"] = max(download_delay, 0)
    if concurrent_requests is not None:
        overrides["CONCURRENT_REQUESTS"] = max(int(concurrent_requests), 1)
        overrides["CONCURRENT_REQUESTS_PER_DOMAIN"] = max(int(concurrent_requests), 1)
    if log_level:
        overrides["LOG_LEVEL"] = log_level

    process = CrawlerProcess(settings=build_scrapy_settings(overrides))
    process.crawl(
        ListingDetailSpider,
        batch_size=batch_size,
        source=source,
        limit=limit,
        locale=locale,
        warmup=warmup,
    )
    process.start()
