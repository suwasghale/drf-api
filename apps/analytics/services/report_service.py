from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, F, FloatField
from apps.orders.models import Order
from apps.analytics.models import SalesReport


def generate_monthly_sales_report():
    """
    Generate and store the monthly sales summary.
    Should be triggered automatically via Celery or CRON.
    """
    today = timezone.now().date()
    start_date = today.replace(day=1)
    end_date = today

    # Aggregate in database (efficient for large data)
    aggregates = (
        Order.objects.filter(
            created_at__date__range=(start_date, end_date),
            status="completed",
        )
        .aggregate(
            total_orders=Sum(1),
            total_revenue=Sum(F("total_price"), output_field=FloatField()),
            average_order_value=Avg(F("total_price")),
        )
    )

    total_orders = aggregates.get("total_orders") or 0
    total_revenue = aggregates.get("total_revenue") or 0.0
    average_order_value = aggregates.get("average_order_value") or 0.0

    # Store or update report
    SalesReport.objects.update_or_create(
        date=start_date,
        defaults={
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
        },
    )

    return {
        "month": start_date.strftime("%B %Y"),
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
    }
