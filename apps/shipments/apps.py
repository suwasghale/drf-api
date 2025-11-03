from django.apps import AppConfig


class ShipmentsConfig(AppConfig):
    """
    Configuration class for the Shipments app.

    Responsible for initializing shipment-related logic such as 
    signal registration, third-party integrations (e.g., courier APIs),
    and service setup on app load.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shipments'
    label = 'shipments'

    def ready(self):
        """
        Hook for initializing signals or background processes when Django starts.
        """
        try:
            pass
            # import apps.shipments.signals  # noqa
        except ImportError:
            # Safe import: avoids crashing during migrations
            pass
