from django.contrib import admin
from .models import StoreStatus


@admin.register(StoreStatus)
class StoreStatusAdmin(admin.ModelAdmin):
    list_display = (
        "is_open",
        "open_time",
        "close_time",
        "note",
        "updated_at",
    )

    # The first column in `list_display` is used as the link by default.
    # Since `is_open` is editable inline, set `list_display_links` to
    # another field so Django does not raise admin.E124.
    list_display_links = ("open_time",)

    list_editable = ("is_open",)

    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Store Availability", {
            "fields": ("is_open", "note"),
        }),
        ("Daily Timing", {
            "fields": ("open_time", "close_time"),
        }),
        ("System", {
            "fields": ("updated_at",),
        }),
    )

    def has_add_permission(self, request):
        # allow only ONE row
        return not StoreStatus.objects.exists()
