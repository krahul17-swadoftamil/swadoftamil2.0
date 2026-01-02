from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    PreparedItem,
    PreparedItemRecipe,
    Combo,
    ComboItem,
)

ZERO = Decimal("0.00")


# ======================================================
# COMMON HELPERS
# ======================================================

def rupees(value):
    try:
        return f"₹{Decimal(value):.2f}" if value is not None else "—"
    except Exception:
        return "—"


def image_tag(url, size=60, radius=10, shadow=False):
    if not url:
        return "—"

    shadow_css = "box-shadow:0 6px 16px rgba(0,0,0,.35);" if shadow else ""

    return format_html(
        "<img src='{}' style='width:{}px;height:{}px;"
        "object-fit:cover;border-radius:{}px;{}'/>",
        url,
        size,
        size,
        radius,
        shadow_css,
    )


# ======================================================
# PREPARED ITEM → INGREDIENT INLINE
# ======================================================

class PreparedItemRecipeInline(admin.TabularInline):
    """
    Ingredient truth for ONE unit of PreparedItem.
    ERP authoritative.
    """
    model = PreparedItemRecipe
    extra = 1
    min_num = 1
    validate_min = True

    autocomplete_fields = ("ingredient",)
    fields = ("ingredient", "quantity", "quantity_unit")


# ======================================================
# PREPARED ITEM ADMIN
# ======================================================

@admin.register(PreparedItem)
class PreparedItemAdmin(admin.ModelAdmin):
    """
    PreparedItem:
    - NOT directly sellable
    - Used inside Combos
    - Owns cost & serving truth
    """

    list_display = (
        "image_thumb",
        "code",
        "name",
        "unit",
        "serving_size",
        "recipe_version",
        "selling_price",
        "cost_price_cached",
        "margin_view",
        "is_active",
    )

    list_filter = ("is_active", "unit")
    search_fields = ("name",)
    ordering = ("name",)

    readonly_fields = (
        "cost_price_cached",
        "image_preview",
        "margin_view",
        "code",
        "recipe_version",
    )

    inlines = (PreparedItemRecipeInline,)

    fieldsets = (
        (
            "Prepared Item",
            {
                "fields": (
                    "name",
                    "code",
                    "description",
                    "unit",
                    "serving_size",
                    "recipe_version",
                    "protein_per_unit",
                    "selling_price",
                    "main_image",
                    "image_preview",
                    "is_active",
                )
            },
        ),
        (
            "ERP (Read Only)",
            {
                "fields": (
                    "cost_price_cached",
                    "margin_view",
                )
            },
        ),
    )

    # ---------------- DISPLAY ----------------

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=44,
            radius=8,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=180,
            radius=16,
            shadow=True,
        )

    @admin.display(description="Margin")
    def margin_view(self, obj):
        if obj.cost_price_cached <= ZERO:
            return "—"

        margin = obj.selling_price - obj.cost_price_cached
        color = "green" if margin >= ZERO else "red"

        return format_html(
            "<strong style='color:{}'>{}</strong>",
            color,
            rupees(margin),
        )


# ======================================================
# COMBO → PREPARED ITEM INLINE
# ======================================================

class ComboItemInline(admin.TabularInline):
    """
    Combo composition:
    PreparedItem × quantity
    """
    model = ComboItem

    extra = 1
    min_num = 1
    validate_min = True

    autocomplete_fields = ("prepared_item",)
    ordering = ("display_order",)

    fields = (
        "prepared_item",
        "display_order",
        "quantity",
        "cost_cached",
        "preview",
    )

    readonly_fields = ("cost_cached", "preview")

    @admin.display(description="Item")
    def preview(self, obj):
        pi = obj.prepared_item
        if pi and pi.main_image:
            return image_tag(
                pi.main_image.url,
                size=56,
                radius=8,
            )
        return "—"


# ======================================================
# COMBO ADMIN
# ======================================================

@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    """
    Combo:
    - ONLY customer sellable product
    - Price controlled here
    - ERP-safe cost aggregation
    """

    list_display = (
        "image_thumb",
        "name",
        "code",
        "serve_persons",
        "serving_unit",
        "serving_size",
        "combo_version",
        "selling_price",
        "total_cost_view",
        "profit_view",
        "is_active",
        "is_featured",
    )

    list_filter = ("is_active", "is_featured")
    search_fields = ("name", "code")
    ordering = ("name",)

    readonly_fields = (
        "image_preview",
        "total_cost_view",
        "profit_view",
        "code",
        "combo_version",
    )

    inlines = (ComboItemInline,)

    fieldsets = (
        (
            "Combo",
            {
                "fields": (
                    "name",
                    "description",
                    "serve_persons",
                    "serving_unit",
                    "serving_size",
                    "combo_version",
                    "code",
                    "main_image",
                    "image_preview",
                    "is_active",
                    "is_featured",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "selling_price",
                    "total_cost_view",
                    "profit_view",
                )
            },
        ),
    )

    # ---------------- DISPLAY ----------------

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=44,
            radius=8,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=180,
            radius=16,
            shadow=True,
        )

    @admin.display(description="Total Cost")
    def total_cost_view(self, obj):
        return rupees(obj.total_cost)

    @admin.display(description="Profit")
    def profit_view(self, obj):
        profit = obj.profit
        color = "green" if profit >= ZERO else "red"

        return format_html(
            "<strong style='color:{}'>{}</strong>",
            color,
            rupees(profit),
        )
