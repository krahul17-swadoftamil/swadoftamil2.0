from django.apps import AppConfig


class SnacksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "snacks"                # ✅ Python module
    verbose_name = "Retail Snacks" # ✅ Admin display name
