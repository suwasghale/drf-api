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
    product = models.OneToOneField("product.Product", on_delete=models.CASCADE, related_name="performance")
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


