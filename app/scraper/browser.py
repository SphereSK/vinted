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

# ======================================================
#   Ensure Chromium Portable
# ======================================================

def ensure_chromium_installed() -> str:
    """
    Ensure portable Chromium is available in ~/.local/share/undetected_chromedriver.
    If not, download and extract it automatically.
    """
    base_dir = os.path.expanduser("~/.local/share/undetected_chromedriver")

    # Try existing binaries first
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

    for chrome_dir_name in ["chrome-linux64", "chrome-linux"]:
        chrome_dir = os.path.join(base_dir, chrome_dir_name)
        chrome_bin = os.path.join(chrome_dir, "chrome")
        if os.path.exists(chrome_bin):
            os.chmod(chrome_bin, 0o755)
            return chrome_bin

    raise RuntimeError("Could not locate extracted Chromium binary")


# ======================================================
#   Initialize Headless Browser
# ======================================================

async def init_driver(headless: bool = True):
    """
    Initializes a new undetected-chromedriver instance (portable & sandbox-safe).
    """
    # Always prefer local portable Chromium to avoid Snap sandbox
    chrome_path = ensure_chromium_installed()

    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    # Sandbox-safe options for VPS / Docker / Snap
    flags = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-blink-features=AutomationControlled",
        "--window-size=1280,800",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--single-process",
        "--no-zygote",
        "--remote-debugging-port=0",  # dynamic port
    ]
    for flag in flags:
        options.add_argument(flag)

    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    logger.info(f"Using portable Chromium binary: {chrome_path}")

    # Print version (optional debug)
    try:
        process = await asyncio.create_subprocess_shell(
            f"{chrome_path} --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if stdout:
            logger.info(f"Chromium version: {stdout.decode().strip()}")
        if stderr and b"memlock" not in stderr:
            logger.warning(f"Chromium version stderr: {stderr.decode().strip()}")
    except Exception as e:
        logger.warning(f"Could not get Chromium version: {e}")

    # Create driver instance
    try:
        driver = uc.Chrome(options=options, browser_executable_path=chrome_path, headless=headless)
        return driver
    except Exception as e:
        logger.error(f"Failed to init browser: {e}", exc_info=True)
        raise


# ======================================================
#   HTML Fetch via Browser
# ======================================================

async def get_html_with_browser(url: str, driver=None) -> str:
    """
    Fetches the HTML of a page using a headless browser to bypass Cloudflare.
    """
    should_quit = False
    if driver is None:
        driver = await init_driver()
        should_quit = True

    try:
        await asyncio.to_thread(driver.get, url)
        await asyncio.sleep(5)  # give time for Cloudflare challenge
        html = driver.page_source or ""
        if "<html" not in html:
            raise ValueError("Empty or invalid HTML response")
        return html
    except Exception as e:
        logger.error(f"Error in get_html_with_browser: {e}", exc_info=True)
        return "<html><body>Error fetching page</body></html>"
    finally:
        if should_quit and driver:
            try:
                driver.quit()
            except Exception:
                pass
