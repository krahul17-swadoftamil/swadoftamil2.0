from rest_framework import serializers
from .models import Customer


# ======================================================
# SEND OTP
# ======================================================
class SendOTPSerializer(serializers.Serializer):
    """
    Validates phone number for OTP sending.
    Phone is the primary identity.
    """

    phone = serializers.CharField(
        max_length=15,
        trim_whitespace=True
    )

    def validate_phone(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain digits only.")

        if len(value) < 10:
            raise serializers.ValidationError("Enter a valid phone number.")

        return value


# ======================================================
# VERIFY OTP
# ======================================================
class VerifyOTPSerializer(serializers.Serializer):
    """
    Validates phone + OTP combination.
    """

    phone = serializers.CharField(
        max_length=15,
        trim_whitespace=True
    )

    code = serializers.CharField(
        max_length=6,
        trim_whitespace=True
    )

    def validate_phone(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError("Invalid phone number.")

        return value

    def validate_code(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")

        if len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits.")

        return value


# ======================================================
# CUSTOMER SERIALIZER (READ-ONLY)
# ======================================================
class CustomerSerializer(serializers.ModelSerializer):
    """
    Read-only customer representation.
    Used after OTP verification and in /me endpoint.
    """

    is_first_time_customer = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "uuid",
            "phone",
            "name",
            "email",
            "total_orders",
            "first_order_at",
            "last_order_at",
            "is_first_time_customer",
            "created_at",
        )
        read_only_fields = fields

    def get_is_first_time_customer(self, obj):
        return obj.total_orders == 0
