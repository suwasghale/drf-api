from django.db import models
from django.conf import settings
from apps.product.models import Product
from decimal import Decimal
# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled")
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    # sum of completed payments
    @property 
    def total_paid(self):
        # payments = self.payment.filter(status="completed")
        # return sum(payment.amount for payment in payments)
        return sum((p.amount for p in self.payment.filter(status="completed")), Decimal("0.00"))
    
    # balance still due/to be paid.
    @property
    def balance_due(self):
        return self.total_price - self.total_paid
    
    # check if the order is fully paid
    @property 
    def is_fully_paid(self):
        return self.total_paid >= self.total_price

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # store product price at time of purchase

    def get_total(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.id})"