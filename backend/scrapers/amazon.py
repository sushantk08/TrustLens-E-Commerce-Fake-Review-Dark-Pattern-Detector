import re
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .base import BaseScraper


class AmazonScraper(BaseScraper):
    """
    Scraper for Amazon product information and publicly visible reviews.

    Supports:
    - Normal Amazon product URLs
    - Amazon short URLs such as https://amzn.in/d/XXXXXXXX
    - Amazon India product pages
    - Amazon review cards embedded on product pages
    """

    # ==============================================================
    # GENERAL HELPERS
    # ==============================================================

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

    def _is_amazon_domain(self, host: str) -> bool:
        """
        Check whether hostname belongs to Amazon or amzn.in.
        """

        host = (
            host or ""
        ).lower().strip()

        if not host:
            return False

        if (
            host == "amzn.in"
            or host.endswith(".amzn.in")
        ):
            return True

        if re.match(
            r"^(?:[\w-]+\.)*amazon\.[a-z.]+$",
            host
        ):
            return True

        return False

    def _is_blocked_page(
        self,
        soup: BeautifulSoup
    ) -> bool:
        """
        Detect common Amazon CAPTCHA or blocked pages.
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

    # ==============================================================
    # AMAZON URL / ASIN
    # ==============================================================

    def extract_asin(
        self,
        url: str
    ) -> str:
        """
        Extract Amazon ASIN from a URL.

        Supported:
            /dp/B0XXXXXXXX
            /gp/product/B0XXXXXXXX
            /product-reviews/B0XXXXXXXX
            ?asin=B0XXXXXXXX
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
        Extract ASIN directly from page HTML.
        """

        selectors = [
            "#ASIN",
            "input[name='ASIN']",
            "input[name='asin']",
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if not element:
                continue

            value = (
                element.get(
                    "value",
                    ""
                )
                or ""
            ).strip()

            if re.fullmatch(
                r"[A-Z0-9]{10}",
                value,
                re.IGNORECASE
            ):
                return value.upper()

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
        Resolve normal Amazon URLs and Amazon short URLs.

        Example:

        https://amzn.in/d/XXXXXXXX
                    ↓
        https://www.amazon.in/dp/B0XXXXXXXX
                    ↓
        ASIN
        """

        if not url:
            raise ValueError(
                "Amazon URL cannot be empty."
            )

        parsed = urlparse(
            url
        )

        host = parsed.netloc.lower()

        if not self._is_amazon_domain(
            host
        ):
            raise ValueError(
                "The supplied URL does not appear to be an Amazon URL."
            )

        # ----------------------------------------------------------
        # Open URL.
        # ----------------------------------------------------------
        try:

            self.driver.get(
                url
            )

            time.sleep(4)

        except Exception as exc:

            raise RuntimeError(
                f"Failed to open Amazon URL: {exc}"
            ) from exc

        # ----------------------------------------------------------
        # Get redirected URL.
        # ----------------------------------------------------------
        final_url = (
            self.driver.current_url
            or url
        )

        # ----------------------------------------------------------
        # Try ASIN from final URL.
        # ----------------------------------------------------------
        asin = self.extract_asin(
            final_url
        )

        # ----------------------------------------------------------
        # Try ASIN from original URL.
        # ----------------------------------------------------------
        if not asin:

            asin = self.extract_asin(
                url
            )

        # ----------------------------------------------------------
        # Try ASIN from page HTML.
        # ----------------------------------------------------------
        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser"
        )

        if not asin:

            asin = self._extract_asin_from_page(
                soup
            )

        # ----------------------------------------------------------
        # Detect blocked page.
        # ----------------------------------------------------------
        if self._is_blocked_page(
            soup
        ):
            raise RuntimeError(
                "Amazon returned a CAPTCHA or blocked page."
            )

        if not asin:

            raise ValueError(
                "Could not find an Amazon ASIN. "
                "The URL may be invalid, Amazon may have blocked "
                "the request, or the short URL did not resolve "
                "to a product page."
            )

        return final_url, asin

    # ==============================================================
    # PRICE
    # ==============================================================

    def get_clean_price(
        self,
        price_str: str
    ) -> float:
        """
        Convert an Amazon price string to float.
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
            return float(
                value
            )
        except (
            ValueError,
            TypeError
        ):
            return 0.0

    def _extract_price_from_selectors(
        self,
        soup: BeautifulSoup,
        selectors: list
    ) -> float:
        """
        Try multiple price selectors.
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
        Extract price when whole and fraction are separate.
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
        Extract original/list price.
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
                    prices.append(
                        price
                    )

        unique_prices = []

        for price in prices:

            if price not in unique_prices:
                unique_prices.append(
                    price
                )

        for price in unique_prices:

            if (
                current_price > 0
                and price > current_price
            ):
                return price

        return current_price

    # ==============================================================
    # PRODUCT INFORMATION
    # ==============================================================

    def _extract_product_rating(
        self,
        soup: BeautifulSoup
    ):
        """
        Extract overall product rating.
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

                    if not match:
                        continue

                    try:

                        rating = float(
                            match.group(1)
                        )

                        if (
                            0.0
                            <= rating
                            <= 5.0
                        ):
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

                if not match:
                    continue

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
        Scrape Amazon product details.
        """

        final_url, asin = (
            self._resolve_amazon_url(
                url
            )
        )

        try:

            if self.driver.current_url != final_url:

                self.driver.get(
                    final_url
                )

                time.sleep(3)

        except Exception:
            pass

        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser"
        )

        if self._is_blocked_page(
            soup
        ):
            raise RuntimeError(
                "Amazon returned a CAPTCHA or blocked page. "
                "Product data could not be scraped."
            )

        # ----------------------------------------------------------
        # Product title
        # ----------------------------------------------------------
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

        # ----------------------------------------------------------
        # Current price
        # ----------------------------------------------------------
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

            ".a-price[data-a-color='price'] "
            ".a-offscreen",

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

        # ----------------------------------------------------------
        # Original price
        # ----------------------------------------------------------
        original_price = (
            self._extract_original_price(
                soup,
                current_price
            )
        )

        # ----------------------------------------------------------
        # Rating
        # ----------------------------------------------------------
        rating = (
            self._extract_product_rating(
                soup
            )
        )

        # ----------------------------------------------------------
        # Review count
        # ----------------------------------------------------------
        review_count = (
            self._extract_review_count(
                soup
            )
        )

        # ----------------------------------------------------------
        # Image
        # ----------------------------------------------------------
        image_url = (
            self._extract_image_url(
                soup
            )
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

    # ==============================================================
    # REVIEW DATE
    # ==============================================================

    def parse_review_date(
        self,
        date_str: str
    ):
        """
        Parse Amazon review dates.

        Example:
            Reviewed in India on 4 September 2026
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

    # ==============================================================
    # REVIEW HELPERS
    # ==============================================================

    def _extract_review_cards(
        self,
        soup: BeautifulSoup
    ):
        """
        Find Amazon review cards.

        The current Amazon page exposes eight review containers
        through data-hook="review".
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

    def _extract_reviewer_name(
        self,
        card
    ) -> str:
        """
        Extract reviewer name.

        Current Amazon structure:
        span.a-profile-name
        """

        selectors = [
            "span.a-profile-name",
            ".a-profile-name",
        ]

        for selector in selectors:

            element = card.select_one(
                selector
            )

            if not element:
                continue

            name = self._clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if name:
                return name[:255]

        return "Amazon Customer"

    def _extract_review_rating(
        self,
        card
    ) -> float:
        """
        Extract actual review rating.

        Current Amazon structure:
        i[data-hook="review-star-rating"]
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

                values = [
                    self._clean_text(
                        element.get_text(
                            " ",
                            strip=True
                        )
                    ),
                    element.get(
                        "title",
                        ""
                    ),
                    element.get(
                        "aria-label",
                        ""
                    ),
                ]

                for value in values:

                    if not value:
                        continue

                    match = re.search(
                        r"([1-5](?:\.\d+)?)"
                        r"\s+out of\s+5",
                        value,
                        re.IGNORECASE
                    )

                    if not match:

                        match = re.search(
                            r"([1-5](?:\.\d+)?)",
                            value
                        )

                    if not match:
                        continue

                    try:

                        rating = float(
                            match.group(1)
                        )

                        if (
                            1.0
                            <= rating
                            <= 5.0
                        ):
                            return rating

                    except ValueError:

                        continue

        return 0.0

    def _extract_review_title(
        self,
        card
    ) -> str:
        """
        Extract actual Amazon review title.

        Current Amazon structure:
        data-hook="reviewTitle"

        Amazon sometimes displays a generic "Review" heading
        when there is no meaningful review title. In that case
        we return an empty string.
        """

        selectors = [
            "[data-hook='reviewTitle']",
            "h5[data-hook='reviewTitle']",
        ]

        for selector in selectors:

            element = card.select_one(
                selector
            )

            if not element:
                continue

            title = self._clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if not title:
                continue

            # "Review" is a generic label, not a real review title.
            if title.strip().lower() == "review":
                return ""

            return title[:500]

        return ""

    def _extract_review_body(
        self,
        card
    ) -> str:
        """
        Extract the actual review body.

        Current Amazon structure:

        data-hook="reviewRichContentContainer"
            -> div.a-cardui-body
                -> actual review text

        This avoids including:
        - Brief content visible...
        - Full content visible...
        - Read more
        - Read less
        - Helpful
        - Report
        """

        # ----------------------------------------------------------
        # Current Amazon structure.
        # ----------------------------------------------------------
        rich_container = card.select_one(
            "[data-hook='reviewRichContentContainer']"
        )

        if rich_container:

            body = rich_container.select_one(
                ".a-cardui-body"
            )

            if body:

                text = self._clean_text(
                    body.get_text(
                        " ",
                        strip=True
                    )
                )

                if text:
                    return self._clean_review_body(
                        text
                    )

            # Fallback to rich container itself.
            text = self._clean_text(
                rich_container.get_text(
                    " ",
                    strip=True
                )
            )

            if text:
                return self._clean_review_body(
                    text
                )

        # ----------------------------------------------------------
        # Fallback selectors for older Amazon layouts.
        # ----------------------------------------------------------
        fallback_selectors = [
            "span[data-hook='review-body']",
            "div[data-hook='review-body']",
            "[data-hook='reviewText']",
        ]

        for selector in fallback_selectors:

            element = card.select_one(
                selector
            )

            if not element:
                continue

            body = element.select_one(
                ".a-cardui-body"
            )

            source = (
                body
                if body
                else element
            )

            text = self._clean_text(
                source.get_text(
                    " ",
                    strip=True
                )
            )

            if text:
                return self._clean_review_body(
                    text
                )

        return ""

    def _clean_review_body(
        self,
        text: str
    ) -> str:
        """
        Remove Amazon UI text from the review body.
        """

        if not text:
            return ""

        # Remove Amazon's dynamic teaser messages.
        boilerplate_patterns = [
            r"Brief content visible, "
            r"double tap to read full content\.",

            r"Full content visible, "
            r"double tap to read brief content\.",

            r"\bRead more\b",

            r"\bRead less\b",
        ]

        cleaned = text

        for pattern in boilerplate_patterns:

            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.IGNORECASE
            )

        cleaned = self._clean_text(
            cleaned
        )

        return cleaned

    def _extract_review_date(
        self,
        card
    ):
        """
        Extract review date.

        Current Amazon structure:
        span[data-hook="review-date"]
        """

        selectors = [
            "span[data-hook='review-date']",
            "[data-hook='review-date']",
        ]

        for selector in selectors:

            element = card.select_one(
                selector
            )

            if not element:
                continue

            date_text = self._clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if date_text:

                return self.parse_review_date(
                    date_text
                )

        return None

    def _extract_verified_purchase(
        self,
        card
    ) -> bool:
        """
        Detect Amazon Verified Purchase.

        Current Amazon structure:
        span[data-hook="avp-badge"]
        """

        selectors = [
            "span[data-hook='avp-badge']",
            "[data-hook='avp-badge']",
            "[data-hook='review-badges']",
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

        # Generic fallback.
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

    # ==============================================================
    # REVIEWS
    # ==============================================================

    def scrape_reviews(
        self,
        product_url: str,
        max_pages: int = 3
    ) -> list:
        """
        Extract publicly visible reviews from the Amazon
        product page.

        Amazon currently exposes a small number of review cards
        directly on the product page. We use those cards instead
        of depending on the standalone review URL.
        """

        # ----------------------------------------------------------
        # Resolve URL and ASIN.
        # ----------------------------------------------------------
        final_url, asin = (
            self._resolve_amazon_url(
                product_url
            )
        )

        if not asin:
            raise ValueError(
                "Could not determine Amazon ASIN."
            )

        # ----------------------------------------------------------
        # Make sure product page is loaded.
        # ----------------------------------------------------------
        try:

            if self.driver.current_url != final_url:

                self.driver.get(
                    final_url
                )

                time.sleep(3)

        except Exception:
            pass

        # ----------------------------------------------------------
        # Scroll down to load the review section.
        # ----------------------------------------------------------
        try:

            self.driver.execute_script(
                "window.scrollTo("
                "0, document.body.scrollHeight * 0.60"
                ");"
            )

            time.sleep(2)

            self.driver.execute_script(
                "window.scrollTo("
                "0, document.body.scrollHeight"
                ");"
            )

            time.sleep(3)

        except Exception:
            pass

        # ----------------------------------------------------------
        # Parse final page.
        # ----------------------------------------------------------
        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser"
        )

        if self._is_blocked_page(
            soup
        ):
            return []

        # ----------------------------------------------------------
        # Find actual review cards.
        # ----------------------------------------------------------
        review_cards = (
            self._extract_review_cards(
                soup
            )
        )

        reviews = []
        seen_reviews = set()

        # ----------------------------------------------------------
        # Parse review cards.
        # ----------------------------------------------------------
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

                # --------------------------------------------------
                # Do not save empty reviews.
                # --------------------------------------------------
                if not review_text:
                    continue

                # --------------------------------------------------
                # Do not accept invalid ratings.
                # --------------------------------------------------
                if not (
                    1.0
                    <= rating
                    <= 5.0
                ):
                    continue

                # --------------------------------------------------
                # Duplicate protection.
                # --------------------------------------------------
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

            except Exception:
                # One malformed review must not stop
                # the remaining reviews.
                continue

        return reviews