from rest_framework import serializers
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import (
    Order,
    OrderItem,
    OrderCombo,
    OrderSnack,
    OrderAddon,
    OrderEvent,
    Cart,
    CartLine,
)

from snacks.models import Snack
from orders.services import create_order_from_normalized_payload


# ======================================================
# ORDER — READ SERIALIZERS
# ======================================================

class OrderItemReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="prepared_item.name",
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "name",
            "quantity",
        )


class OrderComboReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="combo.name",
        read_only=True
    )

    class Meta:
        model = OrderCombo
        fields = (
            "id",
            "name",
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


class OrderAddonReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAddon
        fields = (
            "order_item_type",
            "combo_id",
            "prepared_item_id",
            "snack_id",
            "addon_name",
            "addon_category",
            "quantity",
            "unit_price",
        )


class OrderEventReadSerializer(serializers.ModelSerializer):
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = OrderEvent
        fields = (
            "action",
            "action_display",
            "note",
            "created_at",
        )

    def get_action_display(self, obj):
        # Map action to display name
        action_display_map = {
            Order.STATUS_PLACED: "Order Placed",
            Order.STATUS_CONFIRMED: "Order Confirmed",
            Order.STATUS_PREPARING: "Preparing",
            Order.STATUS_OUT_FOR_DELIVERY: "Out for Delivery",
            Order.STATUS_DELIVERED: "Delivered",
            Order.STATUS_CANCELLED: "Cancelled",
        }
        return action_display_map.get(obj.action, obj.action.title())


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Canonical read serializer.
    Used by:
    - Order list
    - Order detail
    - Kitchen / ops views
    """

    items = OrderItemReadSerializer(many=True, read_only=True, source="order_items")
    combos = OrderComboReadSerializer(many=True, read_only=True, source="order_combos")
    snacks = OrderSnackReadSerializer(many=True, read_only=True, source="order_snacks")
    addons = OrderAddonReadSerializer(many=True, read_only=True, source="order_addons")

    customer_id = serializers.IntegerField(
        source="customer.id",
        read_only=True
    )

    customer_verified = serializers.SerializerMethodField()

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    total_items = serializers.SerializerMethodField()

    events = OrderEventReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "code",
            "status",
            "status_display",
            "payment_method",
            "total_amount",
            "eta_minutes",
            "is_scheduled",
            "scheduled_for",
            "created_at",
            "customer_id",
            "customer_verified",
            "customer_name",
            "customer_phone",
            "customer_email",
            "customer_address",
            "items",
            "combos",
            "snacks",
            "addons",
            "total_items",
            "events",
        )

    def get_total_items(self, obj):
        return (
            sum(i.quantity for i in obj.order_items.all()) +
            sum(c.quantity for c in obj.order_combos.all()) +
            sum(s.quantity for s in obj.order_snacks.all()) +
            sum(a.quantity for a in obj.order_addons.all())
        )

    def get_customer_verified(self, obj):
        return obj.customer and obj.customer.user is not None


# ======================================================
# ORDER CONFIRMATION
# ======================================================

class OrderConfirmationSerializer(serializers.ModelSerializer):
    """
    Enhanced order confirmation response with all details for instant trust.
    """

    items = OrderItemReadSerializer(many=True, read_only=True, source="order_items")
    combos = OrderComboReadSerializer(many=True, read_only=True, source="order_combos")
    snacks = OrderSnackReadSerializer(many=True, read_only=True, source="order_snacks")
    addons = OrderAddonReadSerializer(many=True, read_only=True, source="order_addons")

    customer_verified = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    whatsapp_update_text = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()

    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "status_display",
            "total_amount",
            "payment_method",
            "payment_method_display",
            "eta_minutes",
            "customer_verified",
            "customer_name",
            "customer_phone",
            "customer_address",
            "items",
            "combos",
            "snacks",
            "addons",
            "total_items",
            "whatsapp_update_text",
            "timeline",
            "created_at",
        )

    def get_customer_verified(self, obj):
        return obj.customer and obj.customer.user is not None

    def get_whatsapp_update_text(self, obj):
        """Generate WhatsApp update text for sharing"""
        base_text = f"🍛 Order {obj.order_number} confirmed!\n"
        base_text += f"📍 ETA: {obj.eta_minutes} minutes\n"
        base_text += f"💰 Payment: {obj.get_payment_method_display()}\n"
        base_text += f"📱 Track your order at: swadoftamil.com/track/{obj.id}\n"
        base_text += f"\nSwad of Tamil - Authentic South Indian Food! 🇮🇳"
        return base_text

    def get_timeline(self, obj):
        """Generate order tracking timeline"""
        events = obj.events.all().order_by('created_at')

        # Define status progression with descriptions
        status_progression = {
            Order.STATUS_PLACED: {
                "title": "Order Placed",
                "description": "Your order has been received",
                "icon": "📝",
                "completed": True
            },
            Order.STATUS_CONFIRMED: {
                "title": "Order Confirmed",
                "description": "Your order has been confirmed and is being prepared",
                "icon": "✅",
                "completed": obj.status in [Order.STATUS_CONFIRMED, Order.STATUS_PREPARING, Order.STATUS_OUT_FOR_DELIVERY, Order.STATUS_DELIVERED]
            },
            Order.STATUS_PREPARING: {
                "title": "Preparing",
                "description": "Our chefs are preparing your delicious meal",
                "icon": "👨‍🍳",
                "completed": obj.status in [Order.STATUS_PREPARING, Order.STATUS_OUT_FOR_DELIVERY, Order.STATUS_DELIVERED]
            },
            Order.STATUS_OUT_FOR_DELIVERY: {
                "title": "Out for Delivery",
                "description": "Your order is on the way!",
                "icon": "🚴",
                "completed": obj.status in [Order.STATUS_OUT_FOR_DELIVERY, Order.STATUS_DELIVERED]
            },
            Order.STATUS_DELIVERED: {
                "title": "Delivered",
                "description": "Enjoy your meal!",
                "icon": "🎉",
                "completed": obj.status == Order.STATUS_DELIVERED
            }
        }

        timeline = []
        for status_key, status_info in status_progression.items():
            # Find the event for this status if it exists
            event = None
            for e in events:
                if e.action == status_key or (status_key == Order.STATUS_PLACED and e.action == "created"):
                    event = e
                    break

            timeline_item = {
                "status": status_key,
                "title": status_info["title"],
                "description": status_info["description"],
                "icon": status_info["icon"],
                "completed": status_info["completed"],
                "timestamp": event.created_at if event else None,
                "note": event.note if event else None
            }
            timeline.append(timeline_item)

        return timeline

    def get_total_items(self, obj):
        return (
            sum(i.quantity for i in obj.order_items.all()) +
            sum(c.quantity for c in obj.order_combos.all()) +
            sum(s.quantity for s in obj.order_snacks.all())
        )


# ======================================================
# ORDER — CREATE SERIALIZER (SHAPE ONLY)
# ======================================================

class OrderCreateSerializer(serializers.Serializer):
    """
    SCALABLE ORDER CREATION: Normalized payload structure.

    Accepts normalized payload:
    {
        "order": {...},
        "order_items": [...],
        "order_addons": [...]
    }
    """
    order = serializers.DictField(required=True)
    order_items = serializers.ListField(required=True)
    order_addons = serializers.ListField(required=False, default=list)

    def validate_order(self, order_data):
        """Validate order-level data"""
        required_fields = ["customer_phone", "customer_address"]
        for field in required_fields:
            if not order_data.get(field, "").strip():
                raise serializers.ValidationError(f"{field} is required")

        # Basic phone validation
        phone = order_data.get("customer_phone", "").strip()
        if not re.match(r"^\+?[0-9]{6,15}$", phone):
            raise serializers.ValidationError("Valid phone number required")

        return order_data

    def validate_order_items(self, items):
        """Validate and normalize order items"""
        if not items:
            raise serializers.ValidationError("At least one item required")

        normalized_items = []
        for item in items:
            item_type = item.get("type")
            if item_type not in ["combo", "item", "snack"]:
                raise serializers.ValidationError(f"Invalid item type: {item_type}")

            try:
                item_id = item["id"]
                quantity = int(item.get("quantity", 1))
                if quantity < 1:
                    raise serializers.ValidationError("Quantity must be ≥ 1")
            except (KeyError, ValueError, TypeError):
                raise serializers.ValidationError("Invalid item id or quantity")

            # Validate addons for this item
            addons = item.get("addons", [])
            validated_addons = []
            for addon in addons:
                if not addon.get("name") or not addon.get("unit_price"):
                    raise serializers.ValidationError("Addon must have name and unit_price")
                validated_addons.append({
                    "name": addon["name"],
                    "category": addon.get("category", ""),
                    "quantity": int(addon.get("quantity", 1)),
                    "unit_price": str(addon["unit_price"])
                })

            normalized_items.append({
                "type": item_type,
                "id": item_id,
                "quantity": quantity,
                "addons": validated_addons
            })

        return normalized_items

    def validate_order_addons(self, addons):
        """Validate global order addons"""
        validated_addons = []
        for addon in addons:
            if not addon.get("name") or not addon.get("unit_price"):
                raise serializers.ValidationError("Global addon must have name and unit_price")
            validated_addons.append({
                "name": addon["name"],
                "category": addon.get("category", ""),
                "quantity": int(addon.get("quantity", 1)),
                "unit_price": str(addon["unit_price"])
            })
        return validated_addons

    def validate(self, data):
        """Cross-field validation"""
        # Ensure at least one item
        if not data.get("order_items"):
            raise serializers.ValidationError("Order must contain at least one item")
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create order using normalized payload"""
        from orders.services import create_order_from_normalized_payload

        payload = {
            "order": validated_data["order"],
            "order_items": validated_data["order_items"],
            "order_addons": validated_data.get("order_addons", [])
        }

        try:
            return create_order_from_normalized_payload(payload)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))


# ======================================================
# CART SERIALIZERS (EPHEMERAL)
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
