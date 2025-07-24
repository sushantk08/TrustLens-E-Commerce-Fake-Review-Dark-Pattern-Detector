from django.db import models


class Product(models.Model):
    PLATFORM_CHOICES = (
        ('amazon', 'Amazon'),
        ('flipkart', 'Flipkart'),
    )

    url = models.URLField(max_length=1000, unique=True, db_index=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    title = models.CharField(max_length=500, blank=True, default='')
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    total_reviews_count = models.IntegerField(default=0)
    image_url = models.URLField(max_length=1000, blank=True, default='')
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or self.url


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=255, blank=True, default='Anonymous')
    rating = models.FloatField()
    review_title = models.CharField(max_length=500, blank=True, default='')
    review_text = models.TextField()
    review_date = models.DateField(null=True, blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_flagged_fake = models.BooleanField(default=False)
    sentiment_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title[:30]} - {self.rating} stars"


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_status = models.CharField(max_length=100, blank=True, default='')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.product.title[:30]} - {self.price} at {self.recorded_at.strftime('%Y-%m-%d')}"


class AnalysisReport(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='analysis_report')
    trust_score = models.FloatField(default=0.0)  # Range 0 - 100
    fake_review_percentage = models.FloatField(default=0.0)
    velocity_spike_detected = models.BooleanField(default=False)
    dark_patterns_detected = models.JSONField(default=list, blank=True)
    aspects_sentiment = models.JSONField(default=dict, blank=True)
    summary_reasons = models.JSONField(default=list, blank=True)
    analyzed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report: {self.product.title[:30]} (Score: {self.trust_score})"