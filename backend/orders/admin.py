from decimal import Decimal

from django.contrib import admin
from django.db import transaction
from django.utils.timezone import now
from django.utils.html import format_html

from .models import Order, OrderCombo, OrderItem
from orders.services import confirm_order, cancel_order


MONEY = Decimal("0.01")


# ======================================================
# INLINE — ORDER COMBOS (READ-ONLY SNAPSHOT)
# ======================================================
class OrderComboInline(admin.TabularInline):
    """
    Snapshot of combos ordered.
    Immutable.
    """
    model = OrderCombo
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("combo", "quantity")
    readonly_fields = ("combo", "quantity")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("combo")
        )


# ======================================================
# INLINE — ORDER ITEMS (KITCHEN VIEW)
# ======================================================
class OrderItemInline(admin.TabularInline):
    """
    Flattened prepared items for kitchen usage.
    Clean, readable, no overlap.
    """
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("prepared_item", "quantity")
    readonly_fields = ("prepared_item", "quantity")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("prepared_item")
        )


# ======================================================
# FILTER — TODAY
# ======================================================
class TodayFilter(admin.SimpleListFilter):
    title = "Created Today"
    parameter_name = "today"

    def lookups(self, request, model_admin):
        return (("yes", "Today"),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(created_at__date=now().date())
        return queryset


# ======================================================
# ORDER ADMIN (ERP-SAFE)
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Order Admin Rules:
    - Immutable records
    - Service-driven transitions
    - Kitchen-friendly visibility
    """

    list_display = (
        "order_number",
        "short_id",
        "status_badge",
        "age_minutes",
        "total_amount_display",
        "created_at",
    )

    list_filter = (
        "status",
        TodayFilter,
    )

    search_fields = ("id",)
    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "status",
        "total_amount",
        "created_at",
        "order_number",
        "code",
    )

    inlines = (
        OrderComboInline,
        OrderItemInline,
    )

    actions = (
        "confirm_orders",
        "cancel_orders",
        "kitchen_view",
    )

    # --------------------------------------------------
    # DISPLAY HELPERS
    # --------------------------------------------------
    @admin.display(description="Order")
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            Order.STATUS_PENDING: "#fb8c00",
            Order.STATUS_CONFIRMED: "#43a047",
            Order.STATUS_CANCELLED: "#e53935",
        }
        return format_html(
            '<strong style="color:{};">{}</strong>',
            colors.get(obj.status, "#999"),
            obj.status.upper(),
        )

    @admin.display(description="Age")
    def age_minutes(self, obj):
        minutes = int((now() - obj.created_at).total_seconds() / 60)

        if minutes < 10:
            color = "#43a047"
        elif minutes < 30:
            color = "#fb8c00"
        else:
            color = "#e53935"

        return format_html(
            '<span style="color:{};">{} min</span>',
            color,
            minutes,
        )

    @admin.display(description="Total")
    def total_amount_display(self, obj):
        return f"₹{obj.total_amount.quantize(MONEY)}"

    # --------------------------------------------------
    # PERMISSIONS
    # --------------------------------------------------
    def has_add_permission(self, request):
        # Orders must originate from API / POS only
        return False

    def has_delete_permission(self, request, obj=None):
        # Keep delete available for admin audit control
        return True

    # --------------------------------------------------
    # ACTIONS — SERVICE-DRIVEN ONLY
    # --------------------------------------------------
    @admin.action(description="✅ Confirm orders (deduct stock)")
    def confirm_orders(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != Order.STATUS_PENDING:
                    skipped += 1
                    continue
                try:
                    confirm_order(order)
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.id}: {e}")

        self._notify(request, ok, skipped, failed, "confirmed")

    @admin.action(description="❌ Cancel orders (no stock restore)")
    def cancel_orders(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status == Order.STATUS_CANCELLED:
                    skipped += 1
                    continue
                try:
                    cancel_order(order)
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.id}: {e}")

        self._notify(request, ok, skipped, failed, "cancelled")

    @admin.action(description="🍳 Kitchen view (prepared items)")
    def kitchen_view(self, request, queryset):
        """
        Read-only kitchen summary.
        """
        lines = []

        for order in queryset.prefetch_related("items__prepared_item"):
            for item in order.items.all():
                lines.append(
                    f"{str(order.id)[:8]} → "
                    f"{item.prepared_item.name} × {item.quantity}"
                )

        self.message_user(
            request,
            "\n".join(lines) if lines else "No items to show."
        )

    # --------------------------------------------------
    # MESSAGE HELPER
    # --------------------------------------------------
    def _notify(self, request, ok, skipped, failed, action):
        if ok:
            self.message_user(
                request, f"✅ {ok} order(s) {action}."
            )
        if skipped:
            self.message_user(
                request, f"⚠️ {skipped} order(s) skipped."
            )
        if failed:
            self.message_user(
                request,
                "❌ Failed:\n" + "\n".join(failed),
                level="error",
            )

class MergedOrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("item_name", "total_qty")
    readonly_fields = ("item_name", "total_qty")

    def get_queryset(self, request):
        return OrderItem.objects.none()

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)

        class FakeFormSet(FormSet):
            def get_queryset(self_inner):
                merged = defaultdict(int)
                for item in obj.items.select_related("prepared_item"):
                    merged[item.prepared_item.name] += item.quantity

                return [
                    type(
                        "MergedItem",
                        (),
                        {"item_name": k, "total_qty": v},
                    )
                    for k, v in merged.items()
                ]

        return FakeFormSet


# Alternate kitchen-focused admin — do not auto-register here to avoid
# duplicate model registration with the main site. If you need this
# view, register it on a separate AdminSite or use a proxy model.
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at", "order_number")
    ordering = ("created_at",)
    inlines = (MergedOrderItemInline,)

    def has_add_permission(self, request):
        # Allow superusers to add on this special admin view; keep blocked for others
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        # Allow superusers to view/change; kitchen staff can still be read-only
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete here
        return bool(request.user and request.user.is_superuser)