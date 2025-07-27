import re
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .base import BaseScraper


class AmazonScraper(BaseScraper):
    """
    Scrapes Amazon product metadata and customer reviews.

    Supports:
    - Normal Amazon product URLs
    - Amazon short URLs such as /d/XXXXXXXXXX
    - Product pages
    - Paginated review pages
    """

    # ------------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------------

    def _clean_text(self, value: str) -> str:
        """
        Normalize whitespace and return clean text.
        """
        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value)
        ).strip()

    def _is_blocked_page(self, soup: BeautifulSoup) -> bool:
        """
        Detect common Amazon CAPTCHA, robot-check, login and
        blocked pages.
        """

        title = self._clean_text(
            soup.title.get_text(
                " ",
                strip=True
            )
            if soup.title
            else ""
        ).lower()

        page_text = self._clean_text(
            soup.get_text(
                " ",
                strip=True
            )
        ).lower()

        blocked_phrases = [
            "sorry, we just need to make sure you're not a robot",
            "enter the characters you see below",
            "type the characters you see in this image",
            "robot check",
            "captcha",
            "automated access",
            "sorry, something went wrong",
            "access denied",
        ]

        for phrase in blocked_phrases:
            if phrase in page_text:
                return True

        title_phrases = [
            "robot check",
            "captcha",
            "access denied",
        ]

        for phrase in title_phrases:
            if phrase in title:
                return True

        return False

    # ------------------------------------------------------------------
    # Amazon URL / ASIN handling
    # ------------------------------------------------------------------

    def extract_asin(self, url: str) -> str:
        """
        Extract Amazon ASIN from common Amazon URLs.

        Supports:
        /dp/XXXXXXXXXX
        /gp/product/XXXXXXXXXX
        /product-reviews/XXXXXXXXXX
        ?asin=XXXXXXXXXX
        """

        if not url:
            return ""

        patterns = [
            r"/dp/([A-Z0-9]{10})(?:[/?]|$)",
            r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)",
            r"/product-reviews/([A-Z0-9]{10})(?:[/?]|$)",
            r"[?&](?:asin|ASIN)=([A-Z0-9]{10})(?:[&#]|$)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                url,
                re.IGNORECASE
            )

            if match:
                return match.group(1).upper()

        return ""

    def _extract_asin_from_page(
        self,
        soup: BeautifulSoup
    ) -> str:
        """
        Try to extract ASIN from the product page itself when the URL
        does not contain it.
        """

        # Common Amazon hidden input.
        selectors = [
            "#ASIN",
            "input[name='ASIN']",
            "input[name='asin']",
        ]

        for selector in selectors:
            element = soup.select_one(selector)

            if element:
                value = element.get("value", "").strip()

                if re.fullmatch(
                    r"[A-Z0-9]{10}",
                    value,
                    re.IGNORECASE
                ):
                    return value.upper()

        # Sometimes the ASIN appears in page HTML.
        html = str(soup)

        patterns = [
            r'"ASIN"\s*:\s*"([A-Z0-9]{10})"',
            r'"asin"\s*:\s*"([A-Z0-9]{10})"',
            r'data-asin=["\']([A-Z0-9]{10})["\']',
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                html,
                re.IGNORECASE
            )

            if match:
                return match.group(1).upper()

        return ""

    def _resolve_amazon_url(
        self,
        url: str
    ) -> tuple[str, str]:
        """
        Open the supplied Amazon URL with Selenium.

        This is important for short URLs such as:
        https://amazon.in/d/0cEIiuS3

        Selenium follows Amazon's redirect and exposes the final URL.
        """

        if not url:
            raise ValueError(
                "Amazon URL cannot be empty."
            )

        parsed = urlparse(url)

        if "amazon" not in parsed.netloc.lower():
            raise ValueError(
                "The supplied URL does not appear to be an Amazon URL."
            )

        try:
            self.driver.get(url)

            # Give Amazon time to redirect.
            time.sleep(3)

        except Exception as exc:
            raise RuntimeError(
                f"Failed to open Amazon URL: {exc}"
            ) from exc

        final_url = self.driver.current_url or url

        asin = self.extract_asin(final_url)

        # If ASIN is still not available from the URL, inspect the page.
        if not asin:
            soup = BeautifulSoup(
                self.driver.page_source,
                "html.parser"
            )

            asin = self._extract_asin_from_page(
                soup
            )

        if not asin:
            raise ValueError(
                "Could not find an Amazon ASIN. "
                "The URL may be invalid, Amazon may have blocked the "
                "request, or the page may not be a product page."
            )

        return final_url, asin

    # ------------------------------------------------------------------
    # Price handling
    # ------------------------------------------------------------------

    def get_clean_price(
        self,
        price_str: str
    ) -> float:
        """
        Convert an Amazon price string to float.

        Examples:
        ₹1,499.00 -> 1499.0
        $29.99 -> 29.99
        1,299 -> 1299.0
        """

        if not price_str:
            return 0.0

        value = self._clean_text(
            price_str
        )

        value = re.sub(
            r"[^\d.]",
            "",
            value
        )

        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _extract_price_from_selectors(
        self,
        soup: BeautifulSoup,
        selectors: list
    ) -> float:
        """
        Try multiple Amazon price selectors.
        """

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if not text:
                    continue

                price = self.get_clean_price(
                    text
                )

                if price > 0:
                    return price

        return 0.0

    def _extract_price_from_fraction_parts(
        self,
        soup: BeautifulSoup
    ) -> float:
        """
        Extract price when Amazon splits whole/fraction values.
        """

        whole_element = soup.select_one(
            ".a-price .a-price-whole"
        )

        fraction_element = soup.select_one(
            ".a-price .a-price-fraction"
        )

        if not whole_element:
            return 0.0

        whole = self._clean_text(
            whole_element.get_text(
                " ",
                strip=True
            )
        )

        fraction = (
            self._clean_text(
                fraction_element.get_text(
                    " ",
                    strip=True
                )
            )
            if fraction_element
            else "00"
        )

        whole = re.sub(
            r"[^\d]",
            "",
            whole
        )

        fraction = re.sub(
            r"[^\d]",
            "",
            fraction
        )

        if not whole:
            return 0.0

        try:
            return float(
                f"{whole}.{fraction[:2] or '00'}"
            )
        except ValueError:
            return 0.0

    def _extract_original_price(
        self,
        soup: BeautifulSoup,
        current_price: float
    ) -> float:
        """
        Extract original/list price where available.
        """

        selectors = [
            "#basisPrice .a-offscreen",
            ".basisPrice .a-offscreen",
            "#corePriceDisplay_desktop_feature_div "
            ".a-text-price .a-offscreen",
            "#corePrice_feature_div "
            ".a-text-price .a-offscreen",
            ".a-text-price .a-offscreen",
        ]

        prices = []

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                price = self.get_clean_price(
                    text
                )

                if price > 0:
                    prices.append(price)

        unique_prices = []

        for price in prices:
            if price not in unique_prices:
                unique_prices.append(price)

        for price in unique_prices:
            if (
                current_price > 0
                and price > current_price
            ):
                return price

        return current_price

    # ------------------------------------------------------------------
    # Product metadata
    # ------------------------------------------------------------------

    def _extract_product_rating(
        self,
        soup: BeautifulSoup
    ):
        """
        Extract overall Amazon product rating.
        """

        selectors = [
            "#acrPopover",
            "span[data-hook='rating-out-of-text']",
            "span.a-icon-alt",
        ]

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements:

                values = [
                    element.get(
                        "title",
                        ""
                    ),
                    element.get(
                        "aria-label",
                        ""
                    ),
                    self._clean_text(
                        element.get_text(
                            " ",
                            strip=True
                        )
                    ),
                ]

                for value in values:

                    if not value:
                        continue

                    match = re.search(
                        r"([0-5](?:\.\d+)?)"
                        r"\s*(?:out of 5|stars?)",
                        value,
                        re.IGNORECASE
                    )

                    if not match:
                        match = re.search(
                            r"([0-5](?:\.\d+)?)",
                            value
                        )

                    if match:

                        try:
                            rating = float(
                                match.group(1)
                            )

                            if 0.0 <= rating <= 5.0:
                                return rating

                        except ValueError:
                            continue

        return None

    def _extract_review_count(
        self,
        soup: BeautifulSoup
    ) -> int:
        """
        Extract total customer review count.
        """

        selectors = [
            "#acrCustomerReviewText",
            "[data-hook='total-review-count']",
        ]

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                match = re.search(
                    r"([\d,]+)",
                    text
                )

                if match:

                    try:
                        return int(
                            match.group(1)
                            .replace(",", "")
                        )

                    except ValueError:
                        continue

        return 0

    def _extract_image_url(
        self,
        soup: BeautifulSoup
    ) -> str:
        """
        Extract main product image.
        """

        selectors = [
            "#landingImage",
            "#imgBlkFront",
            "#ebooksImgBlkFront",
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if not element:
                continue

            image_url = (
                element.get(
                    "data-old-hires"
                )
                or element.get(
                    "src"
                )
                or ""
            )

            if image_url:
                return image_url

            dynamic_image = element.get(
                "data-a-dynamic-image"
            )

            if dynamic_image:

                match = re.search(
                    r'"(https?://[^"]+)"',
                    dynamic_image
                )

                if match:
                    return match.group(1)

        return ""

    def scrape_product_details(
        self,
        url: str
    ) -> dict:
        """
        Scrape Amazon product information.

        Handles both regular product links and short links.
        """

        # --------------------------------------------------------------
        # Resolve short URL and identify ASIN.
        # --------------------------------------------------------------
        final_url, asin = self._resolve_amazon_url(
            url
        )

        # The driver is already on the final URL, but reload once
        # to make sure the product page is fully loaded.
        try:
            if self.driver.current_url != final_url:
                self.driver.get(final_url)
                time.sleep(3)
        except Exception:
            pass

        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser"
        )

        if self._is_blocked_page(soup):
            raise RuntimeError(
                "Amazon returned a CAPTCHA or blocked page. "
                "Product data could not be scraped."
            )

        # --------------------------------------------------------------
        # Product title
        # --------------------------------------------------------------
        title = ""

        title_element = soup.select_one(
            "#productTitle"
        )

        if title_element:
            title = self._clean_text(
                title_element.get_text(
                    " ",
                    strip=True
                )
            )

        # --------------------------------------------------------------
        # Current price
        # --------------------------------------------------------------
        current_price_selectors = [
            "#corePriceDisplay_desktop_feature_div "
            ".priceToPay .a-offscreen",

            "#corePriceDisplay_desktop_feature_div "
            ".a-price .a-offscreen",

            "#corePrice_feature_div "
            ".priceToPay .a-offscreen",

            "#corePrice_feature_div "
            ".a-price .a-offscreen",

            "#apex_desktop "
            ".priceToPay .a-offscreen",

            "#apex_desktop "
            ".a-price .a-offscreen",

            ".priceToPay .a-offscreen",
            ".apexPriceToPay .a-offscreen",
            ".a-price[data-a-color='price'] .a-offscreen",
            ".a-price .a-offscreen",

            "#newBuyBoxPrice",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
        ]

        current_price = (
            self._extract_price_from_selectors(
                soup,
                current_price_selectors
            )
        )

        if current_price == 0.0:
            current_price = (
                self._extract_price_from_fraction_parts(
                    soup
                )
            )

        # --------------------------------------------------------------
        # Original price
        # --------------------------------------------------------------
        original_price = (
            self._extract_original_price(
                soup,
                current_price
            )
        )

        # --------------------------------------------------------------
        # Rating
        # --------------------------------------------------------------
        rating = self._extract_product_rating(
            soup
        )

        # --------------------------------------------------------------
        # Review count
        # --------------------------------------------------------------
        review_count = self._extract_review_count(
            soup
        )

        # --------------------------------------------------------------
        # Image
        # --------------------------------------------------------------
        image_url = self._extract_image_url(
            soup
        )

        return {
            "title": title,
            "current_price": current_price,
            "original_price": original_price,
            "rating": rating,
            "total_reviews_count": review_count,
            "image_url": image_url,
            "asin": asin,
        }

    # ------------------------------------------------------------------
    # Review handling
    # ------------------------------------------------------------------

    def parse_review_date(
        self,
        date_str: str
    ):
        """
        Parse Amazon review date.

        Example:
        Reviewed in India on 15 August 2024
        """

        if not date_str:
            return None

        cleaned = self._clean_text(
            date_str
        )

        match = re.search(
            r"\bon\s+(.+)$",
            cleaned,
            re.IGNORECASE
        )

        target = (
            match.group(1).strip()
            if match
            else cleaned
        )

        try:
            return date_parser.parse(
                target,
                fuzzy=True
            ).date()

        except Exception:
            return None

    def _extract_verified_purchase(
        self,
        card
    ) -> bool:
        """
        Detect Amazon Verified Purchase badge.
        """

        selectors = [
            "span[data-hook='avp-badge']",
            "span.a-color-state",
        ]

        for selector in selectors:

            elements = card.select(
                selector
            )

            for element in elements:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if re.search(
                    r"Verified Purchase",
                    text,
                    re.IGNORECASE
                ):
                    return True

        card_text = self._clean_text(
            card.get_text(
                " ",
                strip=True
            )
        )

        return bool(
            re.search(
                r"\bVerified Purchase\b",
                card_text,
                re.IGNORECASE
            )
        )

    def _extract_review_cards(
        self,
        soup: BeautifulSoup
    ):
        """
        Find Amazon review cards.
        """

        selectors = [
            "div[data-hook='review']",
            "li[data-hook='review']",
        ]

        cards = []

        for selector in selectors:
            cards.extend(
                soup.select(
                    selector
                )
            )

        unique_cards = []
        seen_ids = set()

        for card in cards:

            object_id = id(card)

            if object_id not in seen_ids:

                seen_ids.add(
                    object_id
                )

                unique_cards.append(
                    card
                )

        return unique_cards

    def _extract_review_rating(
        self,
        card
    ) -> float:
        """
        Extract actual review star rating.
        """

        selectors = [
            "i[data-hook='review-star-rating'] "
            "span.a-icon-alt",

            "i[data-hook='cmps-review-star-rating'] "
            "span.a-icon-alt",

            "[data-hook='review-star-rating'] "
            ".a-icon-alt",

            "[data-hook='cmps-review-star-rating'] "
            ".a-icon-alt",
        ]

        for selector in selectors:

            elements = card.select(
                selector
            )

            for element in elements:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                match = re.search(
                    r"([1-5](?:\.\d+)?)"
                    r"\s+out of\s+5",
                    text,
                    re.IGNORECASE
                )

                if match:

                    try:
                        rating = float(
                            match.group(1)
                        )

                        if 1.0 <= rating <= 5.0:
                            return rating

                    except ValueError:
                        continue

        return 0.0

    def _extract_review_title(
        self,
        card
    ) -> str:
        """
        Extract review title.
        """

        selectors = [
            "a[data-hook='review-title'] span",
            "span[data-hook='review-title'] span",
            "[data-hook='review-title']",
        ]

        for selector in selectors:

            element = card.select_one(
                selector
            )

            if element:

                title = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if title:
                    return title

        return ""

    def _extract_review_body(
        self,
        card
    ) -> str:
        """
        Extract review body.
        """

        selectors = [
            "span[data-hook='review-body']",
            "div[data-hook='review-body']",
        ]

        for selector in selectors:

            element = card.select_one(
                selector
            )

            if element:

                text = self._clean_text(
                    element.get_text(
                        " ",
                        strip=True
                    )
                )

                if text:
                    return text

        return ""

    def _extract_reviewer_name(
        self,
        card
    ) -> str:
        """
        Extract reviewer display name.
        """

        element = card.select_one(
            ".a-profile-name"
        )

        if element:

            name = self._clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if name:
                return name[:255]

        return "Amazon Customer"

    def _extract_review_date(
        self,
        card
    ):
        """
        Extract review date.
        """

        element = card.select_one(
            "span[data-hook='review-date']"
        )

        if not element:
            return None

        date_text = self._clean_text(
            element.get_text(
                " ",
                strip=True
            )
        )

        return self.parse_review_date(
            date_text
        )

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    def scrape_reviews(
        self,
        product_url: str,
        max_pages: int = 3
    ) -> list:
        """
        Scrape Amazon customer reviews page by page.

        Supports Amazon short URLs.
        """

        # --------------------------------------------------------------
        # Resolve short URL first.
        # --------------------------------------------------------------
        final_url, asin = self._resolve_amazon_url(
            product_url
        )

        parsed_url = urlparse(
            final_url
        )

        domain = (
            parsed_url.netloc
            or "www.amazon.in"
        )

        if "amazon" not in domain.lower():
            raise ValueError(
                "The supplied URL does not appear to be an Amazon URL."
            )

        reviews = []
        seen_reviews = set()

        # --------------------------------------------------------------
        # Scrape review pages.
        # --------------------------------------------------------------
        for page in range(
            1,
            max_pages + 1
        ):

            review_url = (
                f"https://{domain}"
                f"/product-reviews/{asin}"
                f"?pageNumber={page}"
                f"&sortBy=recent"
            )

            try:
                self.driver.get(
                    review_url
                )

                time.sleep(3)

            except Exception:
                break

            soup = BeautifulSoup(
                self.driver.page_source,
                "html.parser"
            )

            if self._is_blocked_page(
                soup
            ):
                break

            review_cards = (
                self._extract_review_cards(
                    soup
                )
            )

            if not review_cards:
                break

            page_review_count = 0

            for card in review_cards:

                try:
                    reviewer_name = (
                        self._extract_reviewer_name(
                            card
                        )
                    )

                    rating = (
                        self._extract_review_rating(
                            card
                        )
                    )

                    review_title = (
                        self._extract_review_title(
                            card
                        )
                    )

                    review_text = (
                        self._extract_review_body(
                            card
                        )
                    )

                    review_date = (
                        self._extract_review_date(
                            card
                        )
                    )

                    is_verified = (
                        self._extract_verified_purchase(
                            card
                        )
                    )

                    # Ignore empty reviews.
                    if not review_text:
                        continue

                    # Prevent duplicate records.
                    review_key = (
                        reviewer_name.lower().strip(),
                        rating,
                        review_title.lower().strip(),
                        review_text.lower().strip(),
                    )

                    if review_key in seen_reviews:
                        continue

                    seen_reviews.add(
                        review_key
                    )

                    reviews.append({
                        "reviewer_name": (
                            reviewer_name
                            or "Amazon Customer"
                        )[:255],

                        "rating": rating,

                        "review_title": (
                            review_title
                        )[:500],

                        "review_text": review_text,

                        "review_date": review_date,

                        "is_verified_purchase": (
                            is_verified
                        ),
                    })

                    page_review_count += 1

                except Exception:
                    # Ignore a malformed card and continue.
                    continue

            # No usable reviews on this page.
            if page_review_count == 0:
                break

        return reviews