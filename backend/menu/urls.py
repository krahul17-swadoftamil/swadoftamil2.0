from django.urls import include, path
from rest_framework.routers import DefaultRouter

from menu.views import PreparedItemViewSet, ComboViewSet, MarketingOfferViewSet, SubscriptionPlanViewSet, SubscriptionViewSet


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
router.register(
    r"marketing-offers",
    MarketingOfferViewSet,
    basename="marketing-offer"
)
router.register(
    r"subscription-plans",
    SubscriptionPlanViewSet,
    basename="subscription-plan"
)
router.register(
    r"subscriptions",
    SubscriptionViewSet,
    basename="subscription"
)


# ======================================================
# URL PATTERNS
# ======================================================

urlpatterns = [
    path("", include(router.urls)),
]
