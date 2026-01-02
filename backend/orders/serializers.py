from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    Order,
    OrderItem,
    OrderCombo,
    OrderSnack,
    Cart,
    CartLine,
)

from snacks.models import Snack
from orders.services import create_order_from_payload


# ======================================================
# ORDER — READ SERIALIZERS
# ======================================================

class OrderItemReadSerializer(serializers.ModelSerializer):
    prepared_item_name = serializers.CharField(
        source="prepared_item.name",
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "prepared_item",
            "prepared_item_name",
            "quantity",
        )


class OrderComboReadSerializer(serializers.ModelSerializer):
    combo_name = serializers.CharField(
        source="combo.name",
        read_only=True
    )

    class Meta:
        model = OrderCombo
        fields = (
            "id",
            "combo",
            "combo_name",
            "quantity",
        )


class OrderSnackReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSnack
        fields = (
            "snack_id",
            "snack_name",
            "quantity",
            "unit_price",
        )


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Used for:
    - My Orders list
    - Order Details page
    """

    order_items = OrderItemReadSerializer(
        many=True, read_only=True, source="items"
    )
    order_combos = OrderComboReadSerializer(
        many=True, read_only=True, source="combos"
    )
    order_snacks = OrderSnackReadSerializer(
        many=True, read_only=True, source="snacks"
    )

    customer_id = serializers.IntegerField(
        source="customer.id", read_only=True
    )
    customer_name = serializers.CharField(read_only=True)
    customer_phone = serializers.CharField(read_only=True)

    total_items = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "status_display",
            "payment_method",
            "total_amount",
            "created_at",
            "customer_id",
            "customer_name",
            "customer_phone",
            "order_items",
            "order_combos",
            "order_snacks",
            "total_items",
        )

    def get_total_items(self, obj):
        return (
            sum(i.quantity for i in obj.items.all()) +
            sum(s.quantity for s in obj.snacks.all())
        )


# ======================================================
# ORDER — CREATE SERIALIZER (SHAPE ONLY)
# ======================================================

class OrderCreateSerializer(serializers.Serializer):
    """
    ✔ Validates request payload shape
    ✔ Business logic lives in service layer
    """

    combos = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    snacks = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    customer = serializers.DictField(
        required=False,
        help_text="Customer snapshot (phone mandatory)"
    )

    payment_method = serializers.CharField(
        required=False, default="online"
    )

    # -----------------------------
    # ROOT VALIDATION
    # -----------------------------
    def validate(self, data):
        if not data.get("combos") and not data.get("snacks"):
            raise serializers.ValidationError(
                "Order must contain at least one combo or snack."
            )
        return data

    # -----------------------------
    # COMBOS — SHAPE VALIDATION
    # -----------------------------
    def validate_combos(self, combos):
        normalized = []

        for row in combos or []:
            combo_id = row.get("combo_id") or row.get("id")
            qty = int(row.get("quantity", 1))

            if not combo_id:
                raise serializers.ValidationError("combo_id is required")

            if qty < 1:
                raise serializers.ValidationError(
                    "Combo quantity must be ≥ 1"
                )

            addons = []
            for addon in row.get("addons", []):
                pid = addon.get("prepared_item_id") or addon.get("id")
                aqty = int(addon.get("quantity", 1))

                if not pid:
                    raise serializers.ValidationError(
                        "prepared_item_id missing in addon"
                    )

                if aqty < 1:
                    raise serializers.ValidationError(
                        "Addon quantity must be ≥ 1"
                    )

                addons.append({
                    "prepared_item_id": pid,
                    "quantity": aqty,
                })

            normalized.append({
                "combo_id": combo_id,
                "quantity": qty,
                "addons": addons,
            })

        return normalized

    # -----------------------------
    # SNACKS — SAFE VALIDATION
    # -----------------------------
    def validate_snacks(self, snacks):
        normalized = []

        for row in snacks or []:
            snack_id = row.get("snack_id")
            qty = int(row.get("quantity", 1))

            if not snack_id:
                raise serializers.ValidationError("snack_id is required")

            if qty < 1:
                raise serializers.ValidationError(
                    "Snack quantity must be ≥ 1"
                )

            snack = None

            # Try numeric ID
            try:
                snack = Snack.objects.get(
                    id=int(snack_id), is_active=True
                )
            except (ValueError, Snack.DoesNotExist):
                pass

            # Try UUID
            if snack is None:
                try:
                    snack = Snack.objects.get(
                        uuid=snack_id, is_active=True
                    )
                except Snack.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Snack '{snack_id}' not found"
                    )

            normalized.append({
                "snack_id": snack.id,
                "snack_name": snack.name,
                "unit_price": snack.selling_price,
                "quantity": qty,
            })

        return normalized

    # -----------------------------
    # CREATE — SERVICE DELEGATION
    # -----------------------------
    @transaction.atomic
    def create(self, validated_data):
        payload = {
            "combos": validated_data.get("combos", []),
            "snacks": validated_data.get("snacks", []),
            "payment_method": validated_data.get("payment_method"),
        }

        if validated_data.get("customer"):
            payload["customer"] = validated_data["customer"]

        try:
            return create_order_from_payload(payload)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))


# ======================================================
# CART SERIALIZERS
# ======================================================

class CartLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartLine
        fields = (
            "id",
            "type",
            "combo",
            "prepared_item",
            "snack_id",
            "snack_name",
            "quantity",
            "unit_price",
        )


class CartSerializer(serializers.ModelSerializer):
    lines = CartLineSerializer(many=True)

    class Meta:
        model = Cart
        fields = (
            "id",
            "customer",
            "session_key",
            "total_amount",
            "metadata",
            "lines",
        )

    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        cart = Cart.objects.create(**validated_data)
        for line in lines:
            CartLine.objects.create(cart=cart, **line)
        return cart

    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                CartLine.objects.create(cart=instance, **line)

        return instance
