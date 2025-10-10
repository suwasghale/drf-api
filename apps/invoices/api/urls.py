from rest_framework.routers import DefaultRouter
from django.urls import path, include
from apps.invoices.api.views import InvoiceViewSet

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("", include(router.urls)),
]
