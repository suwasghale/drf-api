from datetime import timedelta
from django.utils import timezone
from apps.orders.models import Order
from apps.analytics.models import SalesReport


def generate_monthly_sales_report():
    today = timezone.now().date()
    start_date = today.replace(day=1)
    end_date = today

    orders = Order.objects.filter(
        created_at__date__range=(start_date, end_date), status="completed"
    )

    total_orders = orders.count()
    total_revenue = sum(o.total_price for o in orders)
    average_order_value = total_revenue / total_orders if total_orders else 0

    SalesReport.objects.update_or_create(
        date=start_date,
        defaults={
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
        },
    )
# This function can be scheduled to run monthly via Celery or a cron job.