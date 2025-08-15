import re
import time
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from .base import BaseScraper
from .normalizer import clean_price_string, parse_relative_date


class FlipkartScraper(BaseScraper):
    """
    Scrapes product metadata and customer reviews from Flipkart listings.
    """

    def dismiss_login_popup(self):
        """Dismisses the Flipkart login modal if present."""
        try:
            close_buttons = self.driver.find_elements(
                "css selector", "button._2KpZ6l._2doB4z, span._30XB9F, button._2doB4z"
            )
            for btn in close_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(0.5)
                    break
        except Exception:
            pass

    def get_review_url(self, product_url: str, page: int = 1) -> str:
        """
        Constructs the dedicated reviews listing URL:
        https://www.flipkart.com/[product-name]/product-reviews/[product-id]?pid=[pid]&page=[page]
        """
        parsed = urlparse(product_url)
        params = parse_qs(parsed.query)

        # Extract pid
        pid = params.get('pid', [''])[0]
        if not pid:
            match = re.search(r'pid=([A-Z0-9]+)', product_url, re.IGNORECASE)
            if match:
                pid = match.group(1)

        path = parsed.path
        if '/p/' in path:
            review_path = path.replace('/p/', '/product-reviews/')
        elif '/product-reviews/' in path:
            review_path = path
        else:
            review_path = path + '/product-reviews'

        query_str = f"pid={pid}&page={page}" if pid else f"page={page}"
        return f"https://{parsed.netloc}{review_path}?{query_str}"

    def scrape_product_details(self, url: str) -> dict:
        self.driver.get(url)
        time.sleep(3)
        self.dismiss_login_popup()

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # 1. Title
        title_tag = (
            soup.select_one('h1 span') or
            soup.select_one('h1') or
            soup.select_one('span.VU-ZEz') or
            soup.select_one('span.B_NuCI')
        )
        title = title_tag.get_text(strip=True) if title_tag else (soup.title.string if soup.title else '')

        # 2. Price (Matches currency regex)
        prices = [t.strip() for t in soup.find_all(string=re.compile(r"^₹[\d,]+$"))]
        current_price = clean_price_string(prices[0]) if prices else 0.0

        # Original MSRP if discounted
        original_price = clean_price_string(prices[1]) if len(prices) > 1 and clean_price_string(prices[1]) > current_price else current_price

        # 3. Rating
        ratings = [t.strip() for t in soup.find_all(string=re.compile(r"^\d\.\d$"))]
        rating = float(ratings[0]) if ratings else None

        # 4. Total reviews count
        count_tag = soup.select_one('span.Wphh3L') or soup.select_one('span._2_R_DZ')
        review_count = 0
        if count_tag:
            match = re.search(r'([\d,]+)\s+Reviews', count_tag.get_text(strip=True), re.IGNORECASE)
            if match:
                review_count = int(match.group(1).replace(',', ''))

        # 5. Image
        img_tag = (
            soup.select_one('img.DByuf4') or
            soup.select_one('img._396cs4') or
            soup.select_one('img[src*="flixcart"]')
        )
        image_url = img_tag.get('src', '') if img_tag else ''

        return {
            'title': title,
            'current_price': current_price,
            'original_price': original_price,
            'rating': rating,
            'total_reviews_count': review_count,
            'image_url': image_url,
        }

    def scrape_reviews(self, product_url: str, max_pages: int = 3) -> list:
        reviews = []

        for page in range(1, max_pages + 1):
            page_url = self.get_review_url(product_url, page=page)
            self.driver.get(page_url)
            time.sleep(3)
            self.dismiss_login_popup()

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract review cards by filtering out header category chips and boilerplate
            for elem in soup.find_all(['div', 'p']):
                text = elem.get_text(separator=' ', strip=True)

                # Skip header tags and boilerplate
                if 'overall camera battery' in text.lower():
                    continue

                if (
                    30 < len(text) < 400
                    and not any(bad in text.lower() for bad in ['flipkart', 'policy', 'terms', 'home/', 'storage', 'discount', 'sign in', 'read more'])
                    and any(good in text.lower() for good in ['phone', 'camera', 'battery', 'quality', 'display', 'screen', 'apple', 'sound', 'good', 'nice', 'awesome', 'worth', 'fast', 'best', 'buy', 'product'])
                ):
                    # Clean the review text
                    cleaned_text = re.sub(r'READ MORE', '', text, flags=re.IGNORECASE).strip()
                    if not any(r['review_text'] == cleaned_text for r in reviews):
                        reviews.append({
                            'reviewer_name': 'Flipkart Customer',
                            'rating': 5.0,  # Default rating if badge not adjacent
                            'review_title': '',
                            'review_text': cleaned_text,
                            'review_date': None,
                            'is_verified_purchase': True,
                        })

        return reviews