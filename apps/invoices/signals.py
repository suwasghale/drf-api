# apps/invoices/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.payments.models import Payment
from apps.invoices.api.services import create_invoice_for_order

import logging


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance: Payment, created, **kwargs):
    """
    Auto-create invoice when a payment status becomes 'completed'.
    Only for certain gateways/policies; this prevents generating invoices for COD pending.
    """
    try:
        if instance.status == "completed":
            order = instance.order
            # create invoice if order paid/completed
            try:
                create_invoice_for_order(order, created_by=instance.order.user)
            except Exception:
                # swallow: we don't want to break payment logic; log instead
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Failed to create invoice for order %s", order.pk)
    except Exception:
        pass
             
# You can add more signal handlers as needed.
    # swallow all: signals must not break main flow; log instead
    logger = logging.getLogger(__name__)
    logger.exception("Error in payment_post_save signal for Payment %s", instance.pk)  