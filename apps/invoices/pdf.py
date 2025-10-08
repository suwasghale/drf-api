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

def generate_invoice_pdf_bytes(invoice: Invoice) -> bytes:
    """Return PDF bytes for given invoice."""
    html_string = render_invoice_html(invoice)

    if WEASYPRINT_AVAILABLE:
        # Base url helps with static files resolution
        base_url = settings.STATIC_ROOT or settings.BASE_DIR
        html = HTML(string=html_string, base_url=base_url)
        # Optionally pass CSS
        css_path = getattr(settings, "INVOICE_PDF_CSS", None)
        if css_path:
            css = CSS(filename=css_path)
            pdf_bytes = html.write_pdf(stylesheets=[css])
        else:
            pdf_bytes = html.write_pdf()
        return pdf_bytes
    else:
        # Fallback minimal PDF using reportlab if WeasyPrint is not installed
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.drawString(72, 800, f"Invoice: {invoice.invoice_number}")
        p.drawString(72, 780, f"Order: {invoice.order.id}")
        p.drawString(72, 760, f"Total: {invoice.total_amount} {invoice.currency}")
        p.showPage()
        p.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

# Celery scheduling helper (task lives in apps.invoices.tasks)
def schedule_generate_invoice_pdf(invoice_id: int):
    """Schedule PDF generation via Celery if available, else generate sync."""
    try:
        from apps.invoices.tasks import generate_invoice_pdf_task
        # If Celery is configured, this will push task to broker (async)
        generate_invoice_pdf_task.delay(invoice_id)
    except Exception:
        # fallback: synchronous generation
        invoice = Invoice.objects.get(pk=invoice_id)
        pdf_bytes = generate_invoice_pdf_bytes(invoice)
        filename = f"{invoice.invoice_number}.pdf"
        invoice.attach_pdf_bytes(filename, pdf_bytes)
