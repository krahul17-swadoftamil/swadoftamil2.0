from django.urls import include, path
from rest_framework.routers import DefaultRouter

from menu.views import PreparedItemViewSet, ComboViewSet


# ======================================================
# ROUTER
# ======================================================

router = DefaultRouter()
router.register(
    r"prepared-items",
    PreparedItemViewSet,
    basename="prepared-item"
)
router.register(
    r"combos",
    ComboViewSet,
    basename="combo"
)


# ======================================================
# URL PATTERNS
# ======================================================

urlpatterns = [
    path("", include(router.urls)),
]
