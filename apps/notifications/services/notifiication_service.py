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


