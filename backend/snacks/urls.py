from rest_framework.routers import DefaultRouter
from .views import SnackViewSet, SnackComboViewSet


router = DefaultRouter()

router.register("snacks", SnackViewSet, basename="snack")
router.register("combos", SnackComboViewSet, basename="combo")

urlpatterns = router.urls
