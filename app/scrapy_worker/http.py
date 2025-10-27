"""HTTP helper utilities for the Scrapy detail worker."""
from __future__ import annotations

import random
from typing import Dict

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.1 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.1 Mobile Safari/537.36",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8,sk;q=0.6",
    "sk-SK,sk;q=0.9,en;q=0.7",
    "de-DE,de;q=0.9,en;q=0.6",
]

ACCEPT_HEADERS = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "text/html,application/xml;q=0.9,application/xhtml+xml;q=0.9,image/webp,*/*;q=0.8",
]


def build_request_headers() -> Dict[str, str]:
    """Return randomized headers that emulate typical browser traffic."""
    user_agent = random.choice(USER_AGENTS)
    accept_language = random.choice(ACCEPT_LANGUAGES)
    accept_header = random.choice(ACCEPT_HEADERS)

    return {
        "User-Agent": user_agent,
        "Accept": accept_header,
        "Accept-Language": accept_language,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    }
