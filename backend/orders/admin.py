from decimal import Decimal
from collections import defaultdict

from django.contrib import admin
from django.db import transaction
from django.utils.timezone import now
from django.utils.html import format_html
from django import forms

from .models import Order, OrderCombo, OrderItem
from orders.services import confirm_order, cancel_order


MONEY = Decimal("0.01")


# ======================================================
# CUSTOM FORM — COLORED STATUS DROPDOWN
# ======================================================
class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add colors to status choices
        status_choices = []
        for value, display in Order.STATUS_CHOICES:
            color = {
                Order.STATUS_PLACED: "#fb8c00",
                Order.STATUS_CONFIRMED: "#43a047",
                Order.STATUS_PREPARING: "#2196f3",
                Order.STATUS_OUT_FOR_DELIVERY: "#9c27b0",
                Order.STATUS_DELIVERED: "#4caf50",
                Order.STATUS_CANCELLED: "#e53935",
            }.get(value, "#999")
            status_choices.append((value, f"● {display}"))
        self.fields['status'].choices = status_choices

# ======================================================
# INLINE — ORDER COMBOS (READ-ONLY SNAPSHOT)
# ======================================================
class OrderComboInline(admin.TabularInline):
    model = OrderCombo
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("combo", "quantity")
    readonly_fields = fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("combo")


# ======================================================
# INLINE — ORDER ITEMS (KITCHEN VIEW)
# ======================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("prepared_item", "quantity")
    readonly_fields = fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("prepared_item")


# ======================================================
# FILTER — CREATED TODAY
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
# ORDER ADMIN (ERP-SAFE, IMMUTABLE)
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    ERP rules:
    ✔ Orders are immutable
    ✔ Status changes via services only
    ✔ Kitchen-friendly visibility
    """

    form = OrderAdminForm

    list_display = (
        "order_number",
        "short_id",
        "payment_method",
        "status_badge",
        "age_minutes",
        "total_amount_display",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
        TodayFilter,
    )

    search_fields = (
        "order_number",
        "code",
        "customer_phone",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "id",
        "order_number",
        "code",
        "payment_method",
        "total_amount",
        "customer_name",
        "customer_phone",
        "customer_email",
        "customer_address",
        "created_at",
    )

    inlines = (
        OrderComboInline,
        OrderItemInline,
    )

    def save_model(self, request, obj, form, change):
        # Track status changes
        if change and 'status' in form.changed_data:
            old_status = form.initial.get('status')
            new_status = obj.status
            
            # Create OrderEvent for status change
            from .models import OrderEvent
            OrderEvent.objects.create(
                order=obj,
                action="status_changed",
                note=f"Status changed from {old_status} to {new_status} by admin"
            )
        
        super().save_model(request, obj, form, change)

    actions = (
        "confirm_orders",
        "start_preparing",
        "mark_out_for_delivery", 
        "mark_delivered",
        "cancel_orders",
        "kitchen_view",
    )

    # --------------------------------------------------
    # DISPLAY HELPERS
    # --------------------------------------------------
    @admin.display(description="Order ID")
    def short_id(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            Order.STATUS_PLACED: "#fb8c00",
            Order.STATUS_CONFIRMED: "#43a047",
            Order.STATUS_PREPARING: "#2196f3",
            Order.STATUS_OUT_FOR_DELIVERY: "#9c27b0",
            Order.STATUS_DELIVERED: "#4caf50",
            Order.STATUS_CANCELLED: "#e53935",
        }
        return format_html(
            '<strong style="color:{};">{}</strong>',
            colors.get(obj.status, "#999"),
            obj.get_status_display(),
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
        # Orders must come from API / POS only
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent manual edits (immutability)
        return True

    def has_delete_permission(self, request, obj=None):
        # Allow delete for audit / admin cleanup only
        return request.user.is_superuser

    # --------------------------------------------------
    # ACTIONS — SERVICE-DRIVEN ONLY
    # --------------------------------------------------
    @admin.action(description="✅ Confirm orders")
    def confirm_orders(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != Order.STATUS_PLACED:
                    skipped += 1
                    continue
                try:
                    order.status = Order.STATUS_CONFIRMED
                    order.save(update_fields=["status"])
                    
                    from .models import OrderEvent
                    OrderEvent.objects.create(
                        order=order,
                        action="confirmed",
                        note="Confirmed by admin"
                    )
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.order_number}: {e}")

        self._notify(request, ok, skipped, failed, "confirmed")

    @admin.action(description="👨‍🍳 Start preparing")
    def start_preparing(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != Order.STATUS_CONFIRMED:
                    skipped += 1
                    continue
                try:
                    order.status = Order.STATUS_PREPARING
                    order.save(update_fields=["status"])
                    
                    from .models import OrderEvent
                    OrderEvent.objects.create(
                        order=order,
                        action="preparing",
                        note="Started preparing by admin"
                    )
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.order_number}: {e}")

        self._notify(request, ok, skipped, failed, "marked as preparing")

    @admin.action(description="🚚 Out for delivery")
    def mark_out_for_delivery(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != Order.STATUS_PREPARING:
                    skipped += 1
                    continue
                try:
                    order.status = Order.STATUS_OUT_FOR_DELIVERY
                    order.save(update_fields=["status"])
                    
                    from .models import OrderEvent
                    OrderEvent.objects.create(
                        order=order,
                        action="out_for_delivery",
                        note="Marked out for delivery by admin"
                    )
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.order_number}: {e}")

        self._notify(request, ok, skipped, failed, "marked as out for delivery")

    @admin.action(description="✅ Mark delivered")
    def mark_delivered(self, request, queryset):
        ok, skipped, failed = 0, 0, []

        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != Order.STATUS_OUT_FOR_DELIVERY:
                    skipped += 1
                    continue
                try:
                    order.status = Order.STATUS_DELIVERED
                    order.save(update_fields=["status"])
                    
                    from .models import OrderEvent
                    OrderEvent.objects.create(
                        order=order,
                        action="delivered",
                        note="Marked as delivered by admin"
                    )
                    ok += 1
                except Exception as e:
                    failed.append(f"{order.order_number}: {e}")

        self._notify(request, ok, skipped, failed, "marked as delivered")

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
                    failed.append(f"{order.order_number}: {e}")

        self._notify(request, ok, skipped, failed, "cancelled")

    @admin.action(description="🍳 Kitchen view (prepared items)")
    def kitchen_view(self, request, queryset):
        """
        Read-only kitchen summary.
        """
        lines = []

        for order in queryset.prefetch_related("order_items__prepared_item"):
            for item in order.order_items.all():
                lines.append(
                    f"{order.order_number} → "
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


# ======================================================
# KITCHEN-ONLY MERGED VIEW (OPTIONAL / SEPARATE ADMIN)
# ======================================================
class MergedOrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    show_change_link = False

    fields = ("item_name", "total_qty")
    readonly_fields = fields

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
                    type("MergedItem", (), {
                        "item_name": name,
                        "total_qty": qty,
                    })
                    for name, qty in merged.items()
                ]

        return FakeFormSet


class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "created_at")
    ordering = ("created_at",)
    inlines = (MergedOrderItemInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False
