from django.urls import path
from .views import ProductDetailByUrlView, ProductDetailByIdView

urlpatterns = [
    path('lookup/', ProductDetailByUrlView.as_view(), name='product-lookup'),
    path('<int:pk>/', ProductDetailByIdView.as_view(), name='product-detail'),
]