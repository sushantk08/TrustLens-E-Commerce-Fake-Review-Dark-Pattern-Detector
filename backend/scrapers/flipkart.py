import re
import time
from bs4 import BeautifulSoup
from .base import BaseScraper
from .normalizer import clean_price_string, parse_relative_date


class FlipkartScraper(BaseScraper):
    """
    Scrapes product metadata and customer reviews from Flipkart listings.
    """

    def scrape_product_details(self, url: str) -> dict:
        self.driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Title
        title_tag = soup.select_one('span.B_NuCI') or soup.select_one('span.VU-ZEz') or soup.select_one('h1')
        title = title_tag.get_text(strip=True) if title_tag else ''

        # Price
        price_tag = soup.select_one('div._30jeq3._16Jk6d') or soup.select_one('div.Nx9bqj.CxhGGd')
        price = clean_price_string(price_tag.get_text(strip=True) if price_tag else '')

        # Rating
        rating_tag = soup.select_one('div._3LWZlK') or soup.select_one('div.XQDdHH')
        rating_match = re.search(r'([\d.]+)', rating_tag.get_text(strip=True) if rating_tag else '')
        rating = float(rating_match.group(1)) if rating_match else None

        # Total review count
        count_tag = soup.select_one('span._2_R_DZ') or soup.select_one('span.Wphh3L')
        review_count = 0
        if count_tag:
            match = re.search(r'([\d,]+)\s+Reviews', count_tag.get_text(strip=True), re.IGNORECASE)
            if match:
                review_count = int(match.group(1).replace(',', ''))

        # Image
        img_tag = soup.select_one('img._396cs4._2amPTt._3qGmMb') or soup.select_one('img.DByuf4')
        image_url = img_tag.get('src', '') if img_tag else ''

        return {
            'title': title,
            'current_price': price,
            'rating': rating,
            'total_reviews_count': review_count,
            'image_url': image_url,
        }

    def scrape_reviews(self, product_url: str, max_pages: int = 3) -> list:
        """
        Navigates to Flipkart reviews section and extracts review cards.
        """
        reviews = []

        # Convert product URL to reviews listing URL if possible
        if '/p/' in product_url:
            review_url = product_url.replace('/p/', '/product-reviews/')
        else:
            review_url = product_url

        for page in range(1, max_pages + 1):
            page_url = f"{review_url}&page={page}" if '?' in review_url else f"{review_url}?page={page}"
            self.driver.get(page_url)
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Flipkart review card classes
            cards = soup.select('div._1AtVbE div._27M-vq') or soup.select('div.col.EPCmJX')

            if not cards:
                break

            for card in cards:
                # Reviewer name
                name_tag = card.select_one('p._2sc7ZR._2V5Rqn') or card.select_one('p._2NsDsF.AwS1CA')
                reviewer_name = name_tag.get_text(strip=True) if name_tag else 'Anonymous'

                # Rating
                star_tag = card.select_one('div._3LWZlK') or card.select_one('div.XQDdHH')
                star_rating = float(star_tag.get_text(strip=True)) if star_tag and star_tag.get_text(strip=True) else 0.0

                # Review title
                title_tag = card.select_one('p._2-N8zT') or card.select_one('p.z9E0IG')
                review_title = title_tag.get_text(strip=True) if title_tag else ''

                # Review text
                body_tag = card.select_one('div.t-ZTKy div') or card.select_one('div.ZmyHeo div')
                review_text = body_tag.get_text(separator=' ', strip=True) if body_tag else ''
                # Remove "READ MORE" button text artifact
                review_text = re.sub(r'READ MORE', '', review_text).strip()

                # Review date
                date_tag = card.select_one('p._2sc7ZR:not(._2V5Rqn)') or card.select_one('p._2NsDsF:not(.AwS1CA)')
                review_date = parse_relative_date(date_tag.get_text(strip=True) if date_tag else '')

                # Certified Buyer badge
                badge_tag = card.select_one('p._2mcLdV') or card.select_one('div._1eDlvI')
                is_verified = 'certified buyer' in (badge_tag.get_text(strip=True).lower() if badge_tag else '')

                if review_text:
                    reviews.append({
                        'reviewer_name': reviewer_name,
                        'rating': star_rating,
                        'review_title': review_title,
                        'review_text': review_text,
                        'review_date': review_date,
                        'is_verified_purchase': is_verified,
                    })

        return reviews