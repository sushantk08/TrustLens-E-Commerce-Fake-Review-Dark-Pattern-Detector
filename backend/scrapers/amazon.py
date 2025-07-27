import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper


class AmazonScraper(BaseScraper):
    """
    Scrapes product metadata and paginated customer reviews from Amazon listings.
    """

    def extract_asin(self, url: str) -> str:
        """Extracts the 10-character Amazon Standard Identification Number (ASIN)."""
        match = re.search(r'/(?:dp|gp/product|product-reviews)/([A-Z0-9]{10})', url)
        return match.group(1) if match else ''

    def get_clean_price(self, price_str: str) -> float:
        """Removes currency symbols, commas, and converts to float."""
        if not price_str:
            return 0.0
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def parse_review_date(self, date_str: str):
        """Extracts date from strings like 'Reviewed in India on 15 August 2024'."""
        if not date_str:
            return None
        match = re.search(r'on\s+(.+)$', date_str, re.IGNORECASE)
        target_str = match.group(1) if match else date_str
        try:
            return date_parser.parse(target_str, fuzzy=True).date()
        except Exception:
            return None

    def scrape_product_details(self, url: str) -> dict:
        """Scrapes core product information from the main product page."""
        self.driver.get(url)
        time.sleep(2)  

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Title
        title_tag = soup.select_one('#productTitle')
        title = title_tag.get_text(strip=True) if title_tag else ''

        # Price
        price_tag = soup.select_one('.a-price .a-offscreen') or soup.select_one('#priceblock_ourprice')
        price = self.get_clean_price(price_tag.get_text(strip=True) if price_tag else '')

        # Rating
        rating_tag = soup.select_one('span[data-hook="rating-out-of-text"]') or soup.select_one('#acrPopover')
        rating_match = re.search(r'([\d.]+)', rating_tag.get_text(strip=True) if rating_tag else '')
        rating = float(rating_match.group(1)) if rating_match else None

        # Total review count
        count_tag = soup.select_one('#acrCustomerReviewText')
        count_match = re.search(r'([\d,]+)', count_tag.get_text(strip=True) if count_tag else '')
        review_count = int(count_match.group(1).replace(',', '')) if count_match else 0

        # Image
        img_tag = soup.select_one('#landingImage') or soup.select_one('#imgBlkFront')
        image_url = img_tag.get('src', '') if img_tag else ''

        return {
            'title': title,
            'current_price': price,
            'rating': rating,
            'total_reviews_count': review_count,
            'image_url': image_url,
            'asin': self.extract_asin(url),
        }

    def scrape_reviews(self, product_url: str, max_pages: int = 3) -> list:
        """
        Navigates through paginated product reviews and extracts review cards.
        """
        asin = self.extract_asin(product_url)
        parsed_url = urlparse(product_url)
        domain = parsed_url.netloc or "www.amazon.in"

        reviews = []

        for page in range(1, max_pages + 1):
            review_url = f"https://{domain}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_{page}?pageNumber={page}&sortBy=recent"
            self.driver.get(review_url)
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            review_cards = soup.select('div[data-hook="review"]')

            if not review_cards:
                break

            for card in review_cards:
                # Reviewer name
                name_tag = card.select_one('.a-profile-name')
                reviewer_name = name_tag.get_text(strip=True) if name_tag else 'Anonymous'

                # Star rating
                star_tag = card.select_one('i[data-hook="review-star-rating"] span.a-icon-alt') or card.select_one('i[data-hook="cmps-review-star-rating"] span.a-icon-alt')
                star_match = re.search(r'([\d.]+)', star_tag.get_text(strip=True) if star_tag else '')
                star_rating = float(star_match.group(1)) if star_match else 0.0

                # Review title
                title_tag = card.select_one('a[data-hook="review-title"] span') or card.select_one('span[data-hook="review-title"] span')
                review_title = title_tag.get_text(strip=True) if title_tag else ''

                # Review body text
                body_tag = card.select_one('span[data-hook="review-body"]')
                review_text = body_tag.get_text(strip=True) if body_tag else ''

                # Review date
                date_tag = card.select_one('span[data-hook="review-date"]')
                review_date = self.parse_review_date(date_tag.get_text(strip=True) if date_tag else '')

                # Verified Purchase badge
                verified_tag = card.select_one('span[data-hook="avp-badge"]')
                is_verified = bool(verified_tag)

                reviews.append({
                    'reviewer_name': reviewer_name,
                    'rating': star_rating,
                    'review_title': review_title,
                    'review_text': review_text,
                    'review_date': review_date,
                    'is_verified_purchase': is_verified,
                })

        return reviews