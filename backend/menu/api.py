from rest_framework import viewsets, routers
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Combo
from .serializers import ComboSerializer


# ======================================================
# COMBO API (READ-ONLY)
# ======================================================
class ComboViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only Combo API for frontend consumption.
    """
    serializer_class = ComboSerializer

    def get_queryset(self):
        """
        Always return active combos only.
        """
        return Combo.objects.filter(is_active=True).order_by("name")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """
        GET /api/combos/featured/
        """
        qs = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ======================================================
# ROUTER
# ======================================================
router = routers.DefaultRouter()
router.register("combos", ComboViewSet, basename="combo")

urlpatterns = router.urls
