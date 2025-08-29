from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .utils.audit import log_user_activity

USER = get_user_model()

# successful login
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_user_activity(
        user=user, 
        action="User Logged In", 
        request=request, 
        outcome="SUCCESS")

# Logout Success
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    log_user_activity(user=user, action="User Logged Out", request=request, outcome="SUCCESS")


# logout failed
@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Automatically logs failed login attempts.
    If the user exists, the log is linked to the USER.
    If not, user=None, but extra data will contain attempted identifier.
    """
    attempted_user = None
    username = credentials.get('username')

    # Try to get user object if exists
    try:
        attempted_user = USER.objects.get(username=username)
    except USER.DoesNotExist:
        # Try email as identifier fallback
        try:
            attempted_user = USER.objects.get(email__iexact=username)
        except USER.DoesNotExist:
            attempted_user = None

    log_user_activity(
        user=attempted_user,
        action=f"Login failed for identifier '{username}'",
        request=request,
        outcome="FAILURE",
        extra_data={
            "attempted_username": username,
            "request_path": request.path if request else "",
            "request_method": request.method if request else "",
            "ip": request.META.get("REMOTE_ADDR") if request else None,
        }
    )

    # Increment failed attempts for existing user
    if attempted_user:
        attempted_user.failed_login_attempts = getattr(attempted_user, "failed_login_attempts", 0) + 1
        attempted_user.save(update_fields=["failed_login_attempts"])