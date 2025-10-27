"""Spider that enriches listings lacking detailed fields."""
from __future__ import annotations

import asyncio
import json
import os
import random
from pathlib import Path
from typing import Optional

import scrapy
from sqlalchemy import and_, select

from app.db.models import Listing
from app.db.session import Session
from app.scraper.parse_detail import parse_detail_html
from app.scraper.session_warmup import warmup_vinted_session
from app.scrapy_worker.items import ListingDetailItem
from app.scrapy_worker.http import build_request_headers

class ListingDetailSpider(scrapy.Spider):
    """Scrape listing detail pages and persist missing metadata."""

    name = "listing_details"
    handle_httpstatus_list = [403, 429]

    def __init__(
        self,
        batch_size: int = 100,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        locale: str = "sk",
        warmup: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.batch_size = max(int(batch_size), 1)
        self.source = source
        self.limit = int(limit) if limit else None
        self.locale = locale
        self.warmup = bool(warmup)
        self.cookies_path = Path(os.getenv("SCRAPER_COOKIES_FILE", "cookies.txt"))
        self.session_cookies = None
        self.max_retries = 3

    async def start(self):
        if self.warmup:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    warmup_vinted_session,
                    self.locale,
                    str(self.cookies_path),
                    False,
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Warmup failed (%s); continuing without warmup.", exc)

        self.session_cookies = self._load_cookies()
        if self.session_cookies:
            self.logger.info("Loaded %d cookies for session reuse.", len(self.session_cookies))

        candidates = await self._load_candidates()
        if not candidates:
            self.logger.info("No listings require detail scraping.")
            return

        for listing_id, url, source in candidates:
            await asyncio.sleep(random.uniform(0.2, 0.6))
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=build_request_headers(),
                dont_filter=True,
                cookies=self.session_cookies,
                meta={"listing_id": listing_id, "source": source, "retry_count": 0},
            )

    async def _load_candidates(self) -> list[tuple[int, str, Optional[str]]]:
        filters = [Listing.is_active.is_(True)]
        filters.append(Listing.details_scraped.is_(False))
        if self.source:
            filters.append(Listing.source == self.source)

        async with Session() as session:
            query = (
                select(Listing.id, Listing.url, Listing.source)
                .where(and_(*filters))
                .order_by(Listing.last_seen_at.desc())
                .limit(self.limit or self.batch_size)
            )
            result = await session.execute(query)
            return [(row.id, row.url, row.source) for row in result.all()]

    def parse(self, response, **kwargs):
        listing_id = response.meta.get("listing_id")
        source = response.meta.get("source")
        retry_count = response.meta.get("retry_count", 0)

        if response.status in {403, 429}:
            if retry_count < self.max_retries:
                self.logger.info(
                    "Retrying %s (%s) after status %s (attempt %s/%s)",
                    listing_id,
                    response.url,
                    response.status,
                    retry_count + 1,
                    self.max_retries,
                )
                yield response.request.replace(
                    headers=build_request_headers(),
                    cookies=self.session_cookies,
                    dont_filter=True,
                    meta={
                        "listing_id": listing_id,
                        "source": source,
                        "retry_count": retry_count + 1,
                    },
                )
                return
            self.logger.warning(
                "Giving up on listing %s after %s attempts (status %s).",
                listing_id,
                self.max_retries,
                response.status,
            )
            return

        detail_data = parse_detail_html(response.text)
        item = ListingDetailItem()
        item["listing_id"] = listing_id
        item["url"] = response.url
        item["source"] = source
        item["brand"] = detail_data.get("brand")
        item["location"] = detail_data.get("location")
        item["description"] = detail_data.get("description")
        item["shipping_cents"] = detail_data.get("shipping_cents")
        item["photos"] = detail_data.get("photos")
        item["seller_name"] = detail_data.get("seller_name")
        item["raw"] = detail_data

        yield item

    def _load_cookies(self):
        if not self.cookies_path.exists():
            return None
        try:
            with self.cookies_path.open("r") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            self.logger.debug("Failed to load cookies from %s: %s", self.cookies_path, exc)
        return None
