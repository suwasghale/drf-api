# apps/invoices/tasks.py
from celery import shared_task
from django.db import transaction

from apps.invoices.models import Invoice
from apps.invoices.pdf import generate_invoice_pdf_bytes

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def generate_invoice_pdf_task(self, invoice_id):
    """
    Celery task: generate PDF bytes and attach to invoice.
    Retries on transient failures.
    """
    try:
        invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
        pdf_bytes = generate_invoice_pdf_bytes(invoice)
        filename = f"{invoice.invoice_number or 'invoice'}_{invoice.pk}.pdf"
        # attach file (saves the instance)
        invoice.attach_pdf_bytes(filename, pdf_bytes)
    except Exception as exc:
        # Optionally implement backoff / alerting
        raise self.retry(exc=exc)
