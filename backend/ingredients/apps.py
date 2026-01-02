from django.apps import AppConfig


class IngredientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingredients"              # ✅ Python app path
    verbose_name = "Raw Ingredients"  # ✅ Admin display name
