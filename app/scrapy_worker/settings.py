"""Default Scrapy settings for the detail worker."""
from __future__ import annotations

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

DEFAULT_SETTINGS = {
    "BOT_NAME": "vinted_detail_worker",
    "ROBOTSTXT_OBEY": False,
    "USER_AGENT": DEFAULT_USER_AGENT,
    "DOWNLOAD_DELAY": 1.0,
    "RANDOMIZE_DOWNLOAD_DELAY": True,
    "AUTOTHROTTLE_ENABLED": True,
    "AUTOTHROTTLE_START_DELAY": 1.0,
    "AUTOTHROTTLE_MAX_DELAY": 10.0,
    "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
    "RETRY_ENABLED": True,
    "RETRY_TIMES": 3,
    "CONCURRENT_REQUESTS": 8,
    "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    "LOG_LEVEL": "INFO",
    "COOKIES_ENABLED": True,
    "ITEM_PIPELINES": {
        "app.scrapy_worker.pipelines.DetailPersistencePipeline": 300,
    },
}


def build_scrapy_settings(overrides: dict | None = None) -> dict:
    """Return Scrapy settings merged with optional overrides."""
    settings = DEFAULT_SETTINGS.copy()
    if overrides:
        settings.update(overrides)
    return settings
