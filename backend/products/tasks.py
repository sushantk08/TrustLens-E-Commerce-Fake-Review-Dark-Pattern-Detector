from datetime import datetime
from celery import shared_task
from django.utils import timezone

from notifications.utils import send_task_progress
from scrapers.amazon import AmazonScraper
from scrapers.flipkart import FlipkartScraper
from analysis.scoring import compute_true_trust_score
from .models import Product, Review, PriceHistory, AnalysisReport


@shared_task(bind=True)
def run_product_analysis(self, product_url):
    task_id = self.request.id
    platform = 'amazon' if 'amazon' in product_url.lower() else 'flipkart'

    # 1. Initialize
    send_task_progress(task_id, step='INIT', progress_percent=10, message='Initializing browser driver...')

    scraper_class = AmazonScraper if platform == 'amazon' else FlipkartScraper

    # 2. Scrape Metadata & Reviews
    try:
        with scraper_class() as scraper:
            send_task_progress(task_id, step='SCRAPING_PRODUCT', progress_percent=25, message='Extracting product details and current pricing...')
            product_data = scraper.scrape_product_details(product_url)

            send_task_progress(task_id, step='SCRAPING_REVIEWS', progress_percent=50, message='Fetching and parsing customer reviews...')
            scraped_reviews = scraper.scrape_reviews(product_url, max_pages=3)
    except Exception as e:
        send_task_progress(task_id, step='FAILED', progress_percent=0, message=f'Scraping failed: {str(e)}')
        return {'status': 'error', 'message': str(e)}

    # 3. Save or Update Product in Database
    product, _ = Product.objects.update_or_create(
        url=product_url,
        defaults={
            'platform': platform,
            'title': product_data.get('title', '')[:500],
            'current_price': product_data.get('current_price') or 0.0,
            'rating': product_data.get('rating'),
            'total_reviews_count': product_data.get('total_reviews_count', len(scraped_reviews)),
            'image_url': product_data.get('image_url', '')[:1000],
            'last_scraped_at': timezone.now(),
        }
    )

    # Save Price History snapshot
    if product.current_price:
        PriceHistory.objects.create(
            product=product,
            price=product.current_price,
            stock_status=''
        )

    # Save Reviews
    for r in scraped_reviews:
        Review.objects.update_or_create(
            product=product,
            reviewer_name=r.get('reviewer_name', 'Anonymous')[:255],
            review_text=r.get('review_text', ''),
            defaults={
                'rating': r.get('rating', 5.0),
                'review_title': r.get('review_title', '')[:500],
                'review_date': r.get('review_date'),
                'is_verified_purchase': r.get('is_verified_purchase', False),
            }
        )

    # 4. Run Analysis Engine
    send_task_progress(task_id, step='ANALYZING', progress_percent=75, message='Analyzing review velocity, semantics, and dark patterns...')

    db_reviews = list(product.reviews.values())
    price_history = list(product.price_history.values())

    analysis_res = compute_true_trust_score(
        reviews=db_reviews,
        price_history=price_history,
        current_price=float(product.current_price or 0.0),
        original_price=float(product.original_price or 0.0)
    )

    # 5. Persist Analysis Report
    AnalysisReport.objects.update_or_create(
        product=product,
        defaults={
            'trust_score': analysis_res['trust_score'],
            'fake_review_percentage': analysis_res['fake_review_percentage'],
            'velocity_spike_detected': analysis_res['velocity_spike_detected'],
            'dark_patterns_detected': analysis_res['dark_patterns_detected'],
            'aspects_sentiment': analysis_res['aspects_sentiment'],
            'summary_reasons': analysis_res['summary_reasons'],
        }
    )

    # 6. Send Completion WebSocket event with final product ID
    send_task_progress(
        task_id,
        step='COMPLETED',
        progress_percent=100,
        message='Analysis complete.',
        data={'product_id': product.id, 'trust_score': analysis_res['trust_score']}
    )

    return {'status': 'success', 'product_id': product.id, 'trust_score': analysis_res['trust_score']}