from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import AuthViewSet, CustomerViewSet
from .jwt_views import FirebaseTokenObtainPairView, CustomTokenObtainPairView

# ViewSets → method routers
auth = AuthViewSet.as_view
customer = CustomerViewSet.as_view

urlpatterns = [
    # ==================================================
    # JWT AUTH (TOKEN-BASED)
    # ==================================================
    path(
        "jwt/create/",
        CustomTokenObtainPairView.as_view(),
        name="jwt-create",
    ),
    path(
        "jwt/firebase/",
        FirebaseTokenObtainPairView.as_view(),
        name="jwt-firebase",
    ),
    path(
        "jwt/refresh/",
        TokenRefreshView.as_view(),
        name="jwt-refresh",
    ),
    path(
        "jwt/verify/",
        TokenVerifyView.as_view(),
        name="jwt-verify",
    ),

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
        "firebase-login/",
        auth({"post": "firebase_login"}),
        name="auth-firebase-login",
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
