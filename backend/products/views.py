from urllib.parse import urlparse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import ProductDetailSerializer
from .tasks import run_product_analysis


class TriggerAnalysisView(APIView):
    """
    Receives a product URL, validates the platform (Amazon or Flipkart),
    dispatches the Celery task, and returns the task ID.
    POST /api/products/analyze/
    Payload: {"url": "https://www.amazon.in/dp/..."}
    """
    def post(self, request):
        product_url = request.data.get('url')
        if not product_url:
            return Response(
                {"error": "A valid 'url' field is required in the request body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        parsed_url = urlparse(product_url)
        domain = parsed_url.netloc.lower()

        if 'amazon' in domain:
            platform = 'amazon'
        elif 'flipkart' in domain:
            platform = 'flipkart'
        else:
            return Response(
                {"error": "Unsupported platform. Only Amazon and Flipkart URLs are supported."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Dispatch background Celery job
        task = run_product_analysis.delay(product_url)

        return Response({
            "task_id": task.id,
            "platform": platform,
            "websocket_url": f"/ws/progress/{task.id}/",
            "message": "Analysis started in the background."
        }, status=status.HTTP_202_ACCEPTED)


class ProductDetailByUrlView(APIView):
    """
    Lookup a product and its analysis report by URL query parameter.
    Example: /api/products/lookup/?url=https://www.amazon.in/dp/...
    """
    def get(self, request):
        target_url = request.query_params.get('url')
        if not target_url:
            return Response(
                {"error": "The 'url' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = Product.objects.filter(url=target_url).first()
        if not product:
            return Response(
                {"message": "Product not found in cache. Needs scraping."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailByIdView(APIView):
    """
    Retrieve product by primary key ID.
    """
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)