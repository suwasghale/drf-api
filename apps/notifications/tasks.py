from celery import shared_task
from apps.notifications.services.notification_service import create_notification

@shared_task
def async_create_notification(user_id, title, message, notification_type="general", level="info"):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        create_notification(user, title, message, notification_type, level)
    except User.DoesNotExist:
        pass
