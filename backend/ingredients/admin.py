from decimal import Decimal, InvalidOperation
from django.contrib import admin, messages
from django import forms
from django.utils.html import format_html
from django.conf import settings

from .models import Ingredient
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
# FORMS
# ======================================================
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        for k, v in cleaned.items():
            setattr(self.instance, k, v)
        self.instance.clean()
        return cleaned

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

# ======================================================
# ADMIN
# ======================================================
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    form = IngredientForm
    inlines = (IngredientMovementInline,)

    list_display = (
        "name",
        "code",
        "unit",
        "category",
        "stock_qty",
        "cost_per_unit",
        "inventory_value_display",
        "stock_badge",
        "updated_at",
    )

    list_editable = ("stock_qty", "cost_per_unit")
    search_fields = ("name",)
    list_filter = ("unit", "is_active")
    ordering = ("name",)

    readonly_fields = (
        "inventory_value_display",
        "created_at",
        "updated_at",
        "code",
    )

    fieldsets = (
        ("Ingredient", {
            "fields": ("name", "code", "unit", "category", "preferred_vendor", "is_active")
        }),
        ("Inventory & Cost", {
            "fields": (
                "stock_qty",
                "cost_per_unit",
                "fallback_cost_per_unit",
                "expiry_days",
                "inventory_value_display",
            )
        }),
        ("System", {
            "fields": ("created_at", "updated_at")
        }),
    )

    @admin.display(description="Inventory Value")
    def inventory_value_display(self, obj):
        return rupees(obj.total_value)

    @admin.display(description="Stock")
    def stock_badge(self, obj):
        label, color = get_stock_status(obj.stock_qty, obj.unit)
        return format_html("<b style='color:{}'>{}</b>", color, label)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
