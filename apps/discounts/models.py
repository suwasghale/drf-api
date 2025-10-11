from django.db import models
from django.utils import timezone
from django.conf import settings

class Discount(models.Model):
    """
    A reusable coupon/discount model.
    - Supports percentage (0-100) and fixed amount discounts.
    - Tracks usage and limits.
    """
    DISCOUNT_PERCENTAGE = "percentage"
    DISCOUNT_FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_PERCENTAGE, "Percentage"),
        (DISCOUNT_FIXED, "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    # amount semantics:
    # - percentage: 0-100 (store as decimal like 15)
    # - fixed: currency value to subtract
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                          help_text="Minimum order total (before discounts) to allow this coupon")
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="How many times this coupon can be used globally. Null = unlimited")
    used_count = models.PositiveIntegerField(default=0, help_text="How many times this coupon has been used")
    per_user_limit = models.PositiveIntegerField(null=True, blank=True, help_text="How many times a single user may use this coupon. Null = unlimited")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    # optional admin / creator metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active", "valid_until"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.discount_type})"


    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            (self.valid_from <= now <= self.valid_until if self.valid_until else True) and
            (self.used_count < self.usage_limit)
        )
