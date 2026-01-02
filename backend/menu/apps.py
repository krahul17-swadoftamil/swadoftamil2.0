from django.apps import AppConfig


class MenuConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "menu"                 # ✅ Python app module
    verbose_name = "Kitchen Menu" # ✅ Admin display name
    
    def ready(self):
        # Ensure signal handlers are connected when the app is loaded.
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing app import on startup; surface in logs if needed
            pass
