from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.product.models import Review
from apps.analytics.models import SalesReport, ProductPerformance, UserActivity


@receiver(post_save, sender=Order)
def update_sales_report(sender, instance, created, **kwargs):
    if not created and instance.status != "completed":
        return

    date = timezone.now().date()
    report, _ = SalesReport.objects.get_or_create(date=date)

    report.total_orders += 1
    report.total_revenue += instance.total_price
    report.average_order_value = (
        report.total_revenue / report.total_orders if report.total_orders else 0
    )
    report.save(update_fields=["total_orders", "total_revenue", "average_order_value"])
