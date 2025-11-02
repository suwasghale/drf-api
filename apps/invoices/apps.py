from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InvoicesConfig(AppConfig):
    """
    App configuration for the Invoices system.

    Responsible for generating, storing, and managing customer
    invoices linked to completed orders and payments.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.invoices"
    verbose_name = _("Invoices & Billing")

    def ready(self):
        """
        Import signals or Celery task initializers for invoice generation.
        Typically triggered after successful payment or order completion.
        """
        try:
            import apps.invoices.signals  # noqa: F401
        except ImportError:
            pass
