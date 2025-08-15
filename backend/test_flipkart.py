import time
import re
from bs4 import BeautifulSoup
from scrapers.flipkart import FlipkartScraper

review_url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/product-reviews/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W&page=1"

with FlipkartScraper() as scraper:
    # Mask navigator.webdriver
    scraper.driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )

    print(f"Navigating to {review_url}...")
    scraper.driver.get(review_url)
    time.sleep(4)
    scraper.dismiss_login_popup()

    soup = BeautifulSoup(scraper.driver.page_source, "html.parser")
    print("Page Title:", soup.title.string if soup.title else "None")

    ## Filter out navigation chips and extract genuine review cards
    review_cards = []
    for elem in soup.find_all(['div', 'p']):
        text = elem.get_text(separator=' ', strip=True)
        # Skip repetitive category chips
        if 'overall camera battery' in text.lower():
            continue

        if (
            30 < len(text) < 400
            and not any(bad in text.lower() for bad in ['flipkart', 'policy', 'terms', 'home/', 'storage', 'discount', 'sign in'])
            and any(good in text.lower() for good in ['phone', 'camera', 'battery', 'quality', 'display', 'screen', 'apple', 'sound', 'good', 'nice', 'awesome', 'worth', 'fast', 'best'])
        ):
            if text not in review_cards:
                review_cards.append(text)

    print(f"\nReal Customer Reviews Found: {len(review_cards)}")
    for idx, r in enumerate(review_cards[:5], 1):
        print(f"\nReview {idx}:\n  \"{r}\"")
    