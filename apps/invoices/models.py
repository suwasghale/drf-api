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

    class Meta:
        ordering = ["-issued_at", "-created_at"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["order", "issued_at"]),
        ]

    def __str__(self):
        return self.invoice_number or f"Invoice #{self.pk}"
    
    def generate_invoice_number(self):
        """Create human-friendly invoice number once id exists.
        Format: INVYYYYMMDD000001 (date + zero-padded id)
        """
        date = timezone.now().strftime("%Y%m%d")
        return f"INV{date}{self.pk:06d}"
    
    def mark_issued(self, issued_at=None):
        if issued_at is None:
            issued_at = timezone.now()
        self.issued_at = issued_at
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        self.status = Invoice.Statuses.ISSUED
        self.save(update_fields=["issued_at", "invoice_number", "status", "updated_at"])

    def attach_pdf_bytes(self, filename: str, pdf_bytes: bytes):
        """Save PDF bytes into the FileField (atomic)."""
        if not filename.endswith(".pdf"):
            filename = f"{filename}.pdf"
        path = f"invoices/{self.issued_at.strftime('%Y/%m/%d') if self.issued_at else timezone.now().strftime('%Y/%m/%d')}/{filename}"
        # Save using default storage
        content = ContentFile(pdf_bytes)
        self.pdf.save(path.split("/", 1)[-1], content, save=True)  # Save triggers file store and updates model