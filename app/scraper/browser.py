import asyncio
import os
import shutil
import time
import zipfile
import requests
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions
from app.utils.logging import get_logger

logger = get_logger(__name__)

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

    logger.info("Downloading portable Chromium (~120 MB, one-time)…")
    url = "https://download-chromium.appspot.com/dl/Linux_x64?type=snapshots"
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download Chromium: {e}")

    logger.info("Extracting Chromium…")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(base_dir)
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Failed to extract Chromium (bad zip file): {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract Chromium: {e}")

    os.remove(zip_path)

    # Check again for both possible directory names after extraction
    for chrome_dir_name in ["chrome-linux64", "chrome-linux"]:
        chrome_dir = os.path.join(base_dir, chrome_dir_name)
        chrome_bin = os.path.join(chrome_dir, "chrome")
        if os.path.exists(chrome_bin):
            os.chmod(chrome_bin, 0o755)
            return chrome_bin

    raise RuntimeError("Could not locate extracted Chromium binary")

def init_driver(headless: bool = True):
    """
    Initializes a new undetected-chromedriver instance.
    """
    chrome_path = (
        shutil.which("google-chrome")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or ensure_chromium_installed()
    )

    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    logger.info(f"Using Chrome binary: {chrome_path}")
    driver = uc.Chrome(options=options, browser_executable_path=chrome_path)
    return driver

async def get_html_with_browser(url: str, driver = None) -> str:
    """
    Fetches the HTML of a page using a headless browser to bypass Cloudflare.
    """
    should_quit = False
    if driver is None:
        driver = init_driver()
        should_quit = True

    try:
        await asyncio.to_thread(driver.get, url)
        await asyncio.sleep(5)  # Wait for the page to load
        return driver.page_source
    finally:
        if should_quit and driver:
            driver.quit()
