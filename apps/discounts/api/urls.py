from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.discounts.api.views import DiscountViewSet, DiscountRedemptionViewSet

router = DefaultRouter()
router.register(r"discounts", DiscountViewSet, basename="discount")
router.register(r"redemptions", DiscountRedemptionViewSet, basename="discount-redemption")

urlpatterns = [
    path("", include(router.urls)),
]
