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
        """Dismiss the Flipkart login modal if present."""
        try:
            close_buttons = self.driver.find_elements(
                "css selector",
                "button._2KpZ6l._2doB4z, span._30XB9F, button._2doB4z",
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
        Builds the older dedicated Flipkart review URL.

        Kept for compatibility with the existing project.
        Current Flipkart review extraction uses the in-page
        Ratings and Reviews panel instead.
        """
        parsed = urlparse(product_url)
        params = parse_qs(parsed.query)

        pid = params.get("pid", [""])[0]

        if not pid:
            match = re.search(
                r"pid=([A-Z0-9]+)",
                product_url,
                re.IGNORECASE,
            )

            if match:
                pid = match.group(1)

        path = parsed.path

        if "/p/" in path:
            review_path = path.replace(
                "/p/",
                "/product-reviews/",
            )

        elif "/product-reviews/" in path:
            review_path = path

        else:
            review_path = path + "/product-reviews"

        query_string = (
            f"pid={pid}&page={page}"
            if pid
            else f"page={page}"
        )

        return (
            f"https://{parsed.netloc}"
            f"{review_path}?{query_string}"
        )

    def scrape_product_details(self, url: str) -> dict:
        """
        Scrape basic product information from the Flipkart
        product page.
        """
        self.driver.get(url)
        time.sleep(3)

        self.dismiss_login_popup()

        soup = BeautifulSoup(
            self.driver.page_source,
            "html.parser",
        )

        # ---------------------------------------------------------
        # 1. Product title
        # ---------------------------------------------------------
        title_tag = (
            soup.select_one("h1 span")
            or soup.select_one("h1")
            or soup.select_one("span.VU-ZEz")
            or soup.select_one("span.B_NuCI")
        )

        if title_tag:
            title = title_tag.get_text(
                strip=True
            )
        elif soup.title:
            title = soup.title.get_text(
                strip=True
            )
        else:
            title = ""

        # ---------------------------------------------------------
        # 2. Current price
        # ---------------------------------------------------------
        prices = [
            text.strip()
            for text in soup.find_all(
                string=re.compile(
                    r"^₹[\d,]+$"
                )
            )
        ]

        current_price = 0.0

        if prices:
            current_price = clean_price_string(
                prices[0]
            )

        # ---------------------------------------------------------
        # 3. Original price / MRP
        # ---------------------------------------------------------
        original_price = current_price

        if len(prices) > 1:
            second_price = clean_price_string(
                prices[1]
            )

            if second_price > current_price:
                original_price = second_price

        # ---------------------------------------------------------
        # 4. Product rating
        # ---------------------------------------------------------
        ratings = [
            text.strip()
            for text in soup.find_all(
                string=re.compile(
                    r"^\d\.\d$"
                )
            )
        ]

        rating = None

        if ratings:
            try:
                rating = float(ratings[0])
            except (ValueError, TypeError):
                rating = None

        # ---------------------------------------------------------
        # 5. Total review count
        #
        # Current Flipkart page displays:
        #
        # 4.5
        # | 1,987
        #
        # The review count is inside the rating link.
        # ---------------------------------------------------------
        review_count = 0

        # Current Flipkart markup
        for link in soup.find_all("a"):
            try:
                link_text = link.get_text(
                    separator=" ",
                    strip=True,
                )

                match = re.search(
                    r"\|\s*([\d,]+)",
                    link_text,
                )

                if match:
                    review_count = int(
                        match.group(1).replace(",", "")
                    )
                    break

            except (ValueError, TypeError):
                continue

        # Fallback for older Flipkart markup
        if review_count == 0:
            count_tag = (
                soup.select_one("span.Wphh3L")
                or soup.select_one("span._2_R_DZ")
            )

            if count_tag:
                match = re.search(
                    r"([\d,]+)\s+Reviews",
                    count_tag.get_text(strip=True),
                    re.IGNORECASE,
                )

                if match:
                    review_count = int(
                        match.group(1).replace(",", "")
                    )

        # ---------------------------------------------------------
        # 6. Product image
        #
        # Prefer actual product images from:
        # rukminim2.flixcart.com/image/...
        #
        # Avoid Flipkart's own logo SVG.
        # ---------------------------------------------------------
        image_url = ""

        # First try actual product image <img> elements.
        product_img = (
            soup.select_one(
                'img[src*="rukminim2.flixcart.com/image/"]'
            )
            or soup.select_one(
                'img[data-src*="rukminim2.flixcart.com/image/"]'
            )
        )

        if product_img:
            image_url = (
                product_img.get("src")
                or product_img.get("data-src")
                or ""
            )

        # Second try other Flipkart image URLs.
        if not image_url:

            for img in soup.find_all("img"):
                src = (
                    img.get("src")
                    or img.get("data-src")
                    or ""
                )

                if (
                    "flixcart.com/image/" in src
                    and not src.endswith(".svg")
                ):
                    image_url = src
                    break

        # Third try preloaded images.
        if not image_url:

            preload_tags = soup.select(
                'link[rel="preload"][as="image"]'
            )

            for tag in preload_tags:

                srcset = tag.get(
                    "imagesrcset",
                    "",
                )

                match = re.search(
                    r"https://[^,\s]+"
                    r"rukminim2\.flixcart\.com/"
                    r"image/[^,\s]+",
                    srcset,
                )

                if match:
                    image_url = match.group(0)
                    break

        return {
            "title": title,
            "current_price": current_price,
            "original_price": original_price,
            "rating": rating,
            "total_reviews_count": review_count,
            "image_url": image_url,
        }

    def _is_relative_date(self, text: str) -> bool:
        """
        Check whether text looks like a Flipkart relative date.
        """
        if not text:
            return False

        return bool(
            re.search(
                r"\b("
                r"today|"
                r"yesterday|"
                r"\d+\s+days?\s+ago|"
                r"\d+\s+weeks?\s+ago|"
                r"\d+\s+months?\s+ago|"
                r"\d+\s+years?\s+ago"
                r")\b",
                text.lower(),
            )
        )

    def _xpath_literal(self, value: str) -> str:
        """
        Safely create an XPath string literal.

        Handles reviewer names containing apostrophes.
        """
        if "'" not in value:
            return f"'{value}'"

        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")

        return (
            "concat("
            + ", \"'\", ".join(
                f"'{part}'"
                for part in parts
            )
            + ")"
        )

    def _extract_reviewer_and_card(
        self,
        verified_element,
    ):
        """
        Find the reviewer name and complete review card.

        Current Flipkart structure:

        Reviewer
            |
        Verified Buyer
            |
        wrapper
            |
        reviewer container
            |
        complete review card
        """
        try:
            # Parent 2 contains:
            #
            # Nirmal C H
            # Verified Buyer
            #
            reviewer_container = (
                verified_element.find_element(
                    "xpath",
                    "../..",
                )
            )

            container_lines = [
                line.strip()
                for line
                in reviewer_container.text.splitlines()
                if line.strip()
            ]

            if not container_lines:
                return None, None

            reviewer_name = ""

            for line in container_lines:
                if line.lower() != "verified buyer":
                    reviewer_name = line
                    break

            if not reviewer_name:
                return None, None

            # Find actual reviewer element.
            reviewer_elements = reviewer_container.find_elements(
                "xpath",
                (
                    ".//*[normalize-space(text())="
                    f"{self._xpath_literal(reviewer_name)}]"
                ),
            )

            if not reviewer_elements:
                return None, None

            reviewer_element = reviewer_elements[0]

            # Reviewer element -> parent 1 -> parent 2
            # -> parent 3 = complete review card
            card = reviewer_element

            for _ in range(3):
                card = card.find_element(
                    "xpath",
                    "..",
                )

            return reviewer_name, card

        except Exception:
            return None, None

    def _parse_review_card(
        self,
        card,
        reviewer_name: str,
    ):
        """
        Parse one Flipkart review card.

        Example structure:

        5
        Brilliant
        5 months ago
        Review text
        Nirmal C H
        Verified Buyer
        256
        57
        """
        try:
            lines = [
                line.strip()
                for line in card.text.splitlines()
                if line.strip()
            ]

            if not lines:
                return None

            # -----------------------------------------------------
            # Find reviewer position
            # -----------------------------------------------------
            reviewer_index = None

            for index, line in enumerate(lines):
                if line == reviewer_name:
                    reviewer_index = index
                    break

            if reviewer_index is None:
                return None

            # -----------------------------------------------------
            # Find rating
            # -----------------------------------------------------
            rating = None
            rating_index = None

            for index, line in enumerate(
                lines[:reviewer_index]
            ):
                match = re.fullmatch(
                    r"([1-5](?:\.\d+)?)",
                    line,
                )

                if match:
                    rating = float(
                        match.group(1)
                    )

                    rating_index = index
                    break

            if rating is None:
                return None

            # -----------------------------------------------------
            # Review title
            # -----------------------------------------------------
            review_title = ""

            if (
                rating_index is not None
                and rating_index + 1 < reviewer_index
            ):
                possible_title = lines[
                    rating_index + 1
                ]

                if not self._is_relative_date(
                    possible_title
                ):
                    review_title = possible_title

            # -----------------------------------------------------
            # Review date
            # -----------------------------------------------------
            review_date = None
            date_index = None

            for index in range(
                rating_index + 1,
                reviewer_index,
            ):
                line = lines[index]

                if self._is_relative_date(
                    line
                ):
                    date_index = index

                    try:
                        review_date = (
                            parse_relative_date(
                                line
                            )
                        )
                    except Exception:
                        review_date = None

                    break

            # -----------------------------------------------------
            # Review text
            # -----------------------------------------------------
            if date_index is not None:
                body_start = date_index + 1
            else:
                body_start = rating_index + 2

            body_lines = lines[
                body_start:reviewer_index
            ]

            cleaned_body = []

            for line in body_lines:

                # Helpful/reaction counters.
                if line in {
                    "256",
                    "57",
                    "Show all reviews",
                }:
                    continue

                # Remove Flipkart's "...more".
                line = re.sub(
                    r"\.\.\.\s*more$",
                    "",
                    line,
                    flags=re.IGNORECASE,
                ).strip()

                if line.lower() == "more":
                    continue

                if line:
                    cleaned_body.append(line)

            # Do not duplicate title inside body.
            cleaned_body = [
                line
                for line in cleaned_body
                if line != review_title
            ]

            review_text = " ".join(
                cleaned_body
            ).strip()

            # -----------------------------------------------------
            # Verified buyer
            # -----------------------------------------------------
            is_verified_purchase = (
                "Verified Buyer" in lines
            )

            return {
                "reviewer_name": reviewer_name,
                "rating": rating,
                "review_title": review_title,
                "review_text": review_text,
                "review_date": review_date,
                "is_verified_purchase": (
                    is_verified_purchase
                ),
            }

        except Exception:
            return None

    def scrape_reviews(
        self,
        product_url: str,
        max_pages: int = 3,
    ) -> list:
        """
        Scrape Flipkart reviews from the current
        Ratings and Reviews bottom-sheet panel.

        Flipkart currently loads reviews dynamically when
        the product rating/review-count link is clicked.
        """
        reviews = []

        try:
            # -----------------------------------------------------
            # 1. Open product page
            # -----------------------------------------------------
            self.driver.get(product_url)
            time.sleep(5)

            self.dismiss_login_popup()

            # -----------------------------------------------------
            # 2. Scroll to rating/review section
            # -----------------------------------------------------
            self.driver.execute_script(
                """
                window.scrollTo(
                    0,
                    document.body.scrollHeight * 0.65
                );
                """
            )

            time.sleep(3)

            # -----------------------------------------------------
            # 3. Find rating/review link
            #
            # Example:
            #
            # 4.5
            # | 1,987
            # -----------------------------------------------------
            review_link = None

            links = self.driver.find_elements(
                "xpath",
                "//a",
            )

            for link in links:

                try:
                    link_text = (
                        link.text
                        .strip()
                        .replace("\n", " ")
                    )

                    has_rating = bool(
                        re.search(
                            r"\b\d+(?:\.\d+)?\b",
                            link_text,
                        )
                    )

                    has_review_count = bool(
                        re.search(
                            r"\|\s*[\d,]+",
                            link_text,
                        )
                    )

                    if (
                        has_rating
                        and has_review_count
                    ):
                        review_link = link
                        break

                except Exception:
                    continue

            if not review_link:
                return reviews

            # -----------------------------------------------------
            # 4. Click rating/review link
            # -----------------------------------------------------
            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center'
                });
                """,
                review_link,
            )

            time.sleep(1)

            self.driver.execute_script(
                "arguments[0].click();",
                review_link,
            )

            time.sleep(3)

            # -----------------------------------------------------
            # 5. Find review bottom sheet
            # -----------------------------------------------------
            panel_elements = self.driver.find_elements(
                "css selector",
                "#msite-bottomsheet",
            )

            if not panel_elements:
                return reviews

            panel = panel_elements[0]

            # -----------------------------------------------------
            # 6. Find Verified Buyer elements
            # -----------------------------------------------------
            verified_elements = panel.find_elements(
                "xpath",
                ".//*[normalize-space(text())='Verified Buyer']",
            )

            seen_reviews = set()

            # -----------------------------------------------------
            # 7. Parse each review
            # -----------------------------------------------------
            for verified_element in verified_elements:

                reviewer_name, card = (
                    self._extract_reviewer_and_card(
                        verified_element
                    )
                )

                if (
                    not reviewer_name
                    or card is None
                ):
                    continue

                review = self._parse_review_card(
                    card,
                    reviewer_name,
                )

                if not review:
                    continue

                # -------------------------------------------------
                # Duplicate protection
                # -------------------------------------------------
                unique_key = (
                    review["reviewer_name"],
                    review["rating"],
                    review["review_title"],
                    review["review_text"],
                )

                if unique_key in seen_reviews:
                    continue

                seen_reviews.add(
                    unique_key
                )

                reviews.append(review)

        except Exception:
            return reviews

        return reviews