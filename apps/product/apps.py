from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ProductConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.product'
    label = 'product'
    verbose_name = _("Product Management")

    def ready(self):
        import apps.product.signals  # Ensure signals are imported when the app is ready
