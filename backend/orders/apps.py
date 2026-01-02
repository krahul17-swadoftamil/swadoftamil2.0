from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"               # ✅ Python module
    verbose_name = "Sales Orders" # ✅ Admin display name

    def ready(self):
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
