from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.analytics.views import SalesReportViewSet

# ---------------------------------------------------------------------
# ROUTER SETUP
# ---------------------------------------------------------------------
router = DefaultRouter()
router.register(r"sales-reports", SalesReportViewSet, basename="sales-report")

# ---------------------------------------------------------------------
# URL PATTERNS
# ---------------------------------------------------------------------
urlpatterns = [
    path("", include(router.urls)),
]
