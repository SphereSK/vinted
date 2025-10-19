import json
import os
import time
import zipfile
import shutil
import requests
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions


def ensure_chromium_installed() -> str:
    """
    Ensure portable Chromium is available in ~/.local/share/undetected_chromedriver.
    If not, download and extract it automatically from the public snapshot endpoint.
    """
    base_dir = os.path.expanduser("~/.local/share/undetected_chromedriver")

    # Try both possible directory names
    for chrome_dir_name in ["chrome-linux64", "chrome-linux"]:
        chrome_dir = os.path.join(base_dir, chrome_dir_name)
        chrome_bin = os.path.join(chrome_dir, "chrome")
        if os.path.exists(chrome_bin):
            return chrome_bin

    os.makedirs(base_dir, exist_ok=True)
    zip_path = os.path.join(base_dir, "chrome.zip")

    print("⚙️  Downloading portable Chromium (~120 MB, one-time)…")
    url = "https://download-chromium.appspot.com/dl/Linux_x64?type=snapshots"
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"❌ Failed to download Chromium: {e}")

    print("📦 Extracting Chromium …")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(base_dir)
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"❌ Failed to extract Chromium (bad zip file): {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to extract Chromium: {e}")

    os.remove(zip_path)

    # Check again for both possible directory names after extraction
    for chrome_dir_name in ["chrome-linux64", "chrome-linux"]:
        chrome_dir = os.path.join(base_dir, chrome_dir_name)
        chrome_bin = os.path.join(chrome_dir, "chrome")
        if os.path.exists(chrome_bin):
            os.chmod(chrome_bin, 0o755)
            return chrome_bin

    raise RuntimeError("❌ Could not locate extracted Chromium binary")



def browser_warmup(locale: str = "sk"):
    """
    Launch portable headless Chromium with undetected-chromedriver
    to bypass Cloudflare and save cookies.txt.
    """
    base_url = f"https://www.vinted.{locale}"
    print(f"🌐 Launching undetected Chrome for {base_url} …")

    chrome_path = (
        shutil.which("google-chrome")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or ensure_chromium_installed()
    )

    options = ChromeOptions()
    # Try without headless first - Cloudflare detects headless browsers
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,800")

    # Additional stealth options
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        print(f"✅ Using Chrome binary: {chrome_path}")
        driver = uc.Chrome(options=options, browser_executable_path=chrome_path)
        driver.get(base_url)
        print("⏳ Waiting for page to load...")
        time.sleep(5)

        # Check if we got through Cloudflare
        page_title = driver.title
        print(f"📄 Page title: {page_title}")

        # Wait additional time for Cloudflare challenge
        if "Just a moment" in page_title or "challenge" in page_title.lower():
            print("🔄 Cloudflare challenge detected, waiting 20s for redirect...")
            time.sleep(20)

            # Check again after waiting
            page_title = driver.title
            print(f"📄 Updated page title: {page_title}")

            # If still on challenge, wait more
            if "Just a moment" in page_title:
                print("⏳ Still on challenge page, waiting another 10s...")
                time.sleep(10)
        else:
            print("✅ No Cloudflare challenge detected")

        # Always wait a bit more for cookies to be set
        print("⏳ Waiting 5s for cookies to be set...")
        time.sleep(5)

        cookies = driver.get_cookies()
        print(f"🍪 Captured {len(cookies)} cookies")

        # Print cookie names for debugging
        if cookies:
            cookie_names = [c.get('name') for c in cookies]
            print(f"   Cookie names: {', '.join(cookie_names)}")

        with open("cookies.txt", "w") as f:
            json.dump(cookies, f, indent=2)

        if cookies:
            print("✅ Cookies saved to cookies.txt")
        else:
            print("⚠️  No cookies captured - site may be blocking automated access")
    except uc.exceptions.WebDriverException as e:
        print(f"❌ WebDriver error during browser warmup: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Browser warmup failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    browser_warmup("sk")
