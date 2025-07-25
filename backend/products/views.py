from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Product
from .serializers import ProductDetailSerializer


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