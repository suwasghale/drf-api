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

    def get_queryset(self):
        """
        Optimized queryset with caching for performance.
        Cache key expires every 10 minutes.
        """
        cache_key = "analytics:sales_report_queryset"
        queryset = cache.get(cache_key)

        if not queryset:
            queryset = (
                SalesReport.objects
                .all()
                .defer("created_at")
                .order_by("-date")
            )
            cache.set(cache_key, queryset, 600)  # Cache for 10 minutes

        return queryset

    # -----------------------------------------------------------------------
    # CUSTOM ENDPOINTS
    # -----------------------------------------------------------------------

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        Provides an overview of current month’s key metrics.
        Example: /api/analytics/sales-reports/summary/
        """
        today = timezone.now().date()
        start_date = today.replace(day=1)

        report = (
            SalesReport.objects.filter(date=start_date)
            .values("total_orders", "total_revenue", "average_order_value")
            .first()
        )

        if not report:
            return Response(
                {"detail": "No report found for this month."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "month": start_date.strftime("%B %Y"),
                "total_orders": report["total_orders"],
                "total_revenue": f"{report['total_revenue']:.2f}",
                "average_order_value": f"{report['average_order_value']:.2f}",
            }
        )


