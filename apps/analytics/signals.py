from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.products.models import Review
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


@receiver(post_save, sender=Payment)
def log_payment_activity(sender, instance, created, **kwargs):
    if created and instance.status == "completed":
        UserActivity.objects.create(
            user=instance.user,
            activity_type="payment_completed",
            reference_id=str(instance.id),
            metadata={"amount": float(instance.amount)},
        )


@receiver(post_save, sender=Review)
def update_product_performance(sender, instance, created, **kwargs):
    perf, _ = ProductPerformance.objects.get_or_create(product=instance.product)
    perf.total_reviews = instance.product.reviews.count()
    perf.average_rating = instance.product.reviews.aggregate(avg=models.Avg("rating"))["avg"] or 0
    perf.save(update_fields=["total_reviews", "average_rating"])
