from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from django.core.cache import cache
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.analytics.models import SalesReport
from apps.analytics.api.serializers import SalesReportSerializer
from apps.analytics.services.report_service import generate_monthly_sales_report
from apps.orders.models import Order


class SalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Advanced ViewSet for Sales Reports.
    - Read-only (no creation or deletion)
    - Supports filtering and date-range queries
    - Includes admin-only endpoints for regeneration and summary analytics
    """

    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["date"]
    ordering_fields = ["date", "total_revenue"]
    ordering = ["-date"]


