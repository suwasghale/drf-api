from django.utils import timezone
from apps.users.models import UserActivityLog
# from ..models import UserActivityLog

def log_user_activity(user, action):
    """
    Logs user actions for auditing.
    :param user -> User Instance,
    :param action -> Action Description (String) 
    """
    if user and action:
        UserActivityLog.objects.create(
            user = user,
            action = action,
            timestamp = timezone.now()
        )

