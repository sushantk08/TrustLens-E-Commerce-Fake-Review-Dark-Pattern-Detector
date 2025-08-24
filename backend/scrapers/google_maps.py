import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

from .base import BaseScraper
from .normalizer import parse_relative_date


class GoogleMapsScraper(BaseScraper):
    """
    Scrapes business metadata and paginated customer reviews from Google Maps listings.
    """

    def handle_consent(self):
        """Dismisses the Google cookie / consent dialog if present."""
        xpaths = [
            "//button[contains(., 'Accept all')]",
            "//button[contains(., 'Accept')]",
            "//button[contains(., 'I agree')]",
            "//button[contains(., 'Agree')]",
        ]
        for xpath in xpaths:
            try:
                buttons = self.driver.find_elements(By.XPATH, xpath)
                for btn in buttons:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1.5)
                        return
            except Exception:
                continue

    def detect_category(self, category_text: str) -> str:
        c = category_text.lower()
        if any(w in c for w in ['restaurant', 'cafe', 'coffee', 'bakery', 'bar', 'food', 'bistro', 'dhaba']):
            return 'restaurant'
        if any(w in c for w in ['hotel', 'resort', 'stay', 'lodge', 'convention', 'guest house']):
            return 'restaurant'  # Group hospitality with dining/hospitality aspects
        if any(w in c for w in ['hospital', 'clinic', 'doctor', 'medical', 'dental', 'pharmacy', 'health']):
            return 'healthcare'
        if any(w in c for w in ['car', 'auto', 'motor', 'garage', 'workshop', 'showroom', 'bike', 'dealer']):
            return 'automotive'
        return 'general_business'

    def scrape_product_details(self, url: str) -> dict:
        """Extracts listing title, overall rating, and category."""
        self.driver.get(url)
        time.sleep(5)
        self.handle_consent()

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Title
        title_tag = soup.select_one('h1.DUwDvf') or soup.select_one('h1')
        title = title_tag.get_text(strip=True) if title_tag else (soup.title.string if soup.title else '')

        # Rating
        rating_tag = soup.select_one('div.F7nice span[aria-hidden="true"]')
        rating = None
        if rating_tag:
            try:
                rating = float(rating_tag.get_text(strip=True))
            except ValueError:
                rating = None

        # Total reviews count
        count_tag = soup.select_one('div.F7nice span:last-child')
        total_reviews = 0
        if count_tag:
            match = re.search(r'([\d,]+)', count_tag.get_text(strip=True))
            if match:
                total_reviews = int(match.group(1).replace(',', ''))

        # Category
        category_tag = soup.select_one('button[jsaction*="category"]') or soup.select_one('span.DkEaL')
        raw_category = category_tag.get_text(strip=True) if category_tag else 'General'
        category = self.detect_category(raw_category)

        # Image
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

    def find_all_reviews_button(self):
        """Locates the button that navigates to the full reviews feed."""
        selectors = [
            "//button[@aria-label='All reviews']",
            "//button[contains(normalize-space(.), 'All reviews')]",
            "//*[@aria-label='All reviews']",
            "//button[contains(@aria-label, 'Reviews for') or contains(@aria-label, 'reviews for')]",
            "//button[contains(., 'More reviews')]",
            "//button[@role='tab' and contains(., 'Reviews')]",
        ]
        for xpath in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        return None

    def click_all_reviews(self, button):
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button
            )
            time.sleep(1)
        except Exception:
            pass

        try:
            button.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", button)
                return True
            except Exception:
                return False

    def wait_for_reviews(self, timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            try:
                count = self.driver.execute_script("return document.querySelectorAll('div[data-review-id]').length;")
                if count and count > 0:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def find_review_container(self):
        return self.driver.execute_script("""
            const review = document.querySelector('div[data-review-id]');
            if (!review) return null;

            let current = review;
            const candidates = [];
            for (let i = 0; current && i < 10; i++, current = current.parentElement) {
                const style = getComputedStyle(current);
                const isScrollable = current.scrollHeight > current.clientHeight + 100;
                const hasOverflow = style.overflowY === 'auto' || style.overflowY === 'scroll';
                if (isScrollable && hasOverflow) {
                    candidates.push(current);
                }
            }
            return candidates[0] || null;
        """)

    def expand_more_buttons(self):
        try:
            buttons = self.driver.find_elements(
                By.XPATH, "//button[@aria-label='See more' or normalize-space(.)='More']"
            )
            for btn in buttons:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    continue
        except Exception:
            pass

    def get_raw_reviews(self):
        return self.driver.execute_script("""
            const cards = [...document.querySelectorAll('div[data-review-id]')];
            const results = [];
            const seen = new Set();

            for (const card of cards) {
                const reviewId = card.getAttribute('data-review-id');
                if (!reviewId || seen.has(reviewId)) continue;
                seen.add(reviewId);

                const text = (card.innerText || '').trim();
                results.push({ review_id: reviewId, raw_text: text });
            }
            return results;
        """)

    def parse_one_review(self, raw_review):
        raw_text = raw_review.get("raw_text", "")
        review_id = raw_review.get("review_id", "")
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        # 1. Author
        author = lines[0] if lines else "Google User"

        # 2. Rating (matches "X/5" e.g., 4/5, 5/5)
        rating_match = re.search(r"\b([1-5])\s*/\s*5\b", raw_text)
        rating = float(rating_match.group(1)) if rating_match else 5.0

        # 3. Local Guide & stats
        is_local_guide = "local guide" in raw_text.lower()
        rev_count_match = re.search(r"(\d+)\s+reviews?", raw_text, re.IGNORECASE)
        reviewer_total_reviews = int(rev_count_match.group(1)) if rev_count_match else 1

        # 4. Date
        date_str = ""
        for line in lines:
            if " on google" in line.lower() or " on tripadvisor" in line.lower():
                date_str = re.sub(r"\s+on\s+.*$", "", line, flags=re.IGNORECASE).strip()
                break
        review_date = parse_relative_date(date_str) if date_str else None

        # 5. Clean Review Text
        rating_idx = -1
        for i, l in enumerate(lines):
            if re.fullmatch(r"[1-5]\s*/\s*5", l):
                rating_idx = i
                break

        text_lines = lines[rating_idx + 1:] if rating_idx != -1 else lines[1:]
        ignored = {
            "more", "see more", "like", "share", "read more", "read more on tripadvisor",
            "google", "tripadvisor"
        }
        clean_lines = [
            l for l in text_lines
            if l.lower() not in ignored and not l.lower().startswith("read more on")
        ]
        review_text = "\n".join(clean_lines).strip()

        return {
            'reviewer_name': author,
            'rating': rating,
            'review_title': '',
            'review_text': review_text,
            'review_date': review_date,
            'is_verified_purchase': is_local_guide,
            'is_local_guide': is_local_guide,
            'reviewer_total_reviews': reviewer_total_reviews,
        }

    def scrape_reviews(self, business_url: str, max_pages: int = 6) -> list:
        # Load business page
        self.driver.get(business_url)
        time.sleep(5)
        self.handle_consent()

        # Click "All reviews" / Reviews button
        btn = self.find_all_reviews_button()
        if btn:
            self.click_all_reviews(btn)
            time.sleep(2)

        # Wait for review cards to populate
        if not self.wait_for_reviews(timeout=15):
            return []

        container = self.find_review_container()
        if not container:
            return []

        store = {}
        last_scroll_pos = -1
        unchanged = 0
        max_cycles = max_pages * 4

        for _ in range(max_cycles):
            self.expand_more_buttons()
            time.sleep(0.4)

            try:
                raw_batch = self.get_raw_reviews()
                for item in raw_batch:
                    rid = item.get("review_id")
                    if rid and rid not in store:
                        parsed = self.parse_one_review(item)
                        if parsed['review_text'] and len(parsed['review_text']) > 8:
                            store[rid] = parsed
            except WebDriverException:
                time.sleep(1)
                continue

            # Scroll the container
            try:
                after = self.driver.execute_script("""
                    const el = arguments[0];
                    el.scrollTop += Math.max(400, Math.floor(el.clientHeight * 0.85));
                    return el.scrollTop;
                """, container)
            except StaleElementReferenceException:
                container = self.find_review_container()
                if not container:
                    break
                continue

            if after == last_scroll_pos:
                unchanged += 1
            else:
                unchanged = 0
            last_scroll_pos = after

            if unchanged >= 4:
                break
            time.sleep(1.2)

        return list(store.values())