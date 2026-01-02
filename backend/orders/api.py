from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import Prefetch
from django.utils.timezone import now
import uuid

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from orders.services import confirm_order, cancel_order
import uuid

def get_role(request):
    # TEMP: replace with real auth later
    return request.headers.get("X-ROLE", "public")

class OrderViewSet(ModelViewSet):
    """
    ERP-safe Order API with:
    - Idempotency
    - Kitchen view
    - Delivery lifecycle
    - Timeline audit
    - Role safety
    """

    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "head", "options"]

    queryset = (
        Order.objects
        .all()
        .order_by("-created_at")
        .prefetch_related(
            Prefetch(
                "items",
                queryset=OrderItem.objects.select_related("prepared_item")
            ),
            "ordered_combos__combo"
        )
    )

    def get_serializer_class(self):
        return (
            OrderCreateSerializer
            if self.action == "create"
            else OrderSerializer
        )

    def create(self, request, *args, **kwargs):
        key = request.headers.get("Idempotency-Key")

        if key:
            existing = Order.objects.filter(idempotency_key=key).first()
            if existing:
                return Response(
                    OrderSerializer(existing).data,
                    status=status.HTTP_200_OK
                )

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        if key:
            order.idempotency_key = key
            order.save(update_fields=["idempotency_key"])

        self._log(order, "created", request)
        return Response(OrderSerializer(order).data, status=201)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """
        Server-assisted checkout (dev stub)
        Creates a PENDING order and returns a payment_session token.
        Frontend should open payment UI with the returned `payment_session`.
        """
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # generate a dev payment session token (not persisted)
        payment_session = str(uuid.uuid4())

        self._log(order, "checkout:initiated", request)
        return Response({
            "order": OrderSerializer(order).data,
            "payment_session": payment_session,
        }, status=201)

    @action(detail=False, methods=["post"])
    def checkout_confirm(self, request):
        """
        Confirm order after payment. Expects { order_id, payment_session }.
        In this dev implementation we accept any session and confirm the PENDING order.
        """
        order_id = request.data.get("order_id")
        session = request.data.get("payment_session")

        if not order_id:
            return Response({"error": "order_id required"}, status=400)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=order_id)

                if order.status != Order.STATUS_PENDING:
                    return Response({"error": "Invalid state"}, status=400)

                # In a real integration verify the session with the payment provider here.
                confirm_order(order)
                self._log(order, "checkout:confirmed", request)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        if get_role(request) != "admin":
            return Response({"error": "Forbidden"}, status=403)

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=pk)

            if order.status != Order.STATUS_PENDING:
                return Response({"error": "Invalid state"}, status=400)

            confirm_order(order)
            self._log(order, "confirmed", request)

        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if get_role(request) != "admin":
            return Response({"error": "Forbidden"}, status=403)

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=pk)

            if order.status != Order.STATUS_CONFIRMED:
                return Response({"error": "Invalid state"}, status=400)

            cancel_order(order)
            self._log(order, "cancelled", request)

        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=["get"])
    def kitchen(self, request):
        if get_role(request) not in ("kitchen", "admin"):
            return Response({"error": "Forbidden"}, status=403)

        orders = self.get_queryset().filter(status=Order.STATUS_CONFIRMED)

        data = [
            {
                "order_id": o.id,
                "created_at": o.created_at,
                "items": [
                    {
                        "item": i.prepared_item.name,
                        "qty": i.quantity
                    }
                    for i in o.items.all()
                ]
            }
            for o in orders
        ]

        return Response(data)

    @action(detail=True, methods=["post"])
    def delivery_state(self, request, pk=None):
        if get_role(request) not in ("delivery", "admin"):
            return Response({"error": "Forbidden"}, status=403)

        state = request.data.get("state")
        if state not in ("packed", "out_for_delivery", "delivered"):
            return Response({"error": "Invalid state"}, status=400)

        order = self.get_object()
        self._log(order, f"delivery:{state}", request)

        return Response({"status": state})

    def _log(self, order, action, request):
        timeline = getattr(order, "timeline", []) or []
        timeline.append({
            "id": str(uuid.uuid4()),
            "action": action,
            "by": get_role(request),
            "at": now().isoformat()
        })
        order.timeline = timeline
        order.save(update_fields=["timeline"])
