from rest_framework import serializers
from .models import Product, Review, PriceHistory, AnalysisReport


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'reviewer_name',
            'rating',
            'review_title',
            'review_text',
            'review_date',
            'is_verified_purchase',
            'is_flagged_fake',
            'sentiment_score',
        ]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'price', 'stock_status', 'recorded_at']


class AnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = [
            'id',
            'trust_score',
            'fake_review_percentage',
            'velocity_spike_detected',
            'dark_patterns_detected',
            'aspects_sentiment',
            'summary_reasons',
            'analyzed_at',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    analysis_report = AnalysisReportSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    price_history = PriceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'url',
            'platform',
            'title',
            'current_price',
            'original_price',
            'rating',
            'total_reviews_count',
            'image_url',
            'last_scraped_at',
            'analysis_report',
            'reviews',
            'price_history',
        ]