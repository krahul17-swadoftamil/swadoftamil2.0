from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Core system app.

    Responsibilities:
    - Load custom AdminSite
    - Bootstrap admin UI customizations
    - Hold future system-level logic
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core System"

    def ready(self):
        # Ensure custom AdminSite is loaded before model registration
        import core.admin  # noqa: F401
