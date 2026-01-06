from rest_framework import serializers
from django.conf import settings
import os

from .models import Customer


# ======================================================
# ENV HELPERS
# ======================================================

DEV_TEST_OTP = "1234"


def is_dev_mode():
    return bool(settings.DEBUG or os.environ.get("ENV") == "development")


# ======================================================
# PHONE FIELD (REUSABLE, STRICT)
# ======================================================

class PhoneField(serializers.CharField):
    """
    Normalized phone field:
    - digits only
    - length 10–15
    """

    def to_internal_value(self, data):
        value = super().to_internal_value(data).strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain digits only."
            )

        if not (10 <= len(value) <= 15):
            raise serializers.ValidationError(
                "Enter a valid phone number."
            )

        return value


# ======================================================
# SEND OTP
# ======================================================

class SendOTPSerializer(serializers.Serializer):
    """
    Request OTP.

    ✔ Phone-only
    ✔ No user enumeration
    ✔ Same response for new & existing users
    """

    phone = PhoneField()

    def validate(self, attrs):
        # Future hooks:
        # - rate limiting
        # - blocklist
        # - country validation
        return attrs


# ======================================================
# VERIFY OTP
# ======================================================

class VerifyOTPSerializer(serializers.Serializer):
    """
    Verify OTP and authenticate customer.
    """

    phone = PhoneField()
    code = serializers.CharField(max_length=6, trim_whitespace=True)

    def validate_code(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")

        # DEV shortcut
        if is_dev_mode() and value == DEV_TEST_OTP:
            return value

        if len(value) != 6:
            raise serializers.ValidationError(
                "OTP must be exactly 6 digits."
            )

        return value

    def validate(self, attrs):
        # Future hooks:
        # - OTP retry limits
        # - IP/device fingerprint
        # - replay protection
        return attrs


# ======================================================
# CUSTOMER SERIALIZER (READ-ONLY)
# ======================================================

class CustomerSerializer(serializers.ModelSerializer):
    """
    Customer identity payload.

    Used by:
    - /auth/verify-otp/
    - /auth/me/
    - order responses
    """

    is_first_time_customer = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "uuid",
            "code",
            "phone",
            "name",
            "email",
            "is_active",
            "total_orders",
            "first_order_at",
            "last_order_at",
            "preferences",
            "is_first_time_customer",
            "created_at",
        )
        read_only_fields = fields

    def get_is_first_time_customer(self, obj):
        return obj.total_orders == 0


# ======================================================
# CUSTOMER UPDATE
# ======================================================

class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating customer profile.
    Allows updating name, email, and preferences.
    """

    class Meta:
        model = Customer
        fields = ("name", "email", "preferences")
