import requests
import os
import json
from app.utils.logging import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive",
}

def warmup_vinted_session(locale="sk", cookies_file="cookies.txt", use_proxy=True):
    """
    Try to fetch the homepage to generate valid cookies and bypass Cloudflare.
    If blocked, optionally retry with a proxy.
    """
    base_url = f"https://www.vinted.{locale}/"
    logger.info(f"warming up session for {base_url} …")

    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        cookies_dict = resp.cookies.get_dict()
        if cookies_dict:
            with open(cookies_file, "w") as f:
                json.dump(cookies_dict, f)
            logger.info(f"Warmup OK, cookies saved to {cookies_file}")
        else:
            logger.warning("No cookies captured.")
        return True

    except Exception as e:
        logger.warning(f"Direct warmup failed: {e}")

        # Only retry with proxies if enabled
        if not use_proxy:
            logger.info("Proxy disabled — skipping proxy retry.")
            return False

        from app.proxies.fetch_and_test import get_working_proxy
        proxy = get_working_proxy()
        if not proxy:
            logger.error("No working proxy found.")
            return False

        logger.info(f"Retrying warmup via proxy {proxy} …")
        try:
            resp = requests.get(base_url, headers=HEADERS, proxies={"http": proxy, "https": proxy}, timeout=20)
            resp.raise_for_status()
            cookies_dict = resp.cookies.get_dict()
            with open(cookies_file, "w") as f:
                json.dump(cookies_dict, f)
            logger.info("Proxy warmup success, cookies saved.")
            return True
        except Exception as e2:
            logger.error(f"Proxy warmup also failed: {e2}")
            return False
