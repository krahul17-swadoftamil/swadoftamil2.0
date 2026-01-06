from decimal import Decimal

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django.db import models

from ingredients.models import Ingredient
from menu.models import PreparedItem, Combo, MarketingOffer, SubscriptionPlan, Subscription
from menu.serializers import (
    IngredientSerializer,
    PreparedItemSerializer,
    ComboSerializer,
    MarketingOfferSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
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


# ======================================================
# MARKETING OFFERS (PUBLIC READ)
# ======================================================

class MarketingOfferViewSet(ReadOnlyModelViewSet):
    """
    Marketing offers for promotional banners and features.
    """

    serializer_class = MarketingOfferSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        return MarketingOffer.objects.filter(
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )


# ======================================================
# SUBSCRIPTION PLANS (PUBLIC READ)
# ======================================================

class SubscriptionPlanViewSet(ReadOnlyModelViewSet):
    """
    Subscription plans for recurring deliveries.
    """

    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)


# ======================================================
# SUBSCRIPTIONS (CUSTOMER MANAGEMENT)
# ======================================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Customer subscription management.
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]  # TODO: Add proper authentication
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Subscription.objects.all()

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause subscription until specified date."""
        subscription = self.get_object()
        pause_until = request.data.get('pause_until')

        if not pause_until:
            return Response(
                {"error": "pause_until date required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils.dateparse import parse_date
        pause_date = parse_date(pause_until)
        if not pause_date:
            return Response(
                {"error": "Invalid date format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.pause_until(pause_date)
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume paused subscription."""
        subscription = self.get_object()
        subscription.resume()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel subscription."""
        subscription = self.get_object()
        subscription.cancel()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
