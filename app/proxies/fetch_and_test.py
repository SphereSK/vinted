# app/proxies/fetch_and_test.py
import requests
import random
import time

PROXY_SOURCE = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json"

def test_proxy(proxy_url: str, timeout: int = 5) -> bool:
    """Check if proxy works by requesting a lightweight page."""
    test_url = "https://www.google.com/generate_204"
    try:
        r = requests.get(test_url, proxies={"http": proxy_url, "https": proxy_url}, timeout=timeout)
        if r.status_code in (200, 204):
            return True
    except Exception:
        pass
    return False


def get_working_proxy(max_attempts: int = 100, prefer_https: bool = True) -> str:
    """
    Fetch proxies from structured JSON, filter, test, and return the first working one.
    Automatically supports HTTP, HTTPS, SOCKS4, SOCKS5.
    """
    print("🔍 Fetching proxies from Proxifly JSON feed…")
    try:
        r = requests.get(PROXY_SOURCE, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"⚠️  Failed to fetch proxy list: {e}")
        return None

    # --- FILTER ---
    proxies = []
    for p in data:
        proxy_url = p.get("proxy")
        proto = p.get("protocol", "http").lower()
        score = p.get("score", 0)
        https_ok = p.get("https", False)
        country = (p.get("geolocation") or {}).get("country", "")

        # Basic filtering: prefer working, high score, https-capable, and nearby
        if not proxy_url or ":" not in proxy_url:
            continue
        if prefer_https and not https_ok and proto.startswith("http"):
            continue
        if score < 1:
            continue

        proxies.append(proxy_url)

    if not proxies:
        print("⚠️  No proxies available after filtering.")
        return None

    random.shuffle(proxies)
    print(f"📦 Loaded {len(proxies)} proxies to test ({min(len(proxies), max_attempts)} max)")

    # --- TEST ---
    for attempt, proxy in enumerate(proxies[:max_attempts], 1):
        print(f"🧪 Testing proxy {attempt}/{max_attempts}: {proxy}")
        if test_proxy(proxy):
            print(f"✅ Working proxy found: {proxy}")
            return proxy
        time.sleep(0.5)

    print("❌ No working proxy found.")
    return None
