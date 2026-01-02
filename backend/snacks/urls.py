from rest_framework.routers import DefaultRouter
from .views import SnackViewSet


router = DefaultRouter()

router.register("snacks", SnackViewSet, basename="snack")

urlpatterns = router.urls
