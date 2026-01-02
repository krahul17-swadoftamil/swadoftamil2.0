from django.urls import path
from .views import AuthViewSet, CustomerViewSet

auth = AuthViewSet.as_view
customer = CustomerViewSet.as_view

urlpatterns = [
    # ================= AUTH / OTP =================
    path("send-otp/", auth({"post": "send_otp"}), name="send-otp"),
    path("verify-otp/", auth({"post": "verify_otp"}), name="verify-otp"),

    # ================= CUSTOMER =================
    path("me/", customer({"get": "me"}), name="customer-me"),
]
