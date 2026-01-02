import os
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import Customer, OTP, SMSSetting
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    CustomerSerializer,
)
from .sms import send_sms


# ======================================================
# CONSTANTS
# ======================================================
OTP_EXPIRY_MINUTES = 5
DEV_TEST_OTP = "1234"


def is_dev_mode():
    return settings.DEBUG or os.environ.get("ENV") == "development"


# ======================================================
# AUTH / OTP VIEWSET
# ======================================================
class AuthViewSet(ViewSet):
    """
    Phone + OTP authentication (passwordless).

    FLOW:
    1. send_otp
    2. verify_otp
    """

    permission_classes = [AllowAny]

    # --------------------------------------------------
    # SEND OTP
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def send_otp(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        # Invalidate any previous unused OTPs
        OTP.objects.filter(phone=phone, is_used=False).update(is_used=True)

        dev_mode = is_dev_mode()

        # Generate OTP
        if dev_mode:
            code = DEV_TEST_OTP
        else:
            code = OTP.generate_code()

        otp = OTP.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )

        sms_sent = False
        if not dev_mode:
            sms_sent = send_sms(
                phone,
                f"Your Swad of Tamil OTP is {otp.code}"
            )

        # Decide whether plaintext OTP can be returned
        show_plaintext = False

        if dev_mode or getattr(settings, "SEND_PLAINTEXT_OTP", False):
            show_plaintext = True
        else:
            try:
                setting = SMSSetting.objects.first()
                if setting and setting.allow_plaintext_otp:
                    show_plaintext = True
            except Exception:
                pass

        response = {
            "message": "OTP created",
            "sms_sent": bool(sms_sent),
        }

        if show_plaintext:
            response["otp"] = otp.code

        if dev_mode:
            response["helper_text"] = "Development mode: use OTP 1234"

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

        # DEV shortcut
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

            otp.is_used = True
            otp.save(update_fields=["is_used"])

            customer, created = Customer.objects.get_or_create(phone=phone)

        return Response(
            {
                "message": "OTP verified",
                "customer": CustomerSerializer(customer).data,
                "is_new_customer": created or not bool(customer.name),
            },
            status=status.HTTP_200_OK,
        )


# ======================================================
# CUSTOMER PROFILE (AUTHENTICATED)
# ======================================================
class CustomerViewSet(ViewSet):
    """
    Logged-in customer profile APIs.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Return current customer's profile.
        """
        customer = Customer.objects.get(phone=request.user.phone)
        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_200_OK,
        )
