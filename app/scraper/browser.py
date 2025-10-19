import time
import undetected_chromedriver as uc
from undetected_chromedriver import ChromeOptions

def get_html_with_browser(url: str) -> str:
    """
    Fetches the HTML of a page using a headless browser to bypass Cloudflare.
    """
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = uc.Chrome(options=options)
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        return driver.page_source
    finally:
        if driver:
            driver.quit()
