from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import Order, OrderItem
from .serializers import OrderReadSerializer, OrderCreateSerializer
from orders.services import confirm_order, cancel_order
from .serializers import CartSerializer
from .models import Cart
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


class OrderViewSet(ModelViewSet):
    """
    ORDER API (ERP-SAFE)

    ✔ Create pending orders
    ✔ Read orders
    ✔ Confirm (deduct stock)
    ✔ Cancel (NO stock restore)
    """

    permission_classes = [AllowAny]  # auth later

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

    # --------------------------------------------------
    # SERIALIZER SELECTION
    # --------------------------------------------------
    def get_serializer_class(self):
        return (
            OrderCreateSerializer
            if self.action == "create"
            else OrderReadSerializer
        )

    # --------------------------------------------------
    # CREATE ORDER (PENDING ONLY)
    # --------------------------------------------------
    def create(self, request, *args, **kwargs):
        # DEBUG: log incoming payload to help trace 500 errors during development
        try:
            print("[DEBUG] Incoming order payload:", request.data)
        except Exception:
            pass

        serializer = OrderCreateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            order = serializer.save()  # must create PENDING order only
        except Exception as e:
            # Print traceback to server logs for debugging
            import traceback
            trace = traceback.format_exc()
            print(trace)
            # If running in DEBUG, return traceback in response to aid dev debugging
            try:
                from django.conf import settings
                if getattr(settings, "DEBUG", False):
                    return Response({"detail": "Internal server error while creating order.", "trace": trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception:
                pass

            return Response({"detail": "Internal server error while creating order. Check server logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            OrderReadSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    # --------------------------------------------------
    # CONFIRM ORDER (STOCK DEDUCTION)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = self.get_object()

        if order.status != Order.STATUS_PENDING:
            return Response(
                {"error": "Only pending orders can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            confirm_order(order)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # CANCEL ORDER (NO RESTORE)
    # --------------------------------------------------
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()

        if order.status == Order.STATUS_CANCELLED:
            return Response(
                {"error": "Order already cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cancel_order(order)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(OrderReadSerializer(order).data)

    # --------------------------------------------------
    # FILTER BY STATUS
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def by_status(self, request):
        """
        /api/orders/by_status/?status=pending
        """
        status_param = request.query_params.get("status")

        qs = self.get_queryset()
        if status_param:
            qs = qs.filter(status=status_param)

        return Response(
            OrderReadSerializer(qs, many=True).data
        )

    # --------------------------------------------------
    # ORDER SUMMARY (READ-ONLY)
    # --------------------------------------------------
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        order = self.get_object()

        total_items = sum(item.quantity for item in order.items.all())

        return Response({
            "order_id": order.id,
            "status": order.status,
            "status_display": order.get_status_display(),
            "created_at": order.created_at,
            "total_amount": order.total_amount,
            "total_items": total_items,
            "prepared_items": [
                {
                    "name": item.prepared_item.name,
                    "quantity": item.quantity,
                }
                for item in order.items.all()
            ],
            "combos": [
                {
                    "name": oc.combo.name,
                    "quantity": oc.quantity,
                }
                for oc in order.ordered_combos.all()
            ],
        })

def latest_order(request):
    order = Order.objects.order_by("-created_at").first()
    return JsonResponse({"id": order.id if order else None})


def kitchen_screen(request):
    orders = (
        Order.objects
        .filter(status="pending")
        .prefetch_related("items__prepared_item")
        .order_by("created_at")
    )
    return render(request, "orders/kitchen_screen.html", {"orders": orders})


def print_slip(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__prepared_item"),
        pk=order_id
    )
    return render(request, "orders/print_slip.html", {"order": order})

@api_view(["POST"])
def create_order(request):
    """
    POST /api/orders/
    Checkout endpoint
    """
    # Validate and create a real Order using the serializer.
    try:
        print("[DEBUG] Incoming order payload:", request.data)
    except Exception:
        pass

    serializer = OrderCreateSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        # If customer info present in payload, ensure Customer exists
        data = serializer.validated_data
        customer_data = {
            'phone': data.get('customer_phone') or request.data.get('customer_phone'),
            'name': data.get('customer_name') or request.data.get('customer_name'),
            'email': data.get('customer_email') or request.data.get('customer_email'),
        }

        from accounts.models import Customer

        customer = None
        try:
            if customer_data.get('phone'):
                customer, _ = Customer.objects.get_or_create(phone=customer_data['phone'], defaults={
                    'name': customer_data.get('name') or '',
                    'email': customer_data.get('email') or '',
                })
        except Exception:
            customer = None

        order = serializer.save()
        if customer and getattr(order, 'customer', None) is None:
            order.customer = customer
            order.customer_name = customer.name or order.customer_name
            order.customer_phone = customer.phone or order.customer_phone
            order.customer_email = customer.email or order.customer_email
            order.save(update_fields=['customer', 'customer_name', 'customer_phone', 'customer_email'])
    except Exception:
        import traceback
        trace = traceback.format_exc()
        print(trace)
        try:
            from django.conf import settings
            if getattr(settings, "DEBUG", False):
                return Response({"detail": "Internal server error while creating order.", "trace": trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception:
            pass

        return Response({"detail": "Internal server error while creating order. Check server logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        OrderReadSerializer(order).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])
def cart_view(request):
    """Simple cart endpoint:
    - GET /api/orders/cart/?session=<key> or ?customer=<phone>
    - POST /api/orders/cart/  -> create or update cart (accepts id to update)
    - DELETE /api/orders/cart/?id=<cart_id>
    """
    # GET
    if request.method == "GET":
        session = request.query_params.get("session")
        customer = request.query_params.get("customer")

        qs = Cart.objects.all()
        if session:
            cart = qs.filter(session_key=session).order_by("-updated_at").first()
        elif customer:
            cart = qs.filter(customer__phone=customer).order_by("-updated_at").first()
        else:
            return Response([], status=status.HTTP_200_OK)

        if not cart:
            return Response({}, status=status.HTTP_200_OK)

        return Response(CartSerializer(cart).data)

    # DELETE
    if request.method == "DELETE":
        cid = request.query_params.get("id")
        if not cid:
            return Response({"error": "id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            c = Cart.objects.get(pk=cid)
            c.delete()
            return Response({"deleted": True})
        except Cart.DoesNotExist:
            return Response({"deleted": False}, status=status.HTTP_404_NOT_FOUND)

    # POST - create or update
    if request.method == "POST":
        data = request.data
        cid = data.get("id")
        if cid:
            try:
                cart = Cart.objects.get(pk=cid)
            except Cart.DoesNotExist:
                return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = CartSerializer(cart, data=data, partial=True)
        else:
            serializer = CartSerializer(data=data)

        serializer.is_valid(raise_exception=True)
        cart = serializer.save()
        return Response(CartSerializer(cart).data)
    
@api_view(["POST"])
def add_address(request):
    customer_id = request.data.get("customer_id")

    customer = Customer.objects.get(id=customer_id)

    if request.data.get("is_default"):
        Address.objects.filter(customer=customer).update(is_default=False)

    address = Address.objects.create(
        customer=customer,
        line1=request.data["line1"],
        city=request.data["city"],
        pincode=request.data["pincode"],
        is_default=request.data.get("is_default", False),
    )

    return Response({"id": address.id})    