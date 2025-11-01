from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SupportConfig(AppConfig):
    """
    App configuration for the Support system.

    Handles user support tickets, threaded messages, and attachments.
    Auto-loads signals for ticket lifecycle events (notifications, analytics, etc.).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.support"
    verbose_name = _("Support & Helpdesk")

    def ready(self):
        """
        Import signal handlers on app startup.
        This keeps signals from being imported globally (avoiding circular import issues).
        """
        try:
            import apps.support.signals  # noqa: F401
        except ImportError:
            # No signals yet — safe to ignore
            pass
