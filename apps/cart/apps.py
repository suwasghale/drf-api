from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CartConfig(AppConfig):
    """
    App configuration for the Cart system.

    Responsible for handling user shopping carts, item additions,
    quantity updates, and synchronization with checkout and orders.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cart"
    verbose_name = _("Shopping Cart")

    def ready(self):
        """
        Hook for importing cart-related signals, 
        like auto-merging guest carts after login.
        """
        try:
            import apps.cart.signals  # noqa: F401
        except ImportError:
            pass
