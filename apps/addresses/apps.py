from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AddressesConfig(AppConfig):
    """
    App configuration for managing user and shipping addresses.
    
    Provides address-related models such as Country, State, and Address.
    Integrates with Orders and Shipments for consistent address management.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.addresses"
    verbose_name = _("Addresses & Locations")

    def ready(self):
        """
        Import signals for automatic address validation, 
        cleanup, or integration with other apps.
        """
        try:
            import apps.addresses.signals  # noqa: F401
        except ImportError:
            # No signals yet — safe to ignore
            pass
