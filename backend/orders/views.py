from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django.db.models import Prefetch
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import (
    Order,
    OrderItem,
    OrderCombo,
    OrderSnack,
    OrderAddon,
    Cart,
    Address,
)
from .serializers import (
    OrderReadSerializer,
    OrderCreateSerializer,
    CartSerializer,
)
from orders.services import process_scheduled_orders, check_scheduled_orders
from accounts.models import Customer


# ==========================================================
# ORDER VIEWSET (RESTful)
# ==========================================================
class OrderViewSet(ModelViewSet):
    """
    ORDER API (ERP-SAFE)
    ✔ Create pending orders
    ✔ Read orders
    ✔ Confirm (deduct stock)
    ✔ Cancel (no restore)
    """

    permission_classes = [AllowAny]

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
        )
    )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    # --------------------------------------------------
    # UPDATE ORDER STATUS
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        
        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transitions
        valid_transitions = {
            Order.STATUS_PLACED: [Order.STATUS_CONFIRMED, Order.STATUS_CANCELLED],
            Order.STATUS_CONFIRMED: [Order.STATUS_PREPARING, Order.STATUS_CANCELLED],
            Order.STATUS_PREPARING: [Order.STATUS_OUT_FOR_DELIVERY, Order.STATUS_CANCELLED],
            Order.STATUS_OUT_FOR_DELIVERY: [Order.STATUS_DELIVERED],
            Order.STATUS_DELIVERED: [],  # Final state
            Order.STATUS_CANCELLED: [],  # Final state
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {"error": f"Cannot change status from {order.status} to {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save(update_fields=["status"])
        
        # Create event
        from orders.models import OrderEvent
        OrderEvent.objects.create(
            order=order,
            action="status_changed",
            note=f"Status changed to {new_status}"
        )
        
        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # CONFIRM ORDER (LEGACY)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        # Clone request with status
        request._data = request.data.copy()
        request._data["status"] = Order.STATUS_CONFIRMED
        return self.update_status(request)

    # --------------------------------------------------
    # CANCEL ORDER
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()

        if order.status == Order.STATUS_CANCELLED:
            return Response(
                {"error": "Order already cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancel_order(order)
        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # PROCESS SCHEDULED ORDERS (ADMIN/KITCHEN)
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def process_scheduled(self, request):
        """Process all scheduled orders that are ready for preparation"""
        try:
            process_scheduled_orders()
            return Response({"message": "Scheduled orders processed successfully"})
        except Exception as e:
            return Response(
                {"error": f"Failed to process scheduled orders: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # --------------------------------------------------
    # CHECK SCHEDULED ORDERS (ADMIN/KITCHEN)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def scheduled_status(self, request):
        """Get status of scheduled orders"""
        scheduled_orders = check_scheduled_orders()
        return Response({
            "ready_count": scheduled_orders.count(),
            "orders": [
                {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "scheduled_for": order.scheduled_for,
                    "customer_name": order.customer_name,
                    "total_amount": str(order.total_amount)
                }
                for order in scheduled_orders
            ]
        })

    # --------------------------------------------------
    # PREPARE ORDER (KITCHEN)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def prepare(self, request, pk=None):
        """Manually start preparation for a confirmed order"""
        from orders.services import prepare_order
        
        order = self.get_object()
        
        try:
            prepare_order(order)
            return Response(OrderReadSerializer(order).data)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    # --------------------------------------------------
    # GET ORDER STATUS
    # --------------------------------------------------
    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        order = self.get_object()
        return Response({
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "eta_minutes": order.eta_minutes,
            "created_at": order.created_at,
            "tracking_code": order.tracking_code,
        })

    # --------------------------------------------------
    # FILTER BY STATUS
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status")
        qs = self.get_queryset()

        if status_param:
            qs = qs.filter(status=status_param)

        return Response(OrderReadSerializer(qs, many=True).data)

    # --------------------------------------------------
    # ORDER SUMMARY (LIGHTWEIGHT)
    # --------------------------------------------------
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        order = self.get_object()

        total_items = (
            sum(i.quantity for i in order.order_items.all()) +
            sum(c.quantity for c in order.order_combos.all())
        )

        return Response({
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "status_display": order.get_status_display(),
            "created_at": order.created_at,
            "total_amount": order.total_amount,
            "total_items": total_items,
        })


# ==========================================================
# FUNCTION-BASED VIEWS (LEGACY FRONTEND SUPPORT)
# ==========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def search_orders(request):
    """
    Search orders by phone number.
    Used by MyOrders page.
    """
    phone = request.data.get("phone", "").strip()
    if not phone:
        return Response(
            {"error": "Phone number is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    orders = Order.objects.filter(
        customer_phone=phone
    ).order_by("-created_at")[:20]

    serializer = OrderReadSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    """
    Function-based checkout endpoint for legacy frontend routes.
    Supports idempotency via X-Idempotency-Key header.
    """
    try:
        print("[DEBUG] Incoming order payload:", request.data)
    except Exception:
        pass

    # Idempotency check
    idempotency_key = request.headers.get("X-Idempotency-Key")
    if idempotency_key:
        existing = Order.objects.filter(
            metadata__idempotency_key=idempotency_key
        ).first()
        if existing:
            return Response(
                OrderReadSerializer(existing).data,
                status=status.HTTP_200_OK
            )

    # Prepare request data
    request_data = dict(request.data)
    if idempotency_key:
        request_data["metadata"] = {"idempotency_key": idempotency_key}

    serializer = OrderCreateSerializer(data=request_data)
    serializer.is_valid(raise_exception=True)
    order = serializer.save()

    return Response(
        OrderReadSerializer(order).data,
        status=status.HTTP_201_CREATED
    )


# ==========================================================
# CART VIEWS
# ==========================================================
@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])
def cart_view(request):
    """
    /api/orders/cart/
    """
    if request.method == "GET":
        session = request.query_params.get("session")
        phone = request.query_params.get("customer")

        qs = Cart.objects.all()
        cart = None

        if session:
            cart = qs.filter(session_key=session).first()
        elif phone:
            cart = qs.filter(customer__phone=phone).first()

        return Response(
            CartSerializer(cart).data if cart else {},
            status=status.HTTP_200_OK
        )

    elif request.method == "DELETE":
        cid = request.query_params.get("id")
        if not cid:
            return Response({"error": "id required"}, status=status.HTTP_400_BAD_REQUEST)

        Cart.objects.filter(pk=cid).delete()
        return Response({"deleted": True}, status=status.HTTP_200_OK)

    # POST — Create/Update
    serializer = CartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cart = serializer.save()

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# ==========================================================
# OTHER SIMPLE VIEWS
# ==========================================================
def latest_order(request):
    order = Order.objects.order_by("-created_at").first()
    return JsonResponse({"id": order.id if order else None})


def kitchen_screen(request):
    orders = (
        Order.objects
        .filter(status=Order.STATUS_PENDING)
        .prefetch_related("order_items__prepared_item")
        .order_by("created_at")
    )
    return render(request, "orders/kitchen_screen.html", {"orders": orders})


def print_slip(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("order_items__prepared_item"),
        pk=order_id
    )
    return render(request, "orders/print_slip.html", {"order": order})


# ==========================================================
# ADDRESS HANDLING
# ==========================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def add_address(request):
    customer_id = request.data.get("customer_id")
    customer = get_object_or_404(Customer, id=customer_id)

    if request.data.get("is_default"):
        Address.objects.filter(customer=customer).update(is_default=False)

    address = Address.objects.create(
        customer=customer,
        line1=request.data["line1"],
        city=request.data["city"],
        pincode=request.data["pincode"],
        is_default=request.data.get("is_default", False),
    )

    return Response({"id": address.id}, status=status.HTTP_201_CREATED)


# ==========================================================
# ORDER DETAIL (LEGACY)
# ==========================================================
def order_detail(request, order_id):
    from .serializers import OrderReadSerializer
    order = get_object_or_404(
        Order.objects.prefetch_related(
            Prefetch(
                "order_items",
                queryset=OrderItem.objects.select_related("prepared_item")
            ),
            "order_combos__combo",
            "order_snacks",
            "events",
        ),
        id=order_id
    )
    serializer = OrderReadSerializer(order)
    return JsonResponse(serializer.data)
