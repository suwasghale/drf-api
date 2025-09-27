from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.api.views import CountryViewSet, StateViewSet, AddressViewSet

# Create router instance
router = DefaultRouter()

# Register endpoints
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'states', StateViewSet, basename='state')
router.register(r'addresses', AddressViewSet, basename='address')

# Combine into urlpatterns
urlpatterns = [
    path('', include(router.urls)),
]
