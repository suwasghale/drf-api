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

