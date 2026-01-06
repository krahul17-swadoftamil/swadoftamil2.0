from django.contrib import admin
from django.utils.html import format_html
from .models import StoreStatus, StoreShift, StoreException


@admin.register(StoreStatus)
class StoreStatusAdmin(admin.ModelAdmin):
    list_display = (
        "current_status_display",
        "shift_info_display",
        "closing_time_display",
        "next_shift_display",
        "manual_override_display",
        "accept_orders",
        "kitchen_active",
        "note",
        "updated_at",
    )

    list_display_links = ("current_status_display",)

    list_editable = ("accept_orders", "kitchen_active")

    readonly_fields = (
        "current_status_display",
        "shift_info_display", 
        "closing_time_display",
        "next_shift_display",
        "manual_override_display",
        "updated_at"
    )

    fieldsets = (
        ("Current Status", {
            "description": "Real-time store status overview",
            "fields": (
                "current_status_display",
                "shift_info_display",
                "closing_time_display", 
                "next_shift_display",
                "manual_override_display"
            ),
        }),
        ("Master Switch Control", {
            "description": "Emergency override. Turn OFF to force close store.",
            "fields": ("is_enabled", "note"),
        }),
        ("Operational Control", {
            "description": "Fine-grained control during operation hours.",
            "fields": ("accept_orders", "kitchen_active"),
        }),
        ("System", {
            "fields": ("updated_at",),
        }),
    )

    def has_add_permission(self, request):
        # allow only ONE row
        return not StoreStatus.objects.exists()

    # ======================================================
    # DISPLAY HELPERS
    # ======================================================
    @admin.display(description="Status")
    def current_status_display(self, obj):
        from .utils import is_store_open, can_accept_orders
        from .models import StoreException
        
        is_open = is_store_open()
        can_accept = can_accept_orders()
        
        # Check for calendar exception
        exception = StoreException.get_exception_for_today()
        if exception:
            if exception.is_closed:
                return format_html(
                    f"<div style='background:#f44336;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                    f"🔴 CLOSED (Calendar: {exception.note or 'Exception'})"
                    "</div>"
                )
            else:
                return format_html(
                    f"<div style='background:#2196f3;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                    f"🔵 OPEN (Calendar: {exception.note or 'Exception'})"
                    "</div>"
                )
        
        # Normal logic
        if not obj.is_enabled:
            return format_html(
                "<div style='background:#f44336;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                "🔴 CLOSED (Master Switch OFF)"
                "</div>"
            )
        elif is_open and can_accept:
            current_shift = StoreShift.current_shift()
            shift_name = f" ({current_shift.name})" if current_shift else ""
            return format_html(
                f"<div style='background:#4caf50;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                f"🟢 OPEN{shift_name}"
                "</div>"
            )
        elif is_open and not can_accept:
            return format_html(
                "<div style='background:#ff9800;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                "🟡 STORE OPEN (Not Accepting Orders)"
                "</div>"
            )
        else:
            return format_html(
                "<div style='background:#9e9e9e;color:white;padding:8px 12px;border-radius:6px;text-align:center;font-weight:bold'>"
                "⚪ CLOSED (Outside Hours)"
                "</div>"
            )

    @admin.display(description="Current Shift")
    def shift_info_display(self, obj):
        current_shift = StoreShift.current_shift()
        if current_shift:
            return format_html(
                f"<strong>{current_shift.name}</strong><br>"
                f"<small>{current_shift.start_time.strftime('%H:%M')} – {current_shift.end_time.strftime('%H:%M')}</small>"
            )
        return "No active shift"

    @admin.display(description="Closes At")
    def closing_time_display(self, obj):
        current_shift = StoreShift.current_shift()
        if current_shift:
            return f"⏰ {current_shift.end_time.strftime('%H:%M')}"
        return "—"

    @admin.display(description="Next Shift")
    def next_shift_display(self, obj):
        from .utils import next_opening_time
        next_time = next_opening_time()
        if next_time:
            # Find the shift that starts at next_time
            next_shift = StoreShift.objects.filter(
                is_active=True, 
                start_time=next_time
            ).first()
            if next_shift:
                return format_html(
                    f"🔜 {next_shift.name}<br>"
                    f"<small>{next_shift.start_time.strftime('%H:%M')} – {next_shift.end_time.strftime('%H:%M')}</small>"
                )
        return "—"

    @admin.display(description="Manual Override")
    def manual_override_display(self, obj):
        if obj.is_enabled:
            return format_html("<span style='color:#4caf50;font-weight:bold'>✓ ON</span>")
        else:
            return format_html("<span style='color:#f44336;font-weight:bold'>✗ OFF</span>")


# ======================================================
# STORE SHIFT ADMIN
# ======================================================

@admin.register(StoreShift)
class StoreShiftAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "time_range",
        "cutoff_info",
        "is_active_badge",
        "is_active",
        "is_currently_active_badge",
        "updated_at",
    )

    list_editable = ("is_active",)

    list_filter = ("is_active", "created_at")

    readonly_fields = (
        "is_currently_active_badge",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Shift Details", {
            "fields": ("name", "start_time", "end_time", "cutoff_minutes", "is_active"),
        }),
        ("Status", {
            "fields": ("is_currently_active_badge", "cutoff_info"),
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # ======================================================
    # DISPLAY HELPERS
    # ======================================================
    @admin.display(description="Time Range")
    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} – {obj.end_time.strftime('%H:%M')}"

    @admin.display(description="Active?")
    def is_active_badge(self, obj):
        color = "#43a047" if obj.is_active else "#999999"
        text = "✓ Active" if obj.is_active else "⊗ Inactive"
        return format_html(
            f"<strong style='color:{color}'>{text}</strong>"
        )

    @admin.display(description="Currently Running?")
    def is_currently_active_badge(self, obj):
        if obj.is_currently_active:
            return format_html(
                "<div style='background:#4caf50;color:white;padding:6px 12px;border-radius:4px;text-align:center;font-weight:bold'>"
                "🟢 RUNNING NOW"
                "</div>"
            )
        else:
            return format_html(
                "<div style='background:#999;color:white;padding:6px 12px;border-radius:4px;text-align:center;'>"
                "⊗ Not Running"
                "</div>"
            )

    @admin.display(description="Order Cutoff")
    def cutoff_info(self, obj):
        cutoff_time = obj._get_cutoff_time()
        return f"Orders until {cutoff_time.strftime('%H:%M')} ({obj.cutoff_minutes}min buffer)"


# ======================================================
# STORE EXCEPTION ADMIN (CALENDAR)
# ======================================================

@admin.register(StoreException)
class StoreExceptionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "is_closed",
        "status_display",
        "note",
        "is_today_badge",
        "created_at",
    )

    list_editable = ("is_closed", "note")

    list_filter = ("is_closed", "date")

    ordering = ["-date"]

    fieldsets = (
        ("Exception Details", {
            "fields": ("date", "is_closed", "note"),
        }),
        ("Status", {
            "fields": ("is_today_badge",),
        }),
        ("System", {
            "fields": ("created_at",),
        }),
    )

    readonly_fields = ("is_today_badge", "created_at")

    # ======================================================
    # DISPLAY HELPERS
    # ======================================================
    @admin.display(description="Status")
    def status_display(self, obj):
        if obj.is_closed:
            return format_html(
                "<span style='color:#f44336;font-weight:bold'>🔴 CLOSED</span>"
            )
        else:
            return format_html(
                "<span style='color:#2196f3;font-weight:bold'>🔵 OPEN</span>"
            )

    @admin.display(description="Today?")
    def is_today_badge(self, obj):
        from django.utils import timezone
        today = timezone.localdate()
        if obj.date == today:
            return format_html(
                "<div style='background:#ff9800;color:black;padding:4px 8px;border-radius:4px;text-align:center;font-weight:bold'>"
                "📅 TODAY"
                "</div>"
            )
        return "—"
