from django.db import models
from apps.orders.models import Order
# Create your models here.
class Payment(models.Model):
    GATEWAYS = (
        ("esewa", "eSewa"),
        ("khalti", "Khalti"),
        ("stripe", "Stripe"),
        ("cod", "Cash on Delivery"),
    )

    STATUSES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # ✅ amount actually paid
    gateway = models.CharField(max_length=30, choices=GATEWAYS)
    gateway_ref = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order {self.order.id} via {self.gateway} - {self.status}"