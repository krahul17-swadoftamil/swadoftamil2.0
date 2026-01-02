from decimal import Decimal

from django.db.models import F, Sum, Count, DecimalField, ExpressionWrapper
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Ingredient
from .serializers import IngredientSerializer


# ======================================================
# ERP CONSTANTS (BASE UNITS ONLY)
# ======================================================
ZERO = Decimal("0.000")

LOW_STOCK_LIMITS = {
    "kg": Decimal("1.000"),
    "ltr": Decimal("1.000"),
    "pcs": Decimal("10.000"),
}


# ======================================================
# INGREDIENT VIEWSET (ERP SOURCE OF TRUTH)
# ======================================================
class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Ingredient = ERP truth.

    ✔ Stock
    ✔ Cost
    ✔ Inventory value
    ❌ No mutation
    ❌ No food logic
    """

    queryset = Ingredient.objects.filter(is_active=True)
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name",)
    ordering_fields = ("name", "stock_qty", "cost_per_unit")
    ordering = ("name",)

    # --------------------------------------------------
    # LOW STOCK (BUSINESS SIGNAL)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """
        Ingredients nearing depletion.
        """
        low_items = [
            ing for ing in self.get_queryset()
            if ing.stock_qty <= LOW_STOCK_LIMITS.get(ing.unit, ZERO)
            and ing.stock_qty > ZERO
        ]

        return Response({
            "count": len(low_items),
            "results": self.get_serializer(low_items, many=True).data
        })

    # --------------------------------------------------
    # OUT OF STOCK
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def out_of_stock(self, request):
        qs = self.get_queryset().filter(stock_qty__lte=ZERO)

        return Response({
            "count": qs.count(),
            "results": self.get_serializer(qs, many=True).data
        })

    # --------------------------------------------------
    # INVENTORY SUMMARY (DASHBOARD)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset()

        inventory_value_expr = ExpressionWrapper(
            F("stock_qty") * F("cost_per_unit"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        totals = qs.aggregate(
            total_inventory_value=Sum(inventory_value_expr),
            total_quantity=Sum("stock_qty"),
            total_ingredients=Count("id"),
        )

        # -------- unit-wise breakdown --------
        unit_stats = {}
        low_stock_count = 0
        out_of_stock_count = 0

        for ing in qs:
            unit_stats.setdefault(
                ing.unit,
                {"count": 0, "total_qty": ZERO}
            )

            unit_stats[ing.unit]["count"] += 1
            unit_stats[ing.unit]["total_qty"] += ing.stock_qty

            if ing.stock_qty <= ZERO:
                out_of_stock_count += 1
            elif ing.stock_qty <= LOW_STOCK_LIMITS.get(ing.unit, ZERO):
                low_stock_count += 1

        return Response({
            "total_inventory_value": totals["total_inventory_value"] or Decimal("0.00"),
            "total_quantity": totals["total_quantity"] or ZERO,
            "total_ingredients": totals["total_ingredients"] or 0,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "unit_breakdown": unit_stats,
        })
