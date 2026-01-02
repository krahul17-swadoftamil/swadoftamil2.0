"""
Serializers for menu app (ERP-aligned, read-only).

Principles:
- Ingredient is the only cost source
- PreparedItem = 1 production + selling unit
- Combo = customer product
- All calculations explicit
- Decimal-safe (strings)
- Frontend-safe image fields
"""

from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers

from ingredients.models import Ingredient
from menu.models import (
    PreparedItem,
    PreparedItemRecipe,
    Combo,
    ComboItem,
)

ZERO = Decimal("0.00")
Q2 = Decimal("0.01")


# ======================================================
# HELPERS
# ======================================================

def money(value) -> str:
    """Return decimal as string with 2dp."""
    try:
        return str(
            Decimal(value or ZERO).quantize(Q2, rounding=ROUND_HALF_UP)
        )
    except Exception:
        return "0.00"


def abs_image_url(context, image_field):
    """
    Safe absolute image URL resolver.
    Never crashes if request/context missing.
    """
    if not image_field:
        return None

    try:
        url = image_field.url
    except Exception:
        return None

    request = context.get("request") if isinstance(context, dict) else None
    return request.build_absolute_uri(url) if request else url


# ======================================================
# INGREDIENT (ERP READ-ONLY)
# ======================================================

class IngredientSerializer(serializers.ModelSerializer):
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "unit",
            "stock_qty",
            "cost_per_unit",
            "min_stock_level",
            "total_value",
        )
        read_only_fields = fields

    def get_total_value(self, obj):
        return money(getattr(obj, "total_value", None))


# ======================================================
# PREPARED ITEM RECIPE (INGREDIENT TRUTH)
# ======================================================

class PreparedItemRecipeSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.UUIDField(
        source="ingredient.id", read_only=True
    )
    ingredient_name = serializers.CharField(
        source="ingredient.name", read_only=True
    )
    ingredient_unit = serializers.CharField(
        source="ingredient.unit", read_only=True
    )
    ingredient_cost = serializers.SerializerMethodField()

    class Meta:
        model = PreparedItemRecipe
        fields = (
            "ingredient_id",
            "ingredient_name",
            "ingredient_unit",
            "quantity",
            "quantity_unit",
            "ingredient_cost",
        )
        read_only_fields = fields

    def get_ingredient_cost(self, obj):
        return money(obj.ingredient_cost())


# ======================================================
# PREPARED ITEM (SELLABLE UNIT)
# ======================================================

class PreparedItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    selling_price = serializers.SerializerMethodField()
    cost_price = serializers.SerializerMethodField()

    class Meta:
        model = PreparedItem
        fields = (
            "id",
            "name",
            "description",
            "unit",
            "serving_size",
            "selling_price",   # ✅ REQUIRED FOR MRP
            "cost_price",
            "image",           # ✅ canonical frontend field
            "images",
            "is_active",
        )
        read_only_fields = fields

    def get_image(self, obj):
        return abs_image_url(self.context, obj.main_image)

    def get_images(self, obj):
        img = self.get_image(obj)
        return [img] if img else []

    def get_selling_price(self, obj):
        return money(obj.selling_price)

    def get_cost_price(self, obj):
        return money(obj.cost_price_cached)


# ======================================================
# COMBO ITEM (PreparedItem × Quantity)
# ======================================================

class ComboItemSerializer(serializers.ModelSerializer):
    prepared_item_id = serializers.UUIDField(
        source="prepared_item.id", read_only=True
    )
    prepared_item_name = serializers.CharField(
        source="prepared_item.name", read_only=True
    )
    unit = serializers.CharField(
        source="prepared_item.unit", read_only=True
    )

    images = serializers.SerializerMethodField()
    display_quantity = serializers.SerializerMethodField()
    unit_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = ComboItem
        fields = (
            "prepared_item_id",
            "prepared_item_name",
            "unit",
            "quantity",
            "display_quantity",
            "unit_cost",
            "total_cost",
            "images",
        )
        read_only_fields = fields

    def get_images(self, obj):
        pi = obj.prepared_item
        img = abs_image_url(self.context, pi.main_image) if pi else None
        return [img] if img else []

    def get_display_quantity(self, obj):
        pi = obj.prepared_item
        if not pi or pi.serving_size is None:
            return None
        try:
            val = Decimal(pi.serving_size) * Decimal(obj.quantity)
            return str(val.quantize(Q2, rounding=ROUND_HALF_UP))
        except Exception:
            return None

    def get_unit_cost(self, obj):
        return money(obj.prepared_item.cost_price_cached)

    def get_total_cost(self, obj):
        return money(obj.cost_cached)


# ======================================================
# COMBO SERIALIZER (API CONTRACT)
# ======================================================
class ComboSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    # IMPORTANT: expose numeric values
    selling_price = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    total_cost = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )
    profit = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Combo
        fields = (
            "id",
            "name",
            "description",
            "serve_persons",
            "image",          # canonical frontend field
            "images",
            "selling_price",  # ✅ NUMBER
            "total_cost",     # ✅ NUMBER
            "profit",         # ✅ NUMBER
            "is_active",
            "is_featured",
            "items",
        )
        read_only_fields = fields

    # -------------------------------
    # IMAGES
    # -------------------------------
    def get_image(self, obj):
        return abs_image_url(self.context, obj.main_image)

    def get_images(self, obj):
        img = self.get_image(obj)
        return [img] if img else []

    # -------------------------------
    # ITEMS
    # -------------------------------
    def get_items(self, obj):
        qs = obj.items.order_by("display_order")
        return ComboItemSerializer(
            qs,
            many=True,
            context=self.context,
        ).data
