from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_headless_driver():
    """
    Initializes and returns a headless Chrome WebDriver configured
    with anti-bot mitigation and performance optimization flags.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Standard desktop User-Agent to avoid immediate bot detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Disable loading images to make review scraping faster
    prefs = {
        "profile.managed_default_content_settings.images": 2
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        # Fallback to default PATH resolution if ChromeDriverManager has network restrictions
        driver = webdriver.Chrome(options=options)

    return driver


class BaseScraper:
    """
    Base scraper context manager ensuring proper browser lifecycle.
    """
    def __enter__(self):
        self.driver = get_headless_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()