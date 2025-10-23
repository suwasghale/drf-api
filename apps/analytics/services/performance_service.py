from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from apps.users.models import User
from apps.orders.models import Order
from apps.analytics.models import PerformanceMetric


def generate_daily_performance_metrics():
    """
    Generate daily KPIs like active users and conversion rate.
    Runs daily via Celery beat or CRON.
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=1)
    end_date = today

    # Count active users (logged in or made orders in last 24h)
    active_users = User.objects.filter(
        Q(last_login__date__range=(start_date, end_date))
        | Q(order__created_at__date__range=(start_date, end_date))
    ).distinct().count()

    total_orders = Order.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).count()

    completed_orders = Order.objects.filter(
        created_at__date__range=(start_date, end_date),
        status="completed",
    ).count()

    conversion_rate = (
        (completed_orders / active_users) * 100 if active_users else 0
    )

    PerformanceMetric.objects.update_or_create(
        date=start_date,
        defaults={
            "active_users": active_users,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "conversion_rate": conversion_rate,
        },
    )

    return {
        "date": start_date.isoformat(),
        "active_users": active_users,
        "conversion_rate": conversion_rate,
    }
