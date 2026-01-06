from decimal import Decimal
from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """
    INGREDIENT SERIALIZER (READ-ONLY ERP API)

    ✔ Single source of truth
    ✔ Used for reporting, dashboards, availability
    ❌ No create / update
    ❌ No business logic
    """

    total_value = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
        source="total_value",
    )

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "code",
            "name",
            "unit",
            "stock_qty",
            "cost_per_unit",
            "total_value",
            "category",
            "preferred_vendor",
            "expiry_days",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields  # 🔒 ERP RULE: FULL READ-ONLY
