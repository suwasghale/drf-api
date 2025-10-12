from django.db import models
from django.conf import settings

class DiscountRedemption(models.Model):
    """
    Tracks which user used which discount and when.
    Useful for per-user limits, analytics, refunds.
    """
    discount = models.ForeignKey("discounts.Discount", on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discount_redemptions")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="discount_redemptions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # how much discount was applied
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["discount", "user"]),
        ]
        unique_together = ("discount", "user", "order")  # prevent duplicates for same order
