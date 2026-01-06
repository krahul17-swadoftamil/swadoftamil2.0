from decimal import Decimal, InvalidOperation

from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html

from .models import Ingredient, IngredientStockLedger
from .models_move import IngredientMovement

# ======================================================
# CONSTANTS
# ======================================================

QTY_ZERO = Decimal("0.000")
MONEY_ZERO = Decimal("0.00")
MONEY_UNIT = Decimal("0.01")

LOW_STOCK_LIMITS = {
    "kg": Decimal("1.000"),
    "ltr": Decimal("1.000"),
    "pcs": Decimal("10.000"),
}

# ======================================================
# HELPERS
# ======================================================

def to_decimal(value, default=MONEY_ZERO):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return default


def rupees(value):
    return f"₹{to_decimal(value).quantize(MONEY_UNIT)}"


def get_stock_status(qty, unit):
    qty = to_decimal(qty, QTY_ZERO)
    limit = LOW_STOCK_LIMITS.get(unit, QTY_ZERO)

    if qty <= QTY_ZERO:
        return "Out of Stock", "#e53935"
    if qty <= limit:
        return "Low Stock", "#fb8c00"
    return "In Stock", "#43a047"


# ======================================================
# FORM (THIN — MODEL OWNS RULES)
# ======================================================

class IngredientForm(forms.ModelForm):
    """
    Thin admin form.
    All business validation lives in the model.
    """

    class Meta:
        model = Ingredient
        fields = "__all__"


# ======================================================
# INLINES
# ======================================================

class IngredientMovementInline(admin.TabularInline):
    model = IngredientMovement
    extra = 0
    can_delete = False
    readonly_fields = (
        "change_qty",
        "reason",
        "note",
        "timestamp",
        "resulting_qty",
    )

    ordering = ("-timestamp",)


# ======================================================
# ADMIN
# ======================================================

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    form = IngredientForm
    inlines = (IngredientMovementInline,)

    # -----------------------------
    # LIST VIEW
    # -----------------------------
    list_display = (
        "name",
        "code",
        "unit",
        "category",
        "stock_qty",
        "cost_per_unit",
        "consumed_today",
        "consumed_week",
        "inventory_value_display",
        "stock_badge",
        "is_active",
        "updated_at",
    )

    # Stock is now calculated from ledger - no direct editing
    # list_editable = ("stock_qty", "cost_per_unit")
    search_fields = ("name", "code")
    list_filter = ("unit", "is_active", "category")
    ordering = ("name",)

    # -----------------------------
    # DETAIL VIEW
    # -----------------------------
    readonly_fields = (
        "inventory_value_display",
        "created_at",
        "updated_at",
        "code",
        "stock_qty",
        "stock_status_display",
        "low_stock_alert",
    )

    fieldsets = (
        ("Ingredient", {
            "fields": (
                "name",
                "code",
                "unit",
                "category",
                "preferred_vendor",
                "expiry_days",
                "is_active",
            )
        }),
        ("Inventory & Cost", {
            "fields": (
                "cost_per_unit",
                "fallback_cost_per_unit",
                "inventory_value_display",
                "stock_status_display",
                "low_stock_alert",
            )
        }),
        ("System", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # -----------------------------
    # DISPLAY HELPERS
    # -----------------------------
    @admin.display(description="Inventory Value")
    def inventory_value_display(self, obj):
        return rupees(obj.total_value)

    @admin.display(description="Stock Status")
    def stock_badge(self, obj):
        label, color = get_stock_status(obj.stock_qty, obj.unit)
        return format_html(
            "<b style='color:{}'>{}</b>",
            color,
            label
        )

    @admin.display(description="Consumed Today")
    def consumed_today(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        consumed = obj.stock_ledger.filter(
            change_type="consumption",
            created_at__date=today
        ).aggregate(total=Decimal(0) - models.Sum('quantity_change'))['total'] or 0
        
        return f"{consumed:.3f} {obj.unit}"

    @admin.display(description="Consumed This Week")
    def consumed_week(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        week_ago = timezone.now() - timedelta(days=7)
        consumed = obj.stock_ledger.filter(
            change_type="consumption",
            created_at__gte=week_ago
        ).aggregate(total=Decimal(0) - models.Sum('quantity_change'))['total'] or 0
        
        return f"{consumed:.3f} {obj.unit}"

    @admin.display(description="Stock Status")
    def stock_status_display(self, obj):
        status, color = obj.get_stock_status()
        return format_html(
            "<strong style='color:{};font-size:14px'>{}</strong>",
            color,
            status
        )

    @admin.display(description="⚠️ Low Stock Alert")
    def low_stock_alert(self, obj):
        if obj.is_out_of_stock():
            return format_html(
                "<div style='background:#e53935;color:white;padding:8px;border-radius:4px;font-weight:bold;text-align:center'>"
                "🚨 OUT OF STOCK - REORDER IMMEDIATELY"
                "</div>"
            )
        
        if obj.is_low_stock():
            limit = obj.get_low_stock_limit()
            return format_html(
                "<div style='background:#fb8c00;color:white;padding:8px;border-radius:4px;font-weight:bold;'>"
                "⚠️  LOW STOCK<br/>"
                "<small>Current: {:.3f} {} | Limit: {:.3f} {}</small>"
                "</div>",
                obj.stock_qty, obj.unit,
                limit, obj.unit
            )
        
        return format_html(
            "<div style='background:#43a047;color:white;padding:8px;border-radius:4px;text-align:center;font-weight:bold'>"
            "✓ In Stock"
            "</div>"
        )

    # -----------------------------
    # SAVE HOOK (NO BUSINESS LOGIC)
    # -----------------------------
    def save_model(self, request, obj, form, change):
        """
        Admin should NOT decide business rules.
        Model handles:
        - validation
        - code generation
        - movement logging
        """
        super().save_model(request, obj, form, change)


# ======================================================
# INGREDIENT STOCK LEDGER FORM
# ======================================================

class IngredientStockLedgerForm(forms.ModelForm):
    """
    Restrict change types to prevent manual consumption entries.
    CONSUMPTION must be auto-created from orders only.
    """
    
    class Meta:
        model = IngredientStockLedger
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit change_type choices - exclude CONSUMPTION
        if 'change_type' in self.fields:
            allowed_choices = [
                (IngredientStockLedger.OPENING, "Opening Stock"),
                (IngredientStockLedger.PURCHASE, "Purchase"),
                (IngredientStockLedger.ADJUSTMENT, "Adjustment"),
                (IngredientStockLedger.WASTAGE, "Wastage"),
            ]
            self.fields['change_type'].choices = allowed_choices


# ======================================================
# INGREDIENT STOCK LEDGER ADMIN
# ======================================================

@admin.register(IngredientStockLedger)
class IngredientStockLedgerAdmin(admin.ModelAdmin):
    """
    Complete audit trail for ingredient stock changes.
    Editable on ADD, Read-only on CHANGE (ERP pattern).
    """
    
    form = IngredientStockLedgerForm
    
    list_display = (
        "created_at",
        "ingredient",
        "change_type",
        "quantity_change_display",
        "unit",
        "related_order_link",
        "related_prepared_item",
        "note_short",
    )
    
    list_filter = (
        "change_type",
        "created_at",
        "ingredient",
    )
    
    search_fields = (
        "ingredient__name",
        "note",
        "related_order__order_number",
        "related_prepared_item__name",
    )
    
    ordering = ["-created_at"]
    
    def get_readonly_fields(self, request, obj=None):
        # Allow editing when ADDING
        if obj is None:
            return ("created_at",)
        # Lock everything after save
        return (
            "ingredient",
            "change_type",
            "quantity_change",
            "unit",
            "related_order",
            "related_prepared_item",
            "related_combo",
            "note",
            "created_at",
        )
    
    def has_delete_permission(self, request, obj=None):
        """Ledger entries should never be deleted"""
        return False
    
    # Display methods
    @admin.display(description="Change")
    def quantity_change_display(self, obj):
        sign = "+" if obj.quantity_change >= 0 else ""
        color = "green" if obj.quantity_change >= 0 else "red"
        return format_html(
            f"<strong style='color:{color}'>{sign}{obj.quantity_change} {obj.unit}</strong>"
        )
    
    @admin.display(description="Order")
    def related_order_link(self, obj):
        if obj.related_order:
            return format_html(
                f"<a href='/admin/orders/order/{obj.related_order.id}/change/'>{obj.related_order.order_number}</a>"
            )
        return "-"
    
    @admin.display(description="Note")
    def note_short(self, obj):
        if obj.note:
            return obj.note[:50] + "..." if len(obj.note) > 50 else obj.note
        return "-"
