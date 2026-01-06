from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Snack, SnackCombo
from .serializers import SnackSerializer, SnackComboSerializer





# ======================================================
# SNACK VIEWSET — READ ONLY
# ======================================================
# ======================================================
# SNACK VIEWSET — READ ONLY (GLOBAL SNACKS)
# ======================================================
class SnackViewSet(ReadOnlyModelViewSet):
    """
    Snack listing API.

    Design decisions:
    - Snacks are GLOBAL (not store-linked)
    - Visibility controlled by is_active
    - Availability handled by stock / serializer
    """

    serializer_class = SnackSerializer

    def get_queryset(self):
        queryset = (
            Snack.objects
            .filter(is_active=True)
            .order_by("name")
        )

        # Optional: featured snacks
        featured = self.request.query_params.get("featured")
        if featured == "true":
            queryset = queryset.filter(is_featured=True)

        # Optional: filter by region
        region = self.request.query_params.get("region")
        if region:
            queryset = queryset.filter(region=region)

        return queryset

    @action(detail=False, methods=["get"])
    def regions(self, request):
        """
        Get available regions for filtering.
        Returns regions that have active snacks.
        """
        regions = (
            Snack.objects
            .filter(is_active=True)
            .values_list('region', flat=True)
            .distinct()
            .order_by('region')
        )

        # Convert to display names
        region_display_map = dict(Snack.REGION_CHOICES)
        result = [
            {
                "value": region,
                "label": region_display_map.get(region, region.title())
            }
            for region in regions
        ]

        return Response(result)


# ======================================================
# SNACK COMBO VIEWSET — READ ONLY
# ======================================================
class SnackComboViewSet(ReadOnlyModelViewSet):
    """
    Snack combo bundle API.

    Design decisions:
    - Combos are GLOBAL (not store-linked)
    - Visibility controlled by is_active
    - Availability derived from constituent snacks
    """

    serializer_class = SnackComboSerializer

    def get_queryset(self):
        queryset = (
            SnackCombo.objects
            .filter(is_active=True)
            .prefetch_related("items__snack")
            .order_by("name")
        )

        # Optional: featured combos
        featured = self.request.query_params.get("featured")
        if featured == "true":
            queryset = queryset.filter(is_featured=True)

        return queryset