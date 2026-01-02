from decimal import Decimal

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination

from ingredients.models import Ingredient
from menu.models import PreparedItem, Combo
from menu.serializers import (
    IngredientSerializer,
    PreparedItemSerializer,
    ComboSerializer,
)

ZERO = Decimal("0.00")


# ======================================================
# PAGINATION
# ======================================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ======================================================
# INGREDIENTS (INTERNAL / AUTH)
# ======================================================

class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Ingredient data is internal-facing (ERP).
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    pagination_class = StandardResultsSetPagination


# ======================================================
# PREPARED ITEMS (PUBLIC READ)
# ======================================================

class PreparedItemViewSet(ReadOnlyModelViewSet):
    """
    Prepared items are read-only building blocks.
    """

    serializer_class = PreparedItemSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            PreparedItem.objects
            .filter(is_active=True)
            .select_related()  # no FK hops, safe
        )


# ======================================================
# COMBOS (PRIMARY CUSTOMER PRODUCTS)
# ======================================================

class ComboViewSet(ReadOnlyModelViewSet):
    """
    Combos are the ONLY sellable customer products.
    """

    serializer_class = ComboSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "selling_price"]
    ordering = ["name"]

    def get_queryset(self):
        return (
            Combo.objects
            .filter(is_active=True)
            .prefetch_related(
                "items__prepared_item",
            )
        )

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """
        Featured combos for homepage / highlights.
        """
        qs = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
