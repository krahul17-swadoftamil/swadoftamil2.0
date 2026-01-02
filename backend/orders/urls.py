from django.urls import path
from . import views

urlpatterns = [
    # CREATE ORDER (CHECKOUT)
    path("", views.create_order, name="order-create"),  # 👈 THIS WAS MISSING

    # EXISTING
    path("latest/", views.latest_order, name="order-latest"),
    path("kitchen/", views.kitchen_screen, name="order-kitchen"),
    path("print/<int:order_id>/", views.print_slip, name="order-print"),
    path("cart/", views.cart_view, name="cart-root"),
    path("cart/<uuid:cart_id>/", views.cart_view, name="cart-detail"),
]
