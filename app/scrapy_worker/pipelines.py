"""Pipelines that persist scraped detail data to the database."""
from __future__ import annotations

from typing import Iterable, Sequence

from twisted.internet.defer import ensureDeferred

from app.db.models import Listing
from app.db.session import Session
from app.utils.details import compute_details_scraped_flag, missing_detail_fields


DETAIL_FIELDS: Sequence[str] = (
    "brand",
    "location",
    "description",
    "seller_name",
)


def _convert_photos(photos: object) -> list[str] | None:
    if not photos:
        return None
    if isinstance(photos, (list, tuple, set)):
        cleaned = [str(photo) for photo in photos if photo]
        return cleaned or None
    if isinstance(photos, str):
        return [photos]
    return None


class DetailPersistencePipeline:
    """Persist listing detail enrichments and maintain the details_scraped flag."""

    def open_spider(self, spider) -> None:  # pragma: no cover - Scrapy hook
        self.logger = getattr(spider, "logger", None)

    def process_item(self, item, spider):
        return ensureDeferred(self._persist_item(item, spider))

    async def _persist_item(self, item, spider):
        listing_id = item.get("listing_id")
        if listing_id is None:
            if self.logger:
                self.logger.warning("Detail item missing listing_id; skipping: %s", item)
            return item

        async with Session() as session:
            listing = await session.get(Listing, listing_id)
            if not listing:
                if self.logger:
                    self.logger.warning("Listing %s no longer exists; skipping detail update.", listing_id)
                return item

            updated = False

            shipping_cents = item.get("shipping_cents")
            if shipping_cents is not None:
                try:
                    listing.shipping_cents = int(shipping_cents)
                    updated = True
                except (TypeError, ValueError):
                    if self.logger:
                        self.logger.debug("Invalid shipping_cents for listing %s: %s", listing_id, shipping_cents)

            for field in DETAIL_FIELDS:
                value = item.get(field)
                if value:
                    setattr(listing, field, value)
                    updated = True

            photos_value = _convert_photos(item.get("photos"))
            if photos_value:
                listing.photos = photos_value
                if not listing.photo:
                    listing.photo = photos_value[0]
                updated = True

            details_payload = {
                "shipping_cents": listing.shipping_cents,
                "brand": listing.brand,
                "location": listing.location,
                "description": listing.description,
                "photos": listing.photos,
            }

            listing.details_scraped = compute_details_scraped_flag(details_payload)
            if listing.details_scraped:
                missing = []
            else:
                missing = list(missing_detail_fields(details_payload))

            if updated:
                await session.commit()
                if self.logger:
                    if missing:
                        self.logger.info(
                            "Updated listing %s; missing fields: %s",
                            listing_id,
                            ", ".join(missing),
                        )
                    else:
                        self.logger.info("Updated listing %s; details complete.", listing_id)
            else:
                if self.logger:
                    self.logger.debug("No changes detected for listing %s.", listing_id)

        return item
