from apps.notifications.models import Notification


def create_notification(user, title, message, notification_type="general", level="info"):
    """
    Simple helper to create a notification for a user.
    """
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        level=level,
    )


def send_order_placed_notification(order):
    create_notification(
        user=order.user,
        title="Order Placed Successfully",
        message=f"Your order #{order.id} has been placed successfully and is now being processed.",
        notification_type="order",
        level="success",
    )


def send_payment_success_notification(payment):
    create_notification(
        user=payment.user,
        title="Payment Successful",
        message=f"Your payment for order #{payment.order.id} was successful.",
        notification_type="payment",
        level="success",
    )


def send_shipment_delivered_notification(shipment):
    create_notification(
        user=shipment.user,
        title="Shipment Delivered",
        message=f"Your shipment for order #{shipment.order.id} has been delivered.",
        notification_type="shipment",
        level="success",
    )


