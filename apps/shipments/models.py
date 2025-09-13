from django.db import models
from django.conf import settings
from apps.orders.models import Order
# Create your models here.
class Shipment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("returned", "Returned"),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipment")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shipments") # Many-To-One relationship with User. A user can have multiple shipments.
    address = models.TextField()
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Nepal")

    courier = models.CharField(max_length=100, blank=True, null=True)  # e.g. DHL, FedEx
    tracking_number = models.CharField(max_length=120, blank=True, null=True, unique=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    estimated_delivery = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shipment #{self.id} for Order {self.order.id}"