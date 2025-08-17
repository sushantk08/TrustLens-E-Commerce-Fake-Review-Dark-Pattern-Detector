import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .base import BaseScraper
from .normalizer import parse_relative_date


class GoogleMapsScraper(BaseScraper):
    """
    Scrapes business details and customer reviews from Google Maps listings.
    """

    def dismiss_google_consent(self):
        """Dismisses the 'Before you continue to Google' cookie modal if present."""
        try:
            consent_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Agree')]"
            )
            for btn in consent_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    break
        except Exception:
            pass

    def detect_category(self, category_text: str) -> str:
        """Categorizes the business based on Google's listing sub-heading."""
        c = category_text.lower()
        if any(w in c for w in ['restaurant', 'cafe', 'coffee', 'bakery', 'bar', 'food', 'bistro', 'dhaba']):
            return 'restaurant'
        if any(w in c for w in ['hospital', 'clinic', 'doctor', 'medical', 'dental', 'pharmacy', 'health']):
            return 'healthcare'
        if any(w in c for w in ['car', 'auto', 'motor', 'garage', 'workshop', 'showroom', 'bike', 'dealer']):
            return 'automotive'
        return 'general_business'

    def scrape_product_details(self, url: str) -> dict:
        """Extracts business name, rating, total reviews, and category from Google Maps."""
        self.driver.get(url)
        time.sleep(4)
        self.dismiss_google_consent()

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # 1. Business Name (Header)
        title_tag = soup.select_one('h1.DUwDvf') or soup.select_one('h1')
        title = title_tag.get_text(strip=True) if title_tag else ''

        # 2. Overall Rating
        rating_tag = soup.select_one('div.F7nice span[aria-hidden="true"]')
        rating = None
        if rating_tag:
            try:
                rating = float(rating_tag.get_text(strip=True))
            except ValueError:
                rating = None

        # 3. Total Reviews Count
        count_tag = soup.select_one('div.F7nice span:last-child')
        total_reviews = 0
        if count_tag:
            match = re.search(r'([\d,]+)', count_tag.get_text(strip=True))
            if match:
                total_reviews = int(match.group(1).replace(',', ''))

        # 4. Business Category
        category_tag = soup.select_one('button[jsaction*="category"]') or soup.select_one('span.DkEaL')
        raw_category = category_tag.get_text(strip=True) if category_tag else 'General'
        category = self.detect_category(raw_category)

        # 5. Image
        img_tag = soup.select_one('button[aria-label*="Photo"] img') or soup.select_one('img[src*="googleusercontent"]')
        image_url = img_tag.get('src', '') if img_tag else ''

        return {
            'title': title,
            'current_price': 0.0,
            'original_price': 0.0,
            'rating': rating,
            'total_reviews_count': total_reviews,
            'business_category': category,
            'image_url': image_url,
        }

    def scrape_reviews(self, business_url: str, max_pages: int = 4) -> list:
        """
        Navigates to the Reviews tab and scrolls the review container to extract cards.
        """
        # Load the listing
        self.driver.get(business_url)
        time.sleep(3)
        self.dismiss_google_consent()

        # Click the "Reviews" tab if available
        try:
            reviews_tab = self.driver.find_element(
                By.XPATH, "//button[@role='tab' and (contains(@aria-label, 'Reviews') or contains(., 'Reviews'))]"
            )
            reviews_tab.click()
            time.sleep(2)
        except Exception:
            pass

        # Expand truncated reviews ("More" button)
        def expand_reviews():
            try:
                more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'More') and @aria-expanded='false']")
                for btn in more_buttons[:5]:
                    self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass

        # Scroll the dedicated Google Maps reviews pane
        for _ in range(max_pages * 3):
            expand_reviews()
            try:
                # Find scrollable reviews container
                scrollable_div = self.driver.find_element(By.XPATH, "//div[contains(@class, 'm6QErb') and @role='region']")
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_div)
            except Exception:
                # Fallback: send page down to body
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
            time.sleep(1.2)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Google Maps review card container class
        review_cards = soup.select('div.jftiEf')
        reviews = []

        for card in review_cards:
            # Reviewer Name
            name_tag = card.select_one('div.d4r55') or card.select_one('.WNx5fc')
            reviewer_name = name_tag.get_text(strip=True) if name_tag else 'Google User'

            # Local Guide Badge & Reviewer Stats
            sub_info = card.select_one('div.RfnDt')
            sub_text = sub_info.get_text(strip=True) if sub_info else ''
            is_local_guide = 'local guide' in sub_text.lower()

            # Extract reviewer's total reviews count (e.g. '15 reviews · 4 photos')
            rev_match = re.search(r'(\d+)\s+reviews?', sub_text, re.IGNORECASE)
            reviewer_total_reviews = int(rev_match.group(1)) if rev_match else 1

            # Star Rating
            star_tag = card.select_one('span.kvMYJc')
            star_rating = 5.0
            if star_tag and star_tag.get('aria-label'):
                match = re.search(r'(\d+)', star_tag['aria-label'])
                if match:
                    star_rating = float(match.group(1))

            # Review Date
            date_tag = card.select_one('span.rsqaWe')
            date_str = date_tag.get_text(strip=True) if date_tag else ''
            review_date = parse_relative_date(date_str)

            # Review Text
            body_tag = card.select_one('span.wiI7m') or card.select_one('div.MyEned')
            review_text = body_tag.get_text(separator=' ', strip=True) if body_tag else ''

            if review_text and len(review_text) > 8:
                reviews.append({
                    'reviewer_name': reviewer_name,
                    'rating': star_rating,
                    'review_title': '',
                    'review_text': review_text,
                    'review_date': review_date,
                    'is_verified_purchase': is_local_guide,  # Map Local Guide to verified credibility
                    'is_local_guide': is_local_guide,
                    'reviewer_total_reviews': reviewer_total_reviews,
                })

        return reviews