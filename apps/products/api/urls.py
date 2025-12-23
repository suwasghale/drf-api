from rest_framework.routers import DefaultRouter
from django.urls import path, include

from apps.products.api.views import (
    CategoryViewSet,
    ProductViewSet,
    ProductSpecificationViewSet,
    ReviewViewSet,
)

# Use DRF router for automatic RESTful route registration
router = DefaultRouter()

# Register viewsets
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'specifications', ProductSpecificationViewSet, basename='product-specification')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
