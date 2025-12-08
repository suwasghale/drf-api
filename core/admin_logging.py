from apps.users.models import UserActivityLog

def log_admin_action(request, obj, action: str, outcome="SUCCESS"):
    UserActivityLog.objects.create(
        user=request.user,
        action_type=action,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
        extra_data={"object_id": obj.id if obj else None},
        outcome=outcome,
    )
