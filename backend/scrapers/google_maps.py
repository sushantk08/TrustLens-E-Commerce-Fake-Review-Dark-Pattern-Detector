import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
)

from .base import BaseScraper
from .normalizer import parse_relative_date


class GoogleMapsScraper(BaseScraper):
    """
    Scrapes business information and customer reviews from Google Maps.
    """

    def handle_consent(self):
        """Dismiss Google cookie / consent dialogs if present."""
        xpaths = [
            "//button[contains(., 'Accept all')]",
            "//button[contains(., 'Accept')]",
            "//button[contains(., 'I agree')]",
            "//button[contains(., 'Agree')]",
        ]

        for xpath in xpaths:
            try:
                buttons = self.driver.find_elements(
                    By.XPATH,
                    xpath,
                )

                for button in buttons:
                    try:
                        if button.is_displayed():
                            self.driver.execute_script(
                                "arguments[0].click();",
                                button,
                            )
                            time.sleep(1.5)
                            return
                    except Exception:
                        continue

            except Exception:
                continue

    def detect_category(self, category_text: str) -> str:
        """Convert Google business category into TrustLens category."""

        category = category_text.lower()

        if any(
            word in category
            for word in [
                "restaurant",
                "cafe",
                "coffee",
                "bakery",
                "bar",
                "food",
                "bistro",
                "dhaba",
            ]
        ):
            return "restaurant"

        if any(
            word in category
            for word in [
                "hotel",
                "resort",
                "stay",
                "lodge",
                "convention",
                "guest house",
            ]
        ):
            return "restaurant"

        if any(
            word in category
            for word in [
                "hospital",
                "clinic",
                "doctor",
                "medical",
                "dental",
                "pharmacy",
                "health",
            ]
        ):
            return "healthcare"

        if any(
            word in category
            for word in [
                "car",
                "auto",
                "motor",
                "garage",
                "workshop",
                "showroom",
                "bike",
                "dealer",
            ]
        ):
            return "automotive"

        return "general_business"

    def scrape_product_details(self, url: str) -> dict:
        """
        Extract business title, rating, category, review count
        and image from the Google Maps page.
        """

        self.driver.get(url)
        time.sleep(5)
        self.handle_consent()

        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser",
        )

        # Business title
        title_tag = (
            soup.select_one("h1.DUwDvf")
            or soup.select_one("h1")
        )

        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else (
                soup.title.string
                if soup.title
                else ""
            )
        )

        # Overall rating
        rating_tag = soup.select_one(
            "div.F7nice span[aria-hidden='true']"
        )

        rating = None

        if rating_tag:
            try:
                rating = float(
                    rating_tag.get_text(strip=True)
                )
            except ValueError:
                rating = None

        # Google often does not expose the review count
        # in the initial page DOM.
        total_reviews = 0

        # Category
        category_tag = (
            soup.select_one(
                "button[jsaction*='category']"
            )
            or soup.select_one(
                "span.DkEaL"
            )
        )

        raw_category = (
            category_tag.get_text(strip=True)
            if category_tag
            else "General"
        )

        category = self.detect_category(
            raw_category
        )

        # Image
        image_tag = (
            soup.select_one(
                "button[aria-label*='Photo'] img"
            )
            or soup.select_one(
                "img[src*='googleusercontent']"
            )
        )

        image_url = (
            image_tag.get("src", "")
            if image_tag
            else ""
        )

        return {
            "title": title,
            "current_price": 0.0,
            "original_price": 0.0,
            "rating": rating,
            "total_reviews_count": total_reviews,
            "business_category": category,
            "image_url": image_url,
        }

    def build_reviews_url(self, business_url: str) -> str:
        """
        Build Google's dedicated review-feed URL.

        The Place ID is extracted from the original URL.
        We do not rely on driver.current_url because Google
        can rewrite normal Maps URLs.
        """

        match = re.search(
            r"!1s([^!]+)",
            business_url,
        )

        if not match:
            try:
                self.driver.get(business_url)
                time.sleep(5)
                self.handle_consent()

                current_url = self.driver.current_url

                match = re.search(
                    r"!1s([^!]+)",
                    current_url,
                )

            except Exception:
                match = None

        if not match:
            return business_url

        place_id = match.group(1)

        return (
            "https://www.google.com/maps/place//data="
            f"!4m4!3m3!1s{place_id}!9m1!1b1"
        )

    def wait_for_reviews(self, timeout=15):
        """Wait until Google review cards appear."""

        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                count = self.driver.execute_script(
                    """
                    return document.querySelectorAll(
                        'div.jftiEf[data-review-id]'
                    ).length;
                    """
                )

                if count and count > 0:
                    return True

            except Exception:
                pass

            time.sleep(1)

        return False

    def find_review_container(self):
        """
        Find Google's scrollable review container.
        """

        return self.driver.execute_script(
            """
            const review =
                document.querySelector(
                    'div.jftiEf[data-review-id]'
                );

            if (!review) {
                return null;
            }

            let current = review;
            const candidates = [];

            for (
                let i = 0;
                current && i < 12;
                i++,
                current = current.parentElement
            ) {
                const style = getComputedStyle(
                    current
                );

                const isScrollable =
                    current.scrollHeight >
                    current.clientHeight + 100;

                const hasOverflow =
                    style.overflowY === 'auto' ||
                    style.overflowY === 'scroll';

                if (
                    isScrollable &&
                    hasOverflow
                ) {
                    candidates.push(current);
                }
            }

            return candidates[0] || null;
            """
        )

    def expand_more_buttons(self):
        """
        Click visible 'See more' buttons so the complete
        review text becomes available.
        """

        try:
            buttons = self.driver.find_elements(
                By.XPATH,
                "//button[@aria-label='See more']",
            )

            for button in buttons:
                try:
                    if button.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();",
                            button,
                        )
                except Exception:
                    continue

        except Exception:
            pass

    def get_raw_reviews(self):
        """
        Extract structured review information directly from
        Google's current review-card HTML.
        """

        return self.driver.execute_script(
            """
            const cards = [
                ...document.querySelectorAll(
                    'div.jftiEf[data-review-id]'
                )
            ];

            const results = [];
            const seen = new Set();

            for (const card of cards) {
                const reviewId =
                    card.getAttribute(
                        'data-review-id'
                    );

                if (
                    !reviewId ||
                    seen.has(reviewId)
                ) {
                    continue;
                }

                seen.add(reviewId);

                const reviewerElement =
                    card.querySelector(
                        '.d4r55'
                    );

                const reviewerInfoElement =
                    card.querySelector(
                        '.RfnDt'
                    );

                const ratingElement =
                    card.querySelector(
                        '[role="img"][aria-label*="stars"]'
                    );

                const dateElement =
                    card.querySelector(
                        '.rsqaWe'
                    );

                const reviewTextElement =
                    card.querySelector(
                        '.wiI7pd'
                    );

                const reviewerName =
                    reviewerElement
                    ? reviewerElement.textContent.trim()
                    : '';

                const reviewerInfo =
                    reviewerInfoElement
                    ? reviewerInfoElement.textContent.trim()
                    : '';

                const ratingLabel =
                    ratingElement
                    ? ratingElement.getAttribute(
                        'aria-label'
                    )
                    : '';

                const reviewDate =
                    dateElement
                    ? dateElement.textContent.trim()
                    : '';

                const reviewText =
                    reviewTextElement
                    ? reviewTextElement.textContent.trim()
                    : '';

                let rating = null;

                if (ratingLabel) {
                    const match =
                        ratingLabel.match(
                            /([1-5](?:\\.\\d+)?)\\s*stars?/i
                        );

                    if (match) {
                        rating =
                            parseFloat(match[1]);
                    }
                }

                results.push({
                    review_id: reviewId,
                    reviewer_name: reviewerName,
                    reviewer_info: reviewerInfo,
                    rating: rating,
                    review_date: reviewDate,
                    review_text: reviewText
                });
            }

            return results;
            """
        )

    def parse_one_review(self, raw_review):
        """
        Convert structured Google review data into the
        format expected by the TrustLens database.
        """

        reviewer_name = (
            raw_review.get(
                "reviewer_name",
                "",
            ).strip()
            or "Google User"
        )

        reviewer_info = (
            raw_review.get(
                "reviewer_info",
                "",
            ).strip()
        )

        review_text = (
            raw_review.get(
                "review_text",
                "",
            ).strip()
        )

        rating = raw_review.get(
            "rating"
        )

        if rating is None:
            rating = 5.0

        # Google reviewer profile information example:
        #
        # Local Guide · 146 reviews · 1,299 photos
        #
        is_local_guide = (
            "local guide"
            in reviewer_info.lower()
        )

        reviewer_total_reviews = 1

        review_count_match = re.search(
            r"([\d,]+)\s+reviews?",
            reviewer_info,
            re.IGNORECASE,
        )

        if review_count_match:
            reviewer_total_reviews = int(
                review_count_match
                .group(1)
                .replace(",", "")
            )

        # Parse relative date
        date_text = (
            raw_review.get(
                "review_date",
                "",
            ).strip()
        )

        review_date = None

        if date_text:
            review_date = parse_relative_date(
                date_text
            )

        return {
            "reviewer_name": reviewer_name,
            "rating": rating,
            "review_title": "",
            "review_text": review_text,
            "review_date": review_date,
            "is_verified_purchase": is_local_guide,
            "is_local_guide": is_local_guide,
            "reviewer_total_reviews": (
                reviewer_total_reviews
            ),
        }

    def scrape_reviews(
        self,
        business_url: str,
        max_pages: int = 6,
    ) -> list:
        """
        Scrape reviews from Google's dedicated review feed.
        """

        review_url = self.build_reviews_url(
            business_url
        )

        self.driver.get(review_url)
        time.sleep(5)
        self.handle_consent()

        if not self.wait_for_reviews(
            timeout=15
        ):
            return []

        container = (
            self.find_review_container()
        )

        if not container:
            return []

        store = {}

        last_scroll_position = -1
        unchanged = 0

        max_cycles = max_pages * 4

        for _ in range(max_cycles):
            self.expand_more_buttons()
            time.sleep(0.5)

            try:
                raw_reviews = (
                    self.get_raw_reviews()
                )

                for raw_review in raw_reviews:
                    review_id = raw_review.get(
                        "review_id"
                    )

                    if (
                        not review_id
                        or review_id in store
                    ):
                        continue

                    parsed = (
                        self.parse_one_review(
                            raw_review
                        )
                    )

                    if (
                        parsed["review_text"]
                        and len(
                            parsed[
                                "review_text"
                            ]
                        ) > 8
                    ):
                        store[
                            review_id
                        ] = parsed

            except WebDriverException:
                time.sleep(1)
                continue

            # Scroll through the review list.
            try:
                after_scroll = (
                    self.driver.execute_script(
                        """
                        const element = arguments[0];

                        element.scrollTop += Math.max(
                            400,
                            Math.floor(
                                element.clientHeight * 0.85
                            )
                        );

                        return element.scrollTop;
                        """,
                        container,
                    )
                )

            except StaleElementReferenceException:
                container = (
                    self.find_review_container()
                )

                if not container:
                    break

                continue

            if (
                after_scroll
                == last_scroll_position
            ):
                unchanged += 1
            else:
                unchanged = 0

            last_scroll_position = after_scroll

            if unchanged >= 4:
                break

            time.sleep(1.2)

        return list(
            store.values()
        )