from django.db.models.signals import post_save # post_save: This is a built-in Django signal that is "sent" after a model's save() method has completed.
from django.dispatch import receiver # receiver: A decorator used to connect a function (the "receiver") to a specific signal.
from apps.payments.models import Payment # Payment: The Django model for payments, which the signal handler will interact with. 
from apps.orders.models import Order # Order: The Django model for orders, which is the "sender" of the signal.

@receiver(post_save, sender = Order) # @receiver(post_save, sender=Order): This decorator registers the create_refund_on_cancel function to be a receiver for the post_save signal. It specifies that it should only listen for signals sent by the Order model.
def create_refund_on_cancel(sender, instance, created, **kwargs):
    """
    Automatically create a refunded Payment record when an order is cancelled.    
    sender: The model class that sent the signal (Order in this case).
    instance: The actual Order instance that was just saved.
    created: A boolean value that is True if a new record was created, and False if an existing one was updated.
    **kwargs: A placeholder to accept any other keyword arguments that the signal may send. 
    """
    if not created and instance.status == "cancelled": 
        # not created: The signal handler will only proceed if an existing order was updated, not if a new one was just created.
         # instance.status == "cancelled": The handler checks if the updated order's status is "cancelled".

        # check if there's any completed payment for this order
        completed_payments = instance.payment.filter(status="completed") 

        for payment in completed_payments:
            # create a refund record for each completed payment
            Payment.objects.create(
                order = instance,
                amount = payment.amount,
                gateway = payment.gateway,
                gateway_ref = payment.gateway_ref,
                status = "refunded",
                gateway_ref = f"Refund for Payment ID {payment.id} of Order ID {instance.id}"
            )