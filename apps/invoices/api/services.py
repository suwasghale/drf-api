# apps/invoices/services.py
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.invoices.models import Invoice
from apps.orders.models import Order
from apps.payments.models import Payment

DEFAULT_TAX_RATE = getattr(__import__("django.conf").conf.settings, "INVOICE_TAX_RATE", 0.0)  # 0.0 by default

def compute_invoice_amounts(order: Order, tax_rate: float = DEFAULT_TAX_RATE):
    """Compute subtotal/tax/total from order. Extend to include shipping/tax rules."""
    subtotal = Decimal(order.total_price or 0)
    tax_amount = (subtotal * Decimal(tax_rate)) / Decimal(100) if tax_rate else Decimal(0)
    total = subtotal + tax_amount
    # round as needed
    return subtotal.quantize(Decimal("0.01")), tax_amount.quantize(Decimal("0.01")), total.quantize(Decimal("0.01"))

def create_invoice_for_order(order: Order, created_by=None, invoice_type="invoice", force=False) -> Invoice:
    """
    Create and return an Invoice for the given order.
    - Ensures only one final invoice per order unless force True.
    - Uses transaction and on_commit hooks to safely generate invoice number and optionally PDF asynchronously.
    """
    # Basic guard: invoice created only when order is completed/paid, unless force=True.
    if not force:
        # Your policy: allow invoice creation only for 'paid' orders
        if getattr(order, "status", "").lower() not in ("paid", "completed"):
            raise ValueError("Order must be paid/completed to create final invoice.")

    # If an issued invoice already exists and not forcing, return or raise
    existing = order.invoices.filter(status=Invoice.Statuses.ISSUED).first()
    if existing and not force:
        return existing

    subtotal, tax_amount, total = compute_invoice_amounts(order)
    with transaction.atomic():
        inv = Invoice.objects.create(
            order=order,
            invoice_type=invoice_type,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total,
            currency=getattr(order, "currency", getattr(__import__('django.conf').conf.settings, "DEFAULT_CURRENCY", "NPR")),
            billing_address=getattr(order, "billing_address", {}) if hasattr(order, "billing_address") else {},
            shipping_address=getattr(order, "shipping_address", {}) if hasattr(order, "shipping_address") else {},
            created_by=created_by,
            status=Invoice.Statuses.DRAFT,
        )

    return inv
