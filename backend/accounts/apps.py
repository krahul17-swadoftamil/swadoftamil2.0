from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"                 # Python app path
    verbose_name = "Accounts & Auth"  # Admin display name

    def ready(self):
        # Import signal handlers to ensure they're registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
