from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.shipments.models import Shipment
from apps.notifications.services.notification_service import (
    send_order_placed_notification,
    send_payment_success_notification,
    send_shipment_delivered_notification,
)


@receiver(post_save, sender=Order)
def order_created_handler(sender, instance, created, **kwargs):
    if created:
        send_order_placed_notification(instance)


@receiver(post_save, sender=Payment)
def payment_success_handler(sender, instance, **kwargs):
    if instance.status == "paid":
        send_payment_success_notification(instance)


