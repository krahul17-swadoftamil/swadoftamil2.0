import os
import json
import base64
from datetime import timedelta
from collections import defaultdict
import time

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, logout, get_user_model
from django.shortcuts import redirect
from django.urls import reverse

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.authentication import SessionAuthentication

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .models import Customer, OTP, SMSSetting
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
)
from .sms import send_sms

User = get_user_model()

# ======================================================
# RATE LIMITING
# ======================================================
# Simple in-memory rate limiter (use Redis in production)
otp_rate_limits = defaultdict(list)

def check_rate_limit(phone, max_requests=3, window_seconds=300):  # 3 requests per 5 minutes
    """Check if phone number has exceeded rate limit"""
    now = time.time()
    phone_limits = otp_rate_limits[phone]

    # Remove old requests outside the window
    phone_limits[:] = [req_time for req_time in phone_limits if now - req_time < window_seconds]

    if len(phone_limits) >= max_requests:
        return False, window_seconds - (now - phone_limits[0]) if phone_limits else 0

    phone_limits.append(now)
    return True, 0

from django.middleware.csrf import get_token

# ======================================================
# CONSTANTS
# ======================================================
OTP_EXPIRY_MINUTES = 5
DEV_TEST_OTP = "1234"


def is_dev_mode():
    return settings.DEBUG or os.environ.get("ENV") == "development"


def generate_otp():
    """6-digit numeric OTP"""
    return str(int.from_bytes(os.urandom(3), "big") % 1000000).zfill(6)


def get_or_create_user_for_customer(customer, username_hint):
    """
    Ensures a Django auth user exists and is linked.
    """
    if customer.user:
        return customer.user

    username = username_hint
    suffix = 0
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{username_hint}_{suffix}"

    user = User.objects.create_user(
        username=username,
        email=customer.email or "",
        password=None,
    )
    user.set_unusable_password()
    user.save()

    customer.user = user
    customer.save(update_fields=["user"])
    return user


# ======================================================
# AUTH / OTP VIEWSET
# ======================================================
class AuthViewSet(ViewSet):
    permission_classes = [AllowAny]

    # --------------------------------------------------
    # CSRF TOKEN
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def csrf(self, request):
        """Get CSRF token for frontend"""
        token = get_token(request)
        return Response({"csrfToken": token})

    # --------------------------------------------------
    # SEND OTP
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def send_otp(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        # Rate limiting check
        allowed, wait_seconds = check_rate_limit(phone)
        if not allowed:
            return Response(
                {
                    "error": f"Too many OTP requests. Please wait {int(wait_seconds)} seconds before trying again.",
                    "wait_seconds": int(wait_seconds)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        OTP.objects.filter(phone=phone, is_used=False).update(is_used=True)

        dev_mode = is_dev_mode()
        code = DEV_TEST_OTP if dev_mode else generate_otp()

        otp = OTP.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )

        sms_sent = False
        if not dev_mode:
            sms_sent = send_sms(phone, f"Your Swad OTP is {otp.code}")

        show_plaintext = dev_mode
        setting = SMSSetting.objects.first()
        if setting and setting.allow_plaintext_otp:
            show_plaintext = True

        response = {
            "message": "OTP sent",
            "sms_sent": sms_sent,
        }

        if show_plaintext:
            response["otp"] = otp.code

        return Response(response, status=status.HTTP_200_OK)

    # --------------------------------------------------
    # VERIFY OTP
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        dev_mode = is_dev_mode()

        if dev_mode and code == DEV_TEST_OTP:
            customer, created = Customer.objects.get_or_create(phone=phone)
        else:
            try:
                otp = OTP.objects.get(
                    phone=phone,
                    code=code,
                    is_used=False,
                )
            except OTP.DoesNotExist:
                return Response(
                    {"error": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if otp.is_expired:
                return Response(
                    {"error": "OTP expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            otp.mark_used()
            customer, created = Customer.objects.get_or_create(phone=phone)

        user = get_or_create_user_for_customer(customer, username_hint=phone)

        # Set authentication backend for OTP login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        return Response(
            {
                "success": True,
                "customer": CustomerSerializer(customer).data,
                "is_new_customer": created or not bool(customer.name),
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------
    # COMPLETE PROFILE
    # --------------------------------------------------
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def complete_profile(self, request):
        name = request.data.get("name", "").strip()
        email = request.data.get("email", "").strip()

        if not name:
            return Response(
                {"error": "Name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = Customer.objects.get(user=request.user)
        customer.name = name
        if email:
            customer.email = email
        customer.save()

        return Response(
            {
                "success": True,
                "customer": CustomerSerializer(customer).data,
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------
    # GOOGLE LOGIN
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def google_login(self, request):
        credential = request.data.get("credential")
        remember_me = request.data.get("remember_me", False)
        if not credential:
            return Response({"error": "Credential missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the Google token
            data = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

            # Validate token claims
            if not data.get("email_verified", False):
                return Response({"error": "Email not verified with Google"}, status=status.HTTP_400_BAD_REQUEST)

            google_id = data["sub"]
            email = data.get("email", "").strip()
            name = data.get("name", "").strip()

            if not email:
                return Response({"error": "Email is required from Google"}, status=status.HTTP_400_BAD_REQUEST)

            # 🔗 BULLETPROOF ACCOUNT LINKING
            from django.db import transaction

            with transaction.atomic():
                # Check if Google ID is already linked to another customer
                existing_google_customer = Customer.objects.filter(google_id=google_id).first()

                if request.user.is_authenticated:
                    # User is logged in with phone - link Google to existing account
                    current_customer = Customer.objects.get(user=request.user)

                    if existing_google_customer:
                        if existing_google_customer == current_customer:
                            # Already linked - just proceed
                            customer = current_customer
                            created = False
                        else:
                            # Google ID linked to different customer - conflict
                            return Response(
                                {"error": "This Google account is already linked to another user"},
                                status=status.HTTP_409_CONFLICT
                            )
                    else:
                        # Link Google to current customer
                        current_customer.google_id = google_id
                        current_customer.google_email = email
                        current_customer.auth_provider = "google"
                        # Update name/email if not set
                        if not current_customer.name and name:
                            current_customer.name = name
                        if not current_customer.email and email:
                            current_customer.email = email
                        current_customer.save()
                        customer = current_customer
                        created = False
                else:
                    # No session - normal Google login
                    if existing_google_customer:
                        # Existing Google customer - update info and login
                        customer = existing_google_customer
                        if name and not customer.name:
                            customer.name = name
                        if email and not customer.email:
                            customer.email = email
                        customer.google_email = email
                        customer.save()
                        created = False
                    else:
                        # Check for auto-linking: existing customer with same email
                        existing_email_customer = Customer.objects.filter(email=email).first()
                        if existing_email_customer and not existing_email_customer.google_id:
                            # Auto-link: existing phone customer with matching email
                            customer = existing_email_customer
                            customer.google_id = google_id
                            customer.google_email = email
                            customer.auth_provider = "google"
                            # Update name if not set
                            if not customer.name and name:
                                customer.name = name
                            customer.save()
                            created = False
                        else:
                            # New Google customer
                            customer = Customer.objects.create(
                                name=name,
                                email=email,
                                google_id=google_id,
                                google_email=email,
                                auth_provider="google",
                            )
                            created = True

            user = get_or_create_user_for_customer(
                customer, username_hint=f"google_{google_id}"
            )

            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

            # Set session expiry based on remember_me
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(60 * 60 * 24)  # 1 day

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            # Set custom expiry for remember_me
            if remember_me:
                refresh.set_exp(60 * 60 * 24 * 30)  # 30 days
                access = refresh.access_token
                access.set_exp(60 * 60)  # 1 hour access token
            else:
                # Use default expiry from settings
                access = refresh.access_token

            return Response(
                {
                    "success": True,
                    "customer": CustomerSerializer(customer).data,
                    "is_new_customer": created,
                    "access": str(access),
                    "refresh": str(refresh),
                }
            )

        except ValueError as e:
            # Token verification failed
            return Response(
                {"error": "Invalid Google credential"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Log the error for debugging but don't expose details
            print(f"Google login error: {e}")
            return Response(
                {"error": "Google login failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # --------------------------------------------------
    # FIREBASE LOGIN
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def firebase_login(self, request):
        """Authenticate user with Firebase ID token"""
        id_token = request.data.get("id_token")
        remember_me = request.data.get("remember_me", False)
        if not id_token:
            return Response({"error": "Firebase ID token is required"}, status=status.HTTP_400_BAD_REQUEST)

        from backend.firebase_utils import verify_firebase_token, get_or_create_user_from_firebase

        # Verify Firebase token
        firebase_user = verify_firebase_token(id_token)
        if not firebase_user:
            return Response({"error": "Invalid Firebase token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create Django user from Firebase user data
            user = get_or_create_user_from_firebase(firebase_user)

            # Get or create customer profile
            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults={
                    'name': firebase_user.get('name', ''),
                    'email': firebase_user.get('email', ''),
                    'auth_provider': 'firebase',
                }
            )

            # Update customer info if needed
            if not customer.name and firebase_user.get('name'):
                customer.name = firebase_user['name']
                customer.save()

            if not customer.email and firebase_user.get('email'):
                customer.email = firebase_user['email']
                customer.save()

            # Log the user in
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)

            # Set session expiry based on remember_me
            if remember_me:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(60 * 60 * 24)  # 1 day

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            # Set custom expiry for remember_me
            if remember_me:
                refresh.set_exp(60 * 60 * 24 * 30)  # 30 days
                access = refresh.access_token
                access.set_exp(60 * 60)  # 1 hour access token
            else:
                # Use default expiry from settings
                access = refresh.access_token

            return Response({
                "success": True,
                "customer": CustomerSerializer(customer).data,
                "is_new_customer": created or not bool(customer.name),
                "access": str(access),
                "refresh": str(refresh),
            })

        except Exception as e:
            print(f"Firebase login error: {e}")
            return Response(
                {"error": "Firebase authentication failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def logout(self, request):
        request.session.flush()
        logout(request)
        return Response({"success": True})





# ======================================================
# CUSTOMER PROFILE
# ======================================================
class CustomerViewSet(ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def me(self, request):
        customer = Customer.objects.get(user=request.user)
        return Response(CustomerSerializer(customer).data)

    @action(detail=False, methods=["patch"])
    def update_profile(self, request):
        """Update customer profile information"""
        customer = Customer.objects.get(user=request.user)
        
        serializer = CustomerUpdateSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(CustomerSerializer(customer).data)
