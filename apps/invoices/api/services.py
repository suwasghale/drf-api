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
