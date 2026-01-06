from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Orders application configuration.

    - Registers order-related signals
    - Controls admin display name
    - Keeps startup safe (no hard crashes)
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"               # Python app label
    verbose_name = "Sales Orders" # Admin UI label

    def ready(self):
        # Import signals safely to avoid AppRegistryNotReady
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Signals must NEVER break app loading
            pass
