from django.utils import timezone
from apps.users.models import UserActivityLog
# from ..models import UserActivityLog

def log_user_activity(
        user, 
        action, 
        request=None, 
        outcome='SUCCESS', 
        extra_data=None,
        ip_address=None,
        user_agent=None,
        location=None
        ):
    """
    Logs user actions for auditing with full flexibility.
    :param user -> User Instance,
    :param action -> Action Description (String) 
    :param request: Django HttpRequest (optional, used for IP/User-Agent)
    :param outcome: "SUCCESS" | "FAILURE" | "BLOCKED"
    :param location: Geo/City/Country (optional, str)
    :param extra_data: Additional structured info (dict)
    """
    # Extract user ip/agent from requests only if not provided.
    if request and not ip_address:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
    if request and not user_agent:
        user_agent = request.META.get('HTTP_USER_AGENT', "")

    # capture useful request meta data
    if extra_data is None:
        extra_data = {
            "path": request.path if request else "",
            "method": request.method if request else "",
            
        }
    # derive location if possible
    if ip_address and not location:
        location = "Nepal"

    if user and action:
        UserActivityLog.objects.create(
            user = user,
            action = action,
            timestamp = timezone.now(),
            ip_address = ip_address,
            user_agent = user_agent,
            location = location,
            outcome = outcome,
            extra_data = extra_data or {}
        ) 

