from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.addresses.api.views import (
    CountryViewSet,
    StateViewSet,
    AddressViewSet,
)

# DRF Router instance
router = DefaultRouter()

# Register viewsets
router.register("countries", CountryViewSet, basename="countries")
router.register("states", StateViewSet, basename="states")
router.register("addresses", AddressViewSet, basename="addresses")

# Export all router URLs
urlpatterns = [
    path("", include(router.urls)),
]
