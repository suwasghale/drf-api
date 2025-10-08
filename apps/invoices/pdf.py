# apps/invoices/pdf.py
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

from io import BytesIO

# WeasyPrint recommended (pip install weasyprint)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

from apps.invoices.models import Invoice

def render_invoice_html(invoice: Invoice) -> str:
    """Populate the invoice template and return rendered HTML."""
    order = invoice.order
    context = {
        "invoice": invoice,
        "order": order,
        "company": {
            "name": getattr(settings, "COMPANY_NAME", "My Shop"),
            "address": getattr(settings, "COMPANY_ADDRESS", ""),
            "phone": getattr(settings, "COMPANY_PHONE", ""),
            "email": getattr(settings, "COMPANY_EMAIL", ""),
        },
        "generated_at": invoice.issued_at or invoice.created_at,
    }
    html = render_to_string("invoices/invoice.html", context)
    return html
