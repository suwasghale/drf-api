from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from apps.orders.models import Order

class InvoiceQuerySet(models.QuerySet):
    def issued(self):
        return self.filter(status="issued")

class Invoice(models.Model):
    """Flexible invoice record. Can store invoice PDF and billing snapshot."""
    class Types(models.TextChoices):
        INVOICE = "invoice", "Invoice"
        PROFORMA = "proforma", "Proforma"
        CREDIT = "credit_note", "Credit Note"

    class Statuses(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="invoices")
    invoice_type = models.CharField(max_length=30, choices=Types.choices, default=Types.INVOICE)
    invoice_number = models.CharField(max_length=64, unique=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    # snapshot of amounts (to prevent future order changes affecting invoice)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    currency = models.CharField(max_length=10, default=getattr(settings, "DEFAULT_CURRENCY", "NPR"))

    # Billing / Shipping snapshot (serialized to avoid relying on external Address objects)
    billing_address = models.JSONField(default=dict, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)

    pdf = models.FileField(upload_to="invoices/%Y/%m/%d/", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Statuses.choices, default=Statuses.DRAFT)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = InvoiceQuerySet.as_manager()