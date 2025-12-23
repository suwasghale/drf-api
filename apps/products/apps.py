from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ProductConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    label = 'products'
    verbose_name = _("Product Management")

    def ready(self):
        import apps.products.signals  # Ensure signals are imported when the app is ready
