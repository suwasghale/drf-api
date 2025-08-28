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

# login failed
@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    log_user_activity(
        user=None, 
        action=f"User Login Failed (username = {credentials.get('username')})", 
        request=request, 
        outcome="FAILED")

# Logout Success
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    log_user_activity(user=user, action="User Logged Out", request=request, outcome="SUCCESS")