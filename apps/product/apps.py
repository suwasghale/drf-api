from django.apps import AppConfig


class ProductConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.product'
    label = 'product'

    def ready(self):
        import apps.product.signals  # Ensure signals are imported when the app is ready
