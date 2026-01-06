from django.urls import path
from .views import AuthViewSet, CustomerViewSet

# ViewSets → method routers
auth = AuthViewSet.as_view
customer = CustomerViewSet.as_view

urlpatterns = [
    # ==================================================
    # AUTH / OTP (SESSION-BASED)
    # ==================================================
    path(
        "send-otp/",
        auth({"post": "send_otp"}),
        name="auth-send-otp",
    ),
    path(
        "verify-otp/",
        auth({"post": "verify_otp"}),
        name="auth-verify-otp",
    ),
    path(
        "complete-profile/",
        auth({"post": "complete_profile"}),
        name="auth-complete-profile",
    ),
    path(
        "google-login/",
        auth({"post": "google_login"}),
        name="auth-google-login",
    ),
    path(
        "logout/",
        auth({"post": "logout"}),
        name="auth-logout",
    ),

    # ==================================================
    # CUSTOMER (SESSION REQUIRED)
    # ==================================================
    path(
        "me/",
        customer({"get": "me", "patch": "update_profile"}),
        name="customer-me",
    ),
]
