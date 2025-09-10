from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.payments.models import Payment

@receiver(post_save, sender=Payment)
def update_order_status_on_payment(sender, instance, created, **kwargs):
    """
    Automatically update the associated order's status to 'paid' if the payment is completed
    """
    order = instance.order
    # only update if the payment is completed.
    if instance.status == "completed":
        if order.is_fully_paid:
            order.status = "paid"
        else:
            order.status = 'pending' # still waiting for the full payment
        order.save(update_fields=['status'])