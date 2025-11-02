from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DiscountsConfig(AppConfig):
    """
    App configuration for the Discounts system.

    Handles dynamic pricing, coupon validation, and automatic
    promotional discounts applied to carts, orders, or products.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.discounts"
    verbose_name = _("Discounts & Promotions")

    def ready(self):
        """
        Import signals, scheduled tasks, or discount rule registries.
        This ensures discount logic hooks into orders and carts safely.
        """
        try:
            pass
            # import apps.discounts.signals  # noqa: F401
        except ImportError:
            pass
