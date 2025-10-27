"""Scrapy item definitions used by the detail worker."""
from __future__ import annotations

import scrapy


class ListingDetailItem(scrapy.Item):
    """Normalized detail payload for a Vinted listing."""

    listing_id = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    brand = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    shipping_cents = scrapy.Field()
    photos = scrapy.Field()
    seller_name = scrapy.Field()
    raw = scrapy.Field()
