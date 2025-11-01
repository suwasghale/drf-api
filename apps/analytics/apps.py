from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnalyticsConfig(AppConfig):
    """
    App configuration for Analytics.
    
    Handles generation of reports, sales summaries, user activity tracking,
    and performance metrics across the platform.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = _("Analytics & Insights")

    def ready(self):
        """
        Import signals or background job initializations for analytics tracking.
        """
        try:
            import apps.analytics.signals  # noqa: F401
        except ImportError:
            pass
