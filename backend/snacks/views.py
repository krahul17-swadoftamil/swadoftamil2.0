from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Snack
from .serializers import SnackSerializer





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

        return queryset