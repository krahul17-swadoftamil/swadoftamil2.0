import logging
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils.timezone import now

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Order, OrderItem
from .serializers import (
    OrderReadSerializer,
    OrderCreateSerializer,
    OrderConfirmationSerializer,
)
from orders.services import confirm_order, cancel_order
from orders.personalization import personalization_service

logger = logging.getLogger(__name__)


# ======================================================
# TEMP ROLE RESOLUTION (REPLACE WITH AUTH LATER)
# ======================================================
def get_role(request):
    return request.headers.get("X-ROLE", "public")


# ======================================================
# ORDER API — SINGLE SOURCE OF TRUTH
# ======================================================
class OrderViewSet(ModelViewSet):
    """
    ERP-safe Order API

    ✔ Create PENDING orders (COD / Online)
    ✔ Read orders
    ✔ Confirm (stock deduction)
    ✔ Cancel (no restore)
    ✔ Kitchen feed
    """

    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "head", "options"]

    queryset = (
        Order.objects
        .all()
        .order_by("-created_at")
        .prefetch_related(
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.select_related("prepared_item")
            ),
            "order_combos__combo",
            "order_snacks",
            "events",
        )
    )

    # --------------------------------------------------
    # SERIALIZER SELECTION
    # --------------------------------------------------
    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    # --------------------------------------------------
    # CREATE ORDER (PENDING ONLY)
    # --------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            # Convert validation errors to user-friendly messages
            errors = serializer.errors
            user_friendly_errors = []
            
            for field, messages in errors.items():
                if field == 'phone':
                    user_friendly_errors.append("Please provide a valid phone number")
                elif field == 'address':
                    user_friendly_errors.append("Please provide a delivery address")
                elif field == 'combos' or field == 'snacks':
                    user_friendly_errors.append("Please add items to your order")
                else:
                    user_friendly_errors.extend([str(msg) for msg in messages])
            
            return Response(
                {"error": " · ".join(user_friendly_errors)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = serializer.save()
        except Exception as e:
            logger.exception("Order creation failed")
            # Never show system errors to customers
            return Response(
                {"error": "Unable to process order. Please try again or contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            OrderConfirmationSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    # --------------------------------------------------
    # CONFIRM ORDER (ADMIN / SYSTEM)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        if get_role(request) not in ("admin", "system"):
            return Response({"error": "Forbidden"}, status=403)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)

                if order.status != Order.STATUS_PENDING:
                    return Response(
                        {"error": "Only pending orders can be confirmed"},
                        status=400,
                    )

                confirm_order(order)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Exception as e:
            logger.exception("Order confirm failed")
            return Response(
                {"error": str(e)} if settings.DEBUG else {"error": "Confirm failed"},
                status=500,
            )

        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # CANCEL ORDER (ADMIN / SYSTEM)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if get_role(request) not in ("admin", "system"):
            return Response({"error": "Forbidden"}, status=403)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=pk)

                if order.status == Order.STATUS_CANCELLED:
                    return Response(
                        {"error": "Order already cancelled"},
                        status=400,
                    )

                cancel_order(order)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        except Exception as e:
            logger.exception("Order cancel failed")
            return Response(
                {"error": str(e)} if settings.DEBUG else {"error": "Cancel failed"},
                status=500,
            )

        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # STATUS ENDPOINT (FRONTEND POLLING)
    # --------------------------------------------------
    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        try:
            order = self.get_object()
            return Response({
                "id": order.id,
                "status": order.status,
                "status_display": order.get_status_display(),
                "eta_minutes": order.eta_minutes,
                "created_at": order.created_at,
                "updated_at": order.created_at,  # For now, use created_at
            })
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

    # --------------------------------------------------
    # KITCHEN VIEW (CONFIRMED ORDERS ONLY)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def kitchen(self, request):
        if get_role(request) not in ("kitchen", "admin"):
            return Response({"error": "Forbidden"}, status=403)

        orders = (
            self.get_queryset()
            .filter(status=Order.STATUS_CONFIRMED)
            .order_by("created_at")
        )

        data = [
            {
                "order_number": o.order_number,
                "created_at": o.created_at,
                "items": [
                    {
                        "name": i.prepared_item.name,
                        "quantity": i.quantity,
                    }
                    for i in o.items.all()
                ],
            }
            for o in orders
        ]

        return Response(data)

    # --------------------------------------------------
    # LIST BY STATUS (OPS / DASHBOARD)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status")

        qs = self.get_queryset()
        if status_param:
            qs = qs.filter(status=status_param)

        return Response(
            OrderReadSerializer(qs, many=True).data
        )

    # --------------------------------------------------
    # STORE STATUS (TIMING INFO FOR FRONTEND)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def store_status(self, request):
        """Get current store status for frontend timing display"""
        from core.utils import get_store_status, next_opening_datetime
        
        try:
            status = get_store_status()
            
            # Enhance with user-friendly messages
            if not status.get('is_open', False):
                next_open = next_opening_datetime()
                if next_open:
                    status['message'] = f"Currently closed · Opens at {next_open.strftime('%I:%M %p')}"
                else:
                    status['message'] = "Currently closed"
            else:
                status['message'] = "Open for orders"
            
            return Response(status)
            
        except Exception as e:
            # Never show system errors to customers
            return Response({
                'is_open': False,
                'accept_orders': False,
                'kitchen_active': False,
                'master_switch': False,
                'shifts_active': False,
                'current_shift': None,
                'message': 'Service temporarily unavailable',
                'next_opening': None,
                'order_cutoff': None,
                'calendar_exception': None,
            })

    # --------------------------------------------------
    # ORDER PREVIEW (DETAILED BREAKDOWN)
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Preview order with detailed breakdown before creation"""
        from orders.serializers import OrderCreateSerializer
        
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated data
        data = serializer.validated_data
        
        # Calculate preview
        preview = self._calculate_order_preview(data)
        
        return Response(preview)

    def _calculate_order_preview(self, data):
        """Calculate detailed order preview"""
        from menu.models import Combo, PreparedItem
        from decimal import Decimal
        
        combos_data = []
        total_amount = Decimal('0.00')
        
        # Process combos
        for combo_item in data.get('combos', []):
            combo_id = combo_item['combo_id']
            quantity = combo_item['quantity']
            
            try:
                combo = Combo.objects.get(id=combo_id, is_active=True)
            except Combo.DoesNotExist:
                continue
            
            combo_total = combo.selling_price * quantity
            total_amount += combo_total
            
            # Get combo items breakdown
            items_breakdown = []
            for combo_item_obj in combo.items.all():
                prepared_item = combo_item_obj.prepared_item
                if prepared_item:
                    item_quantity = combo_item_obj.quantity * quantity
                    items_breakdown.append({
                        'id': str(prepared_item.id),
                        'name': prepared_item.name,
                        'quantity': float(item_quantity),
                        'unit': prepared_item.unit,
                        'unit_cost': float(prepared_item.cost_price_cached),
                        'total_cost': float(prepared_item.cost_price_cached * item_quantity),
                    })
            
            combos_data.append({
                'id': str(combo.id),
                'name': combo.name,
                'quantity': quantity,
                'unit_price': float(combo.selling_price),
                'total_price': float(combo_total),
                'items': items_breakdown,
                'addons': [],  # For future addon support
            })
        
        # Process snacks (simplified)
        snacks_data = []
        for snack_item in data.get('snacks', []):
            snack_id = snack_item['snack_id']
            quantity = snack_item['quantity']
            
            # For now, just add basic info - in real implementation, get from Snack model
            snacks_data.append({
                'id': snack_id,
                'name': f'Snack {snack_id}',  # Placeholder
                'quantity': quantity,
                'unit_price': 0.00,  # Placeholder
                'total_price': 0.00,  # Placeholder
            })
        
        return {
            'combos': combos_data,
            'snacks': snacks_data,
            'total_amount': float(total_amount),
            'payment_mode': data.get('payment_mode', 'cod'),
            'customer': {
                'phone': data.get('phone'),
                'address': data.get('address'),
                'name': data.get('customer_name', ''),
                'email': data.get('customer_email', ''),
            }
        }

    # --------------------------------------------------
    # ORDER TRACKING (PUBLIC)
    # --------------------------------------------------
    @action(detail=True, methods=["get"])
    def track(self, request, pk=None):
        """Public order tracking endpoint"""
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(OrderConfirmationSerializer(order).data)

    # --------------------------------------------------
    # STATUS UPDATES (ADMIN/SYSTEM)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update order status (admin/system only)"""
        if get_role(request) not in ("admin", "system"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        note = request.data.get("note", "")

        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate status transition
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid options: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status and create event
        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status"])

        OrderEvent.objects.create(
            order=order,
            action=new_status,
            note=note or f"Status changed from {old_status} to {new_status}"
        )

        return Response(OrderConfirmationSerializer(order).data)

    # --------------------------------------------------
    # PERSONALIZED SUGGESTIONS
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def suggestions(self, request):
        """Get personalized combo/item suggestions for the current customer"""
        # Try to get customer from session (if authenticated)
        customer = None
        if request.user.is_authenticated:
            try:
                customer = request.user.customer_profile
            except:
                pass

        # If no authenticated customer, try to get from phone parameter
        if not customer:
            phone = request.query_params.get('phone')
            if phone:
                from accounts.models import Customer
                try:
                    customer = Customer.objects.get(phone=phone)
                except Customer.DoesNotExist:
                    pass

        # Get suggestions
        suggestions = personalization_service.get_personalized_suggestions(customer)

        return Response(suggestions)
