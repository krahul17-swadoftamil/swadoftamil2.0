from decimal import Decimal
from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """
    INGREDIENT SERIALIZER (READ-ONLY ERP API)

    ✔ Stock lives here
    ✔ Cost lives here
    ✔ Used for availability & reporting
    ❌ No mutation via API
    """

    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "unit",
            "stock_qty",
            "cost_per_unit",
            "total_value",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields  # 🔒 FULL READ-ONLY (ERP RULE)

    # --------------------------------------------------
    # DERIVED FIELDS
    # --------------------------------------------------
    def get_total_value(self, obj) -> Decimal:
        """
        Total inventory value (safe decimal)
        """
        return obj.total_value
