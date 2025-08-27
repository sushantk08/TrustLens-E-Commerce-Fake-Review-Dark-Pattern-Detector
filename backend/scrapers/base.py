from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_headless_driver():
    """
    Initializes a lightweight headless Chrome instance configured with
    anti-bot stealth mitigation and strict low-memory constraints
    to run reliably in 512MB cloud environments.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Cloud container memory optimizations
    options.add_argument("--single-process")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--js-flags=--max-old-space-size=128")

    # Standard desktop User-Agent to avoid immediate bot detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Disable loading images to reduce memory footprint and bandwidth
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
        # Fallback to system Chromium binary if present
        driver = webdriver.Chrome(options=options)

    # Mask navigator.webdriver via Chrome DevTools Protocol (CDP)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
        )
    except Exception:
        pass

    return driver


class BaseScraper:
    """
    Context manager ensuring proper driver creation and cleanup.
    """
    def __enter__(self):
        self.driver = get_headless_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()