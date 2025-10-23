from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone
from apps.analytics.models import SalesReport, PerformanceMetric


CACHE_TIMEOUT = 60 * 60  # 1 hour


def get_cached_sales_summary():
    """
    Fetch cached monthly sales summary if available.
    Otherwise compute and store in cache.
    """
    key = "analytics:monthly_sales_summary"
    data = cache.get(key)

    if not data:
        latest_report = SalesReport.objects.order_by("-date").first()
        if not latest_report:
            return None

        data = {
            "month": latest_report.date.strftime("%B %Y"),
            "total_orders": latest_report.total_orders,
            "total_revenue": latest_report.total_revenue,
            "average_order_value": latest_report.average_order_value,
        }
        cache.set(key, data, CACHE_TIMEOUT)
    return data


