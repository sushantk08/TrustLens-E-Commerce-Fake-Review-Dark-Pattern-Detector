import re
import time
from urllib.parse import urlparse, parse_qs, urlencode

from bs4 import BeautifulSoup

from .base import BaseScraper
from .normalizer import clean_price_string, parse_relative_date


class FlipkartScraper(BaseScraper):
    

    def dismiss_login_popup(self):
        """
        Dismiss Flipkart login/sign-in popup when it appears.
        """
        selectors = [
            "button._2KpZ6l._2doB4z",
            "span._30XB9F",
            "button._2doB4z",
            "button[aria-label='Close']",
            "button[title='Close']",
        ]

        try:
            for selector in selectors:
                buttons = self.driver.find_elements(
                    "css selector",
                    selector
                )

                for button in buttons:
                    try:
                        if button.is_displayed():
                            button.click()
                            time.sleep(0.5)
                            return
                    except Exception:
                        continue

        except Exception:
            pass

    def get_review_url(self, product_url: str, page: int = 1) -> str:
        

        parsed = urlparse(product_url)
        params = parse_qs(parsed.query)

      
        pid = params.get("pid", [""])[0]

        if not pid:
            match = re.search(
                r"(?:[?&])pid=([^&]+)",
                product_url,
                re.IGNORECASE
            )

            if match:
                pid = match.group(1)

        path = parsed.path.rstrip("/")

        if "/product-reviews/" in path:
            review_path = path

        elif "/p/" in path:
            review_path = path.replace(
                "/p/",
                "/product-reviews/",
                1
            )

        else:
            review_path = f"{path}/product-reviews"

        query_params = {}

        if pid:
            query_params["pid"] = pid

        query_params["page"] = page

        query_string = urlencode(query_params)

        return (
            f"https://{parsed.netloc or 'www.flipkart.com'}"
            f"{review_path}?{query_string}"
        )

    def _get_text(self, element) -> str:
        """
        Safely extract clean text from a BeautifulSoup element.
        """
        if not element:
            return ""

        return re.sub(
            r"\s+",
            " ",
            element.get_text(" ", strip=True)
        ).strip()

    def _extract_rating(self, review_card):
        

        rating_selectors = [
            "div._3LWZlK",
            "div.XQDdHH",
            "[class*='_3LWZlK']",
            "[class*='XQDdHH']",
        ]

        for selector in rating_selectors:
            rating_element = review_card.select_one(selector)

            if not rating_element:
                continue

            text = self._get_text(rating_element)

            # Handles:
            # 5
            # 4
            # 4.5
            # 5 ★
            match = re.search(
                r"(?<!\d)([1-5](?:\.\d)?)\s*(?:★)?",
                text
            )

            if match:
                try:
                    rating = float(match.group(1))

                    if 1.0 <= rating <= 5.0:
                        return rating

                except ValueError:
                    pass

        return 0.0

    def _extract_review_title(self, review_card) -> str:
        """
        Extract the review headline/title.
        """

        title_selectors = [
            "p._2-N8zT",
            "div._2-N8zT",
            "span._2-N8zT",
            "[class*='_2-N8zT']",
        ]

        for selector in title_selectors:
            title_element = review_card.select_one(selector)

            if title_element:
                title = self._get_text(title_element)

                if title:
                    return title

        return ""

    def _extract_review_body(self, review_card) -> str:
       

        body_selectors = [
            "div.t-ZTKy",
            "[class*='t-ZTKy']",
        ]

        for selector in body_selectors:
            body_element = review_card.select_one(selector)

            if body_element:
                text = self._get_text(body_element)

                text = re.sub(
                    r"\bREAD MORE\b",
                    "",
                    text,
                    flags=re.IGNORECASE
                )

                text = re.sub(
                    r"\bREAD LESS\b",
                    "",
                    text,
                    flags=re.IGNORECASE
                )

                text = re.sub(r"\s+", " ", text).strip()

                if text:
                    return text

        # Fallback: look for paragraphs/divs containing meaningful text
        candidates = review_card.find_all(["p", "div"])

        for element in candidates:
            text = self._get_text(element)

            if not text:
                continue

            lowered = text.lower()

            if (
                len(text) >= 15
                and "certified buyer" not in lowered
                and "report abuse" not in lowered
                and "helpful" not in lowered
            ):
                # Avoid treating the title as the body.
                if text != self._extract_review_title(review_card):
                    return text

        return ""

    def _extract_reviewer_name(self, review_card) -> str:
        """
        Extract the reviewer's display name.
        """

        name_selectors = [
            "p._2sc7ZR._2V5EHH",
            "p._2V5EHH",
            "[class*='_2V5EHH']",
        ]

        for selector in name_selectors:
            name_element = review_card.select_one(selector)

            if name_element:
                name = self._get_text(name_element)

                # Sometimes the location/details are inside the same element.
                name = re.split(
                    r"\bCertified Buyer\b",
                    name,
                    flags=re.IGNORECASE
                )[0].strip()

                name = name.rstrip(",").strip()

                if name:
                    return name

        # Fallback
        certified_element = review_card.find(
            string=re.compile(
                r"Certified Buyer",
                re.IGNORECASE
            )
        )

        if certified_element:
            parent = certified_element.parent

            if parent:
                previous = parent.find_previous(
                    ["p", "span", "div"]
                )

                if previous:
                    name = self._get_text(previous)

                    if name:
                        return name

        return "Flipkart Customer"

    def _extract_review_date(self, review_card):
        """
        Extract and normalize review date.

        Supports values such as:
        - Today
        - Yesterday
        - 2 days ago
        - 2 months ago
        - Aug, 2024
        """

        date_selectors = [
            "p._2sc7ZR:not(._2V5EHH)",
            "[class*='_2sc7ZR']",
        ]

        possible_dates = []

        for selector in date_selectors:
            elements = review_card.select(selector)

            for element in elements:
                text = self._get_text(element)

                if text:
                    possible_dates.append(text)

        # Also inspect text around date-like phrases.
        card_text = self._get_text(review_card)

        date_patterns = [
            r"\b\d+\s+days?\s+ago\b",
            r"\b\d+\s+weeks?\s+ago\b",
            r"\b\d+\s+months?\s+ago\b",
            r"\b\d+\s+years?\s+ago\b",
            r"\btoday\b",
            r"\byesterday\b",
            r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
            r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
            r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?),?\s+\d{4}\b",
        ]

        for pattern in date_patterns:
            match = re.search(
                pattern,
                card_text,
                re.IGNORECASE
            )

            if match:
                possible_dates.append(match.group(0))

        # Remove duplicates while preserving order.
        unique_dates = []

        for value in possible_dates:
            value = value.strip()

            if value and value not in unique_dates:
                unique_dates.append(value)

        for date_text in unique_dates:
            parsed_date = parse_relative_date(date_text)

            if parsed_date:
                return parsed_date

        return None

    def _extract_verified_status(self, review_card) -> bool:
        """
        Detect whether Flipkart displays the Certified Buyer badge.
        """

        verified_selectors = [
            "p._2mcZGG",
            "[class*='_2mcZGG']",
        ]

        for selector in verified_selectors:
            element = review_card.select_one(selector)

            if element:
                text = self._get_text(element)

                if re.search(
                    r"certified buyer",
                    text,
                    re.IGNORECASE
                ):
                    return True

        # Generic fallback
        card_text = self._get_text(review_card)

        return bool(
            re.search(
                r"\bCertified Buyer\b",
                card_text,
                re.IGNORECASE
            )
        )

    def _find_review_cards(self, soup):
        """
        Find individual Flipkart review containers.

        We use several known structures because Flipkart changes
        CSS classes periodically.
        """

        selectors = [
            # Common Flipkart review-card structures
            "div._2wzgFH",
            "div._16PBlm",
            "div._16PBlm._3_IKGE",

            # More generic review structures
            "div[class*='_2wzgFH']",
            "div[class*='_16PBlm']",
        ]

        cards = []

        for selector in selectors:
            found = soup.select(selector)

            if found:
                cards.extend(found)

        # Remove duplicate BeautifulSoup objects.
        unique_cards = []
        seen_ids = set()

        for card in cards:
            card_id = id(card)

            if card_id not in seen_ids:
                seen_ids.add(card_id)
                unique_cards.append(card)

        if not unique_cards:

            buyer_nodes = soup.find_all(
                string=re.compile(
                    r"Certified Buyer",
                    re.IGNORECASE
                )
            )

            for buyer_node in buyer_nodes:

                container = buyer_node.parent

                # Move upward through the DOM.
                for _ in range(8):

                    if container is None:
                        break

                    text = self._get_text(container)

                    if (
                        50 <= len(text) <= 2000
                        and (
                            container.select_one("div.t-ZTKy")
                            or container.select_one("p._2-N8zT")
                            or re.search(
                                r"\bCertified Buyer\b",
                                text,
                                re.IGNORECASE
                            )
                        )
                    ):
                        break

                    container = container.parent

                if container is not None:
                    if id(container) not in {
                        id(card) for card in unique_cards
                    }:
                        unique_cards.append(container)

        return unique_cards

    def scrape_product_details(self, url: str) -> dict:
        """
        Scrape product title, current price, original price,
        rating, review count and image.
        """

        self.driver.get(url)
        time.sleep(3)
        self.dismiss_login_popup()

        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser"
        )

        
        title_selectors = [
            "h1 span",
            "h1",
            "span.VU-ZEz",
            "span.B_NuCI",
        ]

        title = ""

        for selector in title_selectors:
            title_tag = soup.select_one(selector)

            if title_tag:
                title = self._get_text(title_tag)

                if title:
                    break

        if not title and soup.title:
            title = self._get_text(soup.title)

        price_values = []

        price_selectors = [
            "div.Nx9bqj",
            "div._30jeq3",
            "div._16Jk6d",
            "[class*='Nx9bqj']",
            "[class*='_30jeq3']",
        ]

        for selector in price_selectors:
            elements = soup.select(selector)

            for element in elements:
                text = self._get_text(element)

                if "₹" in text:
                    price = clean_price_string(text)

                    if price > 0:
                        price_values.append(price)

        # Fallback to currency strings.
        if not price_values:
            currency_strings = soup.find_all(
                string=re.compile(
                    r"₹\s*[\d,]+(?:\.\d+)?"
                )
            )

            for value in currency_strings:
                price = clean_price_string(value)

                if price > 0:
                    price_values.append(price)

        # Remove duplicates while preserving order.
        unique_prices = []

        for price in price_values:
            if price not in unique_prices:
                unique_prices.append(price)

        current_price = unique_prices[0] if unique_prices else 0.0

        
        original_price = current_price

        for price in unique_prices[1:]:
            if price > current_price:
                original_price = price
                break

        rating = None

        rating_selectors = [
            "div.XQDdHH",
            "span.XQDdHH",
            "div._3LWZlK",
            "[class*='XQDdHH']",
            "[class*='_3LWZlK']",
        ]

        for selector in rating_selectors:
            rating_element = soup.select_one(selector)

            if rating_element:
                rating_text = self._get_text(rating_element)

                match = re.search(
                    r"(?<!\d)([1-5](?:\.\d)?)",
                    rating_text
                )

                if match:
                    try:
                        value = float(match.group(1))

                        if 1.0 <= value <= 5.0:
                            rating = value
                            break

                    except ValueError:
                        pass

        # Fallback
        if rating is None:
            rating_strings = soup.find_all(
                string=re.compile(
                    r"^\s*[1-5](?:\.\d)?\s*$"
                )
            )

            for value in rating_strings:
                try:
                    parsed_rating = float(value.strip())

                    if 1.0 <= parsed_rating <= 5.0:
                        rating = parsed_rating
                        break

                except ValueError:
                    continue

        
        review_count = 0

        count_selectors = [
            "span.Wphh3N",
            "span.Wphh3L",
            "span._2_R_DZ",
            "[class*='Wphh3N']",
            "[class*='Wphh3L']",
        ]

        for selector in count_selectors:
            count_elements = soup.select(selector)

            for element in count_elements:
                text = self._get_text(element)

                match = re.search(
                    r"([\d,]+)\s*(?:Reviews?|Ratings?\s*&\s*([\d,]+)\s*Reviews?)",
                    text,
                    re.IGNORECASE
                )

                if match:
                    # Group 1 normally contains review count.
                    try:
                        review_count = int(
                            match.group(1).replace(",", "")
                        )
                        break
                    except ValueError:
                        pass

            if review_count:
                break

        # Generic page-text fallback.
        if review_count == 0:
            page_text = soup.get_text(
                " ",
                strip=True
            )

            match = re.search(
                r"([\d,]+)\s+Reviews?",
                page_text,
                re.IGNORECASE
            )

            if match:
                try:
                    review_count = int(
                        match.group(1).replace(",", "")
                    )
                except ValueError:
                    review_count = 0

        image_url = ""

        image_selectors = [
            "img.DByuf4",
            "img._396cs4",
            "img._2r_T1I",
            "img[src*='flixcart']",
            "img[src*='flipkart']",
        ]

        for selector in image_selectors:
            image_element = soup.select_one(selector)

            if image_element:
                image_url = (
                    image_element.get("src")
                    or image_element.get("data-src")
                    or ""
                )

                if image_url:
                    break

        return {
            "title": title,
            "current_price": current_price,
            "original_price": original_price,
            "rating": rating,
            "total_reviews_count": review_count,
            "image_url": image_url,
        }

    def scrape_reviews(
        self,
        product_url: str,
        max_pages: int = 3
    ) -> list:
        """
        Scrape Flipkart customer reviews page by page.

        Each review contains:
        - reviewer_name
        - rating
        - review_title
        - review_text
        - review_date
        - is_verified_purchase
        """

        reviews = []
        seen_reviews = set()

        for page in range(1, max_pages + 1):

            page_url = self.get_review_url(
                product_url,
                page=page
            )

            try:
                self.driver.get(page_url)
                time.sleep(3)
                self.dismiss_login_popup()

            except Exception:
                break

            soup = BeautifulSoup(
                self.driver.page_source,
                "html.parser"
            )

            page_text = self._get_text(soup).lower()

            
            blocked_messages = [
                "enter the characters you see below",
                "sorry, something went wrong",
                "are you a human",
                "captcha",
                "access denied",
            ]

            if any(
                message in page_text
                for message in blocked_messages
            ):
                break

            review_cards = self._find_review_cards(soup)

            if not review_cards:
                break

            page_review_count = 0

            for card in review_cards:

                try:
                    reviewer_name = self._extract_reviewer_name(
                        card
                    )

                    rating = self._extract_rating(
                        card
                    )

                    review_title = self._extract_review_title(
                        card
                    )

                    review_text = self._extract_review_body(
                        card
                    )

                    review_date = self._extract_review_date(
                        card
                    )

                    is_verified = self._extract_verified_status(
                        card
                    )

                    
                    if not review_text:
                        continue

                    # A review without a valid rating is still possible,
                    # but don't invent a rating.
                    if rating < 0 or rating > 5:
                        rating = 0.0

                    review_key = (
                        reviewer_name.lower().strip(),
                        rating,
                        review_title.lower().strip(),
                        review_text.lower().strip(),
                    )

                    if review_key in seen_reviews:
                        continue

                    seen_reviews.add(review_key)

                    reviews.append({
                        "reviewer_name": (
                            reviewer_name[:255]
                            if reviewer_name
                            else "Flipkart Customer"
                        ),
                        "rating": rating,
                        "review_title": review_title[:500],
                        "review_text": review_text,
                        "review_date": review_date,
                        "is_verified_purchase": is_verified,
                    })

                    page_review_count += 1

                except Exception:
                    # A malformed review should not stop the complete
                    # scraping process.
                    continue

            if page_review_count == 0:
                break

        return reviews