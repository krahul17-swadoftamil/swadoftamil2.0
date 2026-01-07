"""
Serializers for menu app (ERP-aligned, read-only).

Principles:
- Ingredient is the only cost source
- PreparedItem = 1 serving unit (not stock)
- Combo = only sellable product
- All values explicit & decimal-safe
- Images are frontend-safe
"""

from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers

from ingredients.models import Ingredient
from menu.models import (
    PreparedItem,
    PreparedItemRecipe,
    Combo,
    ComboItem,
    MarketingOffer,
    SubscriptionPlan,
    Subscription,
)

ZERO = Decimal("0.00")
Q2 = Decimal("0.01")


# ======================================================
# HELPERS
# ======================================================

def money(value) -> str:
    """
    Return decimal as string with 2dp.
    Always safe for frontend.
    """
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

    # Handle context being None or not a dict
    if not context or not isinstance(context, dict):
        return url

    request = context.get("request")
    return request.build_absolute_uri(url) if request else url


# ======================================================
# INGREDIENT (ERP READ-ONLY)
# ======================================================

class IngredientSerializer(serializers.ModelSerializer):
    """
    Ingredient = ERP source of truth (read-only).
    """

    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "unit",
            "stock_qty",
            "cost_per_unit",
            "total_value",
            "is_active",
        )
        read_only_fields = fields

    def get_total_value(self, obj):
        return money(obj.total_value)


# ======================================================
# PREPARED ITEM RECIPE (INGREDIENT TRUTH)
# ======================================================

class PreparedItemRecipeSerializer(serializers.ModelSerializer):
    """
    Ingredient usage for ONE PreparedItem unit.
    """

    ingredient_id = serializers.UUIDField(
        source="ingredient.id", read_only=True
    )
    ingredient_name = serializers.CharField(
        source="ingredient.name", read_only=True
    )
    ingredient_unit = serializers.CharField(
        source="ingredient.unit", read_only=True
    )
    # ingredient_cost = serializers.SerializerMethodField()

    class Meta:
        model = PreparedItemRecipe
        fields = (
            "ingredient_id",
            "ingredient_name",
            "ingredient_unit",
            "quantity",
            "quantity_unit",
            # "ingredient_cost",
        )
        read_only_fields = fields

    # def get_ingredient_cost(self, obj):
    #     return money(obj.ingredient_cost())


# ======================================================
# PREPARED ITEM (SERVING UNIT)
# ======================================================

class PreparedItemSerializer(serializers.ModelSerializer):
    """
    PreparedItem = serving definition used inside combos.
    """

    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
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
            "selling_price",
            "cost_price",
            "image_url",
            "thumbnail_url",
            "images",
            "is_active",
        )
        read_only_fields = fields

    def get_image_url(self, obj):
        return abs_image_url(self.context, obj.main_image)

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL (smaller version for lists/cards)"""
        full_url = self.get_image_url(obj)
        if full_url:
            # For now, return the same URL - can be enhanced with actual thumbnails later
            return full_url
        return None

    def get_images(self, obj):
        img = self.get_image_url(obj)
        return [img] if img else []

    def get_selling_price(self, obj):
        return money(obj.selling_price)

    def get_cost_price(self, obj):
        return money(obj.cost_price_cached)


# ======================================================
# COMBO ITEM (PreparedItem × Quantity)
# ======================================================

class ComboItemSerializer(serializers.ModelSerializer):
    """
    PreparedItem contribution inside a Combo.
    """

    prepared_item_id = serializers.UUIDField(
        source="prepared_item.id", read_only=True
    )
    prepared_item_name = serializers.CharField(
        source="prepared_item.name", read_only=True
    )
    display_text = serializers.CharField(
        source="prepared_item.name", read_only=True
    )
    unit = serializers.CharField(
        source="prepared_item.unit", read_only=True
    )

    images = serializers.SerializerMethodField()
    display_quantity = serializers.SerializerMethodField()
    unit_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    recipe = serializers.SerializerMethodField()

    class Meta:
        model = ComboItem
        fields = (
            "prepared_item_id",
            "prepared_item_name",
            "display_text",
            "unit",
            "quantity",
            "display_quantity",
            "unit_cost",
            "total_cost",
            "images",
            "recipe",
        )
        read_only_fields = fields

    def get_images(self, obj):
        pi = obj.prepared_item
        img = abs_image_url(self.context, pi.main_image) if pi else None
        return [img] if img else []

    def get_display_quantity(self, obj):
        """
        Customer-facing quantity (serving_size × quantity).
        """
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

    def get_recipe(self, obj):
        """
        Return the ingredients used in this prepared item.
        """
        recipe_items = obj.prepared_item.recipe_items.all()
        return PreparedItemRecipeSerializer(
            recipe_items,
            many=True,
        ).data


# ======================================================
# COMBO SERIALIZER (API CONTRACT)
# ======================================================

class ComboSerializer(serializers.ModelSerializer):
    """
    Combo = customer-facing sellable product.
    """

    items = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Combo
        fields = (
            "id",
            "name",
            "description",
            "serve_persons",
            "selling_price",
            "is_active",
            "is_featured",
            "image_url",
            "thumbnail_url",
            "images",
            "items",
        )
        read_only_fields = fields

    def get_image_url(self, obj):
        return abs_image_url(self.context, obj.main_image)

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL (smaller version for lists/cards)"""
        full_url = self.get_image_url(obj)
        if full_url:
            # For now, return the same URL - can be enhanced with actual thumbnails later
            return full_url
        return None

    def get_images(self, obj):
        img = self.get_image_url(obj)
        return [img] if img else []

    def get_items(self, obj):
        qs = obj.items.order_by("display_order")
        return ComboItemSerializer(
            qs,
            many=True,
            context=self.context,
        ).data


# ======================================================
# MARKETING OFFER
# ======================================================

class MarketingOfferSerializer(serializers.ModelSerializer):
    """
    Marketing offers for promotional banners.
    """
    is_currently_active = serializers.ReadOnlyField()

    class Meta:
        model = MarketingOffer
        fields = (
            "id",
            "title",
            "description",
            "short_text",
            "banner_type",
            "discount_percentage",
            "discount_amount",
            "start_date",
            "end_date",
            "priority",
            "is_currently_active",
        )
        read_only_fields = fields


# ======================================================
# SUBSCRIPTION PLAN
# ======================================================

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Subscription plans for recurring deliveries.
    """
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "name",
            "description",
            "plan_type",
            "base_price",
            "billing_cycle_days",
            "discounted_price",
            "is_active",
            "combo",
        )
        read_only_fields = ("discounted_price",)

    def get_discounted_price(self, obj):
        """Return discounted price for display."""
        return money(obj.get_discounted_price(30))  # Show monthly discount


# ======================================================
# SUBSCRIPTION
# ======================================================

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Active customer subscriptions.
    """
    plan = SubscriptionPlanSerializer(read_only=True)
    price_per_cycle_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "plan",
            "customer_name",
            "customer_email",
            "customer_phone",
            "billing_cycle_days",
            "price_per_cycle",
            "price_per_cycle_display",
            "status",
            "status_display",
            "delivery_address",
            "delivery_instructions",
            "start_date",
            "next_delivery_date",
            "paused_until",
            "custom_days",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "price_per_cycle_display",
            "status_display",
            "created_at",
            "updated_at",
        )

    def get_price_per_cycle_display(self, obj):
        """Format price for display."""
        return money(obj.price_per_cycle)

    def create(self, validated_data):
        """Create subscription with calculated pricing."""
        plan = validated_data.get('plan')
        billing_cycle_days = validated_data.get('billing_cycle_days', 30)

        # Calculate price
        validated_data['price_per_cycle'] = plan.get_discounted_price(billing_cycle_days)

        return super().create(validated_data)
