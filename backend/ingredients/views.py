from decimal import Decimal

from django.db.models import (
    F, Sum, Count, DecimalField, ExpressionWrapper, Q
)
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Ingredient
from .serializers import IngredientSerializer

# ======================================================
# CONSTANTS
# ======================================================

ZERO = Decimal("0.000")

LOW_STOCK_LIMITS = {
    "kg": Decimal("1.000"),
    "ltr": Decimal("1.000"),
    "pcs": Decimal("10.000"),
}


# ======================================================
# INGREDIENT VIEWSET (ERP READ API)
# ======================================================

class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Ingredient = ERP truth (READ ONLY)

    ✔ Stock
    ✔ Cost
    ✔ Inventory value
    ✔ Availability signals
    ❌ No mutation
    ❌ No order logic
    """

    permission_classes = [IsAuthenticated]
    serializer_class = IngredientSerializer

    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name", "code")
    ordering_fields = ("name", "stock_qty", "cost_per_unit")
    ordering = ("name",)

    def get_queryset(self):
        """
        Centralized base queryset.
        """
        return Ingredient.objects.filter(is_active=True)

    # --------------------------------------------------
    # LOW STOCK (BUSINESS SIGNAL)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """
        Ingredients nearing depletion.
        Uses DB filtering per unit type.
        """

        qs = self.get_queryset().filter(
            Q(unit="kg", stock_qty__gt=ZERO, stock_qty__lte=LOW_STOCK_LIMITS["kg"]) |
            Q(unit="ltr", stock_qty__gt=ZERO, stock_qty__lte=LOW_STOCK_LIMITS["ltr"]) |
            Q(unit="pcs", stock_qty__gt=ZERO, stock_qty__lte=LOW_STOCK_LIMITS["pcs"])
        )

        return Response({
            "count": qs.count(),
            "results": self.get_serializer(qs, many=True).data,
        })

    # --------------------------------------------------
    # OUT OF STOCK
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def out_of_stock(self, request):
        qs = self.get_queryset().filter(stock_qty__lte=ZERO)

        return Response({
            "count": qs.count(),
            "results": self.get_serializer(qs, many=True).data,
        })

    # --------------------------------------------------
    # INVENTORY SUMMARY (DASHBOARD)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset()

        inventory_value_expr = ExpressionWrapper(
            F("_stock_qty") * F("cost_per_unit"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        totals = qs.aggregate(
            total_inventory_value=Sum(inventory_value_expr),
            total_quantity=Sum("_stock_qty"),
            total_ingredients=Count("id"),
        )

        # -------- unit-wise aggregation --------
        unit_rows = (
            qs.values("unit")
            .annotate(
                count=Count("id"),
                total_qty=Sum("_stock_qty"),
                low_stock=Count(
                    "id",
                    filter=Q(
                        _stock_qty__gt=ZERO
                    ) & (
                        Q(unit="kg", _stock_qty__lte=LOW_STOCK_LIMITS["kg"]) |
                        Q(unit="ltr", _stock_qty__lte=LOW_STOCK_LIMITS["ltr"]) |
                        Q(unit="pcs", _stock_qty__lte=LOW_STOCK_LIMITS["pcs"])
                    )
                ),
                out_of_stock=Count(
                    "id",
                    filter=Q(_stock_qty__lte=ZERO)
                ),
            )
        )

        unit_breakdown = {
            row["unit"]: {
                "count": row["count"],
                "total_qty": row["total_qty"] or ZERO,
                "low_stock": row["low_stock"],
                "out_of_stock": row["out_of_stock"],
            }
            for row in unit_rows
        }

        return Response({
            "total_inventory_value": totals["total_inventory_value"] or Decimal("0.00"),
            "total_quantity": totals["total_quantity"] or ZERO,
            "total_ingredients": totals["total_ingredients"] or 0,
            "unit_breakdown": unit_breakdown,
        })
