from django.urls import path
from .views import ProductDetailByUrlView, ProductDetailByIdView, TriggerAnalysisView

urlpatterns = [
    path('analyze/', TriggerAnalysisView.as_view(), name='trigger-analysis'),
    path('lookup/', ProductDetailByUrlView.as_view(), name='product-lookup'),
    path('<int:pk>/', ProductDetailByIdView.as_view(), name='product-detail'),
]