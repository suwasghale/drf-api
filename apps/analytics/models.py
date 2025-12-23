from django.db import models
from django.utils import timezone
from django.conf import settings


class SalesReport(models.Model):
    """
    Aggregated daily/monthly revenue and sales metrics.
    Generated automatically via signals or Celery.
    """
    date = models.DateField(db_index=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded_orders = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Sales Report"
        verbose_name_plural = "Sales Reports"
        unique_together = ("date",)
        ordering = ["-date"]

    def __str__(self):
        return f"Sales Report - {self.date}"


class ProductPerformance(models.Model):
    """
    Tracks how each product performs in terms of sales and ratings.
    """
    product = models.OneToOneField("products.Product", on_delete=models.CASCADE, related_name="performance")
    total_sales = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    last_sold_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Product Performance"
        verbose_name_plural = "Product Performances"

    def __str__(self):
        return f"Performance: {self.product.name}"


class UserActivity(models.Model):
    """
    Logs key user activities for analytics & engagement insights.
    """
    ACTIVITY_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("order_created", "Order Created"),
        ("payment_completed", "Payment Completed"),
        ("review_submitted", "Review Submitted"),
        ("wishlist_added", "Wishlist Added"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    reference_id = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"
