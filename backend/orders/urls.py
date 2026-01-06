from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import OrderViewSet

# ======================================================
# API ROUTER
# ======================================================

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    # API routes (REST framework) - no extra api/ prefix needed
    path("", include(router.urls)),

    # --------------------------------------------------
    # ORDER ROUTES (Legacy / Direct)
    # --------------------------------------------------
    path("", views.create_order, name="order-create"),
    path("search/", views.search_orders, name="order-search"),
    path("latest/", views.latest_order, name="order-latest"),
    path("kitchen/", views.kitchen_screen, name="order-kitchen"),
    path("print/<int:order_id>/", views.print_slip, name="order-print"),
    path("<int:order_id>/", views.order_detail, name="order-detail"),  # ✅ Get order details

    # --------------------------------------------------
    # CART ROUTES
    # --------------------------------------------------
    path("cart/", views.cart_view, name="cart-root"),
    path("cart/<uuid:cart_id>/", views.cart_view, name="cart-detail"),

    # --------------------------------------------------
    # ADDRESS ROUTES
    # --------------------------------------------------
    path("address/add/", views.add_address, name="address-add"),
]
