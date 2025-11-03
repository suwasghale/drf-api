from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the Users app.

    Handles user-related logic such as authentication signals, 
    custom user model initialization, and audit hooks.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'

    def ready(self):
        """
        Load user-related signals and startup logic.
        This ensures custom user profile creation or JWT-related hooks are active.
        """
        try:
            import apps.users.signals  # noqa
        except ImportError:
            # Prevent import errors during collectstatic/migrations
            pass
