from decimal import Decimal
import re
from uuid import UUID

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from orders.models import (
    Order,
    OrderCombo,
    OrderItem,
    OrderSnack,
    OrderAddon,
    OrderEvent,
)
from menu.models import Combo, PreparedItem
from snacks.models import Snack
from ingredients.models import Ingredient
from accounts.models import Customer
from accounts.sms import send_sms

ZERO = Decimal("0.00")
PHONE_RE = re.compile(r"^\+?[0-9]{6,15}$")

# ======================================================
# LEGACY FUNCTIONS (DEPRECATED)
# ======================================================

# Old create_order_from_payload function removed - use create_order_from_normalized_payload


def check_menu_availability(order_items: list) -> dict:
    """
    DECOUPLED: Check menu availability without affecting order placement.

    Returns:
    {
        "available": bool,
        "total_amount": Decimal,
        "unavailable_items": list
    }
    """
    from menu.models import Combo, PreparedItem
    from snacks.models import Snack

    total_amount = ZERO
    unavailable_items = []

    for item in order_items:
        item_type = item["type"]
        item_id = item["id"]
        quantity = item["quantity"]

        try:
            if item_type == "combo":
                combo = Combo.objects.get(id=item_id, is_active=True)
                total_amount += combo.selling_price * quantity
            elif item_type == "item":
                prepared_item = PreparedItem.objects.get(id=item_id, is_active=True)
                # Note: PreparedItem doesn't have selling_price, need to calculate from recipes
                # For now, assume it's available
                pass
            elif item_type == "snack":
                snack = Snack.objects.get(id=int(item_id), is_active=True)
                total_amount += snack.selling_price * quantity
            else:
                unavailable_items.append(f"Unknown item type: {item_type}")
                continue
        except Exception as e:
            unavailable_items.append(f"{item_type} {item_id}: {str(e)}")
            continue

        # Check addons availability
        for addon in item.get("addons", []):
            total_amount += Decimal(str(addon.get("unit_price", "0"))) * addon.get("quantity", 1)

    return {
        "available": len(unavailable_items) == 0,
        "total_amount": total_amount,
        "unavailable_items": unavailable_items
    }


def calculate_scheduled_time() -> timezone.datetime:
    """
    Calculate when a scheduled order should be prepared/delivered.

    Returns the next opening time of the store.
    """
    from core.utils import next_opening_datetime
    return next_opening_datetime()


def create_order_items_and_addons(order: Order, order_items: list):
    """
    Create OrderItem, OrderCombo, OrderSnack, and OrderAddon records.
    """
    from menu.models import Combo, PreparedItem
    from snacks.models import Snack

    combos_to_create = []
    items_to_create = []
    snacks_to_create = []
    addons_to_create = []

    for item in order_items:
        item_type = item["type"]
        item_id = item["id"]
        quantity = item["quantity"]

        if item_type == "combo":
            combo = Combo.objects.get(id=item_id)
            combos_to_create.append(OrderCombo(
                order=order,
                combo=combo,
                quantity=quantity
            ))
            parent_type = "combo"
            parent_id = item_id

        elif item_type == "item":
            prepared_item = PreparedItem.objects.get(id=item_id)
            items_to_create.append(OrderItem(
                order=order,
                prepared_item=prepared_item,
                quantity=quantity
            ))
            parent_type = "item"
            parent_id = item_id

        elif item_type == "snack":
            snack = Snack.objects.get(id=int(item_id))
            snacks_to_create.append(OrderSnack(
                order=order,
                snack_id=snack.id,
                snack_name=snack.name,
                quantity=quantity,
                unit_price=snack.selling_price
            ))
            parent_type = "snack"
            parent_id = item_id

        # Create addons for this item
        for addon in item.get("addons", []):
            addons_to_create.append(OrderAddon(
                order=order,
                order_item_type=parent_type,
                combo_id=parent_id if parent_type == "combo" else None,
                prepared_item_id=parent_id if parent_type == "item" else None,
                snack_id=int(parent_id) if parent_type == "snack" else None,
                addon_name=addon["name"],
                addon_category=addon.get("category", ""),
                quantity=addon.get("quantity", 1),
                unit_price=Decimal(str(addon["unit_price"]))
            ))

    # Bulk create all items
    OrderCombo.objects.bulk_create(combos_to_create)
    OrderItem.objects.bulk_create(items_to_create)
    OrderSnack.objects.bulk_create(snacks_to_create)
    OrderAddon.objects.bulk_create(addons_to_create)


def handle_customer_creation(order: Order, order_data: dict):
    """
    Handle customer creation and linking.
    """
    phone = (order_data.get("customer_phone") or "").strip()

    if phone and PHONE_RE.match(phone):
        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={
                "name": order_data.get("customer_name", ""),
                "email": order_data.get("customer_email", ""),
            }
        )

        # Send welcome OTP for new customers
        if created:
            send_welcome_otp(customer)

        order.customer = customer
        order.save(update_fields=["customer"])


def setup_payment_and_tracking(order: Order):
    """
    Setup payment method specific handling and tracking.
    """
    if order.payment_method == Order.PAYMENT_METHOD_COD:
        short = str(order.id)[:8]
        order.tracking_code = f"COD-{timezone.now().year}-{short}"
        order.save(update_fields=["tracking_code"])

        if order.customer_phone:
            try:
                send_sms(
                    order.customer_phone,
                    f"Order {order.order_number} placed. "
                    f"Tracking {order.tracking_code} – Swad of Tamil"
                )
            except Exception:
                pass


def create_order_events(order: Order, is_scheduled: bool):
    """
    Create initial order events and notifications.
    """
    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_PLACED,
        note="Order placed" + (" (scheduled)" if is_scheduled else "")
    )

    # For immediate orders, auto-confirm but don't prepare yet
    # Preparation is handled separately by prepare_order()
    if not is_scheduled:
        order.status = Order.STATUS_CONFIRMED
        order.save(update_fields=["status"])

        OrderEvent.objects.create(
            order=order,
            action=Order.STATUS_CONFIRMED,
            note="Order auto-confirmed"
        )


def send_welcome_otp(customer: Customer):
    """
    Send welcome OTP to new customers.
    """
    from accounts.models import OTP
    from accounts.sms import send_sms
    from django.utils import timezone
    from datetime import timedelta
    import threading

    def _send_otp():
        try:
            # Invalidate existing OTPs
            OTP.objects.filter(phone=customer.phone, is_used=False).update(is_used=True)

            # Generate new OTP
            import random
            code = f"{random.randint(100000, 999999)}"

            otp = OTP.objects.create(
                phone=customer.phone,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            # Send SMS
            sms_sent = send_sms(customer.phone, f"Welcome to Swad of Tamil! Your verification code is {otp.code}")

            print(f"Welcome OTP sent to {customer.phone}: {code} (SMS: {sms_sent})")

        except Exception as e:
            print(f"Failed to send welcome OTP: {e}")

    # Send in background thread
    thread = threading.Thread(target=_send_otp, daemon=True)
    thread.start()


@transaction.atomic
def create_order_from_normalized_payload(payload: dict) -> Order:
    """
    SCALABLE ORDER CREATION: Normalized payload structure.

    Payload structure:
    {
        "order": {
            "payment_method": "cod|online",
            "customer_name": str,
            "customer_phone": str,
            "customer_email": str,
            "customer_address": str,
            "metadata": dict
        },
        "order_items": [
            {
                "type": "combo|item|snack",
                "id": str|int,
                "quantity": int,
                "addons": [...]  # optional
            }
        ],
        "order_addons": [...]  # optional global addons
    }
    """
    from core.utils import store_runtime_status

    # Extract payload sections
    order_data = payload.get("order", {})
    order_items = payload.get("order_items", [])
    order_addons = payload.get("order_addons", [])

    if not order_items:
        raise ValidationError("Order must contain at least one item")

    # Check store status for scheduling decision
    store_status = store_runtime_status()
    is_scheduled = not store_status["accept_orders"]

    # 1. MENU AVAILABILITY CHECK (DECOUPLED)
    menu_availability = check_menu_availability(order_items)
    if not menu_availability["available"]:
        raise ValidationError(f"Menu items unavailable: {menu_availability['unavailable_items']}")

    total_amount = menu_availability["total_amount"]

    # Add global addons to total
    for addon in order_addons:
        total_amount += Decimal(str(addon.get("unit_price", "0"))) * addon.get("quantity", 1)

    # 2. ORDER PLACEMENT (DECOUPLED FROM AVAILABILITY)
    order = Order.objects.create(
        status=Order.STATUS_PLACED,
        total_amount=total_amount,
        payment_method=order_data.get("payment_method", "cod"),
        customer_name=order_data.get("customer_name", ""),
        customer_phone=order_data.get("customer_phone", ""),
        customer_email=order_data.get("customer_email", ""),
        customer_address=order_data.get("customer_address", ""),
        metadata={
            **order_data.get("metadata", {}),
            "is_scheduled": is_scheduled,
            "scheduled_for": calculate_scheduled_time().isoformat() if is_scheduled else None,
        }
    )

    # 3. CREATE ORDER ITEMS AND ADDONS
    create_order_items_and_addons(order, order_items)

    # Create global addons
    global_addons = []
    for addon in order_addons:
        global_addons.append(OrderAddon(
            order=order,
            order_item_type="global",  # Global addons not tied to specific items
            addon_name=addon["name"],
            addon_category=addon.get("category", ""),
            quantity=addon.get("quantity", 1),
            unit_price=Decimal(str(addon["unit_price"]))
        ))
    OrderAddon.objects.bulk_create(global_addons)

    # 4. HANDLE CUSTOMER
    handle_customer_creation(order, order_data)

    # 5. SETUP PAYMENT AND TRACKING
    setup_payment_and_tracking(order)

    # 6. CREATE EVENTS AND NOTIFICATIONS
    create_order_events(order, is_scheduled)

    return order


# ======================================================
# PREPARATION SERVICE (DECOUPLED)
# ======================================================

@transaction.atomic
def prepare_order(order: Order):
    """
    DECOUPLED: Handle order preparation (stock deduction, status updates).

    This can be called:
    - Immediately for regular orders
    - At scheduled time for scheduled orders
    - Manually by kitchen staff
    """
    if order.status != Order.STATUS_CONFIRMED:
        raise ValidationError("Only confirmed orders can be prepared")

    # Deduct stock for all order items
    order.confirm_order()  # This handles stock deduction

    # Update status to preparing
    order.status = Order.STATUS_PREPARING
    order.save(update_fields=["status"])

    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_PREPARING,
        note="Order preparation started"
    )


def check_scheduled_orders():
    """
    Check for scheduled orders that are ready for preparation.

    Returns orders that should be prepared now.
    """
    from django.utils import timezone

    now = timezone.now()
    return Order.objects.filter(
        is_scheduled=True,
        status=Order.STATUS_PLACED,
        scheduled_for__lte=now
    )


def process_scheduled_orders():
    """
    Process all scheduled orders that are ready.

    This should be called by a periodic task (Celery, cron, etc.)
    """
    scheduled_orders = check_scheduled_orders()

    for order in scheduled_orders:
        try:
            # Auto-confirm scheduled orders
            order.status = Order.STATUS_CONFIRMED
            order.save(update_fields=["status"])

            OrderEvent.objects.create(
                order=order,
                action=Order.STATUS_CONFIRMED,
                note="Auto-confirmed scheduled order"
            )

            # Start preparation
            prepare_order(order)

        except Exception as e:
            # Log error but don't fail other orders
            print(f"Failed to process scheduled order {order.id}: {e}")
            continue
    snacks_payload = payload.get("snacks") or []
    customer_payload = payload.get("customer") or {}
    metadata = payload.get("metadata") or {}

    if not combos_payload and not snacks_payload:
        raise ValidationError("Order must contain at least one combo or snack")

    combo_map = {}

    for row in combos_payload:
        raw_id = row.get("id") or row.get("combo_id")
        qty = int(row.get("quantity", 1))

        if not raw_id:
            raise ValidationError("combo_id missing")

        try:
            combo_id = UUID(str(raw_id))
        except Exception:
            raise ValidationError("Invalid combo UUID")

        if qty < 1:
            raise ValidationError("Combo quantity must be ≥ 1")

        combo_map.setdefault(combo_id, 0)
        combo_map[combo_id] += qty

    combos = {
        c.id: c
        for c in Combo.objects.filter(id__in=combo_map.keys(), is_active=True)
    }

    if len(combos) != len(combo_map):
        raise ValidationError("Invalid or inactive combo detected")

    total_amount = ZERO
    prepared_item_totals = {}
    order_combos = []

    for combo_id, qty in combo_map.items():
        combo = combos[combo_id]
        total_amount += combo.selling_price * qty

        order_combos.append(OrderCombo(combo=combo, quantity=qty))

        for ci in combo.items.all():
            prepared_item_totals[ci.prepared_item_id] = (
                prepared_item_totals.get(ci.prepared_item_id, 0)
                + ci.quantity * qty
            )

    valid_items = set(
        PreparedItem.objects.filter(
            id__in=prepared_item_totals.keys()
        ).values_list("id", flat=True)
    )

    if set(prepared_item_totals) - valid_items:
        raise ValidationError("Invalid prepared_item detected")

    snack_totals = {}

    for row in snacks_payload:
        sid = row.get("snack_id") or row.get("id")
        qty = int(row.get("quantity", 1))

        if not sid or qty < 1:
            raise ValidationError("Invalid snack payload")

        snack_totals[int(sid)] = snack_totals.get(int(sid), 0) + qty

    snacks = {
        s.id: s
        for s in Snack.objects.filter(id__in=snack_totals, is_active=True)
    }

    if len(snacks) != len(snack_totals):
        raise ValidationError("Invalid or inactive snack detected")

    for sid, qty in snack_totals.items():
        total_amount += snacks[sid].selling_price * qty

    payment_method = (payload.get("payment_method") or "cod").lower()

    order = Order.objects.create(
        status=Order.STATUS_PLACED,  # Start as PLACED
        total_amount=total_amount,
        payment_method=payment_method,
        customer_name=customer_payload.get("name", ""),
        customer_phone=customer_payload.get("phone", ""),
        customer_email=customer_payload.get("email", ""),
        customer_address=customer_payload.get("address", ""),
        metadata=metadata,
    )

    phone = (customer_payload.get("phone") or "").strip()

    if phone:
        if not PHONE_RE.match(phone):
            raise ValidationError("Invalid phone format")

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={
                "name": customer_payload.get("name", ""),
                "email": customer_payload.get("email", ""),
            }
        )
        
        # Send OTP in background for new customers
        if created:
            from django.core.mail import send_mail
            from django.conf import settings
            import threading
            
            def send_welcome_otp():
                try:
                    # Generate and send OTP
                    from accounts.models import OTP
                    from accounts.sms import send_sms
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Invalidate any existing unused OTPs
                    OTP.objects.filter(phone=phone, is_used=False).update(is_used=True)
                    
                    # Generate new OTP
                    import random
                    code = f"{random.randint(100000, 999999)}"
                    
                    otp = OTP.objects.create(
                        phone=phone,
                        code=code,
                        expires_at=timezone.now() + timedelta(minutes=10),
                    )
                    
                    # Send SMS (non-blocking)
                    sms_sent = send_sms(phone, f"Welcome to Swad of Tamil! Your verification code is {otp.code}")
                    
                    # Log for debugging
                    print(f"Welcome OTP sent to {phone}: {code} (SMS: {sms_sent})")
                    
                except Exception as e:
                    print(f"Failed to send welcome OTP: {e}")
            
            # Send OTP in background thread
            thread = threading.Thread(target=send_welcome_otp, daemon=True)
            thread.start()
        
        order.customer = customer
        order.save(update_fields=["customer"])

    for oc in order_combos:
        oc.order = order
    OrderCombo.objects.bulk_create(order_combos)

    OrderItem.objects.bulk_create([
        OrderItem(order=order, prepared_item_id=pid, quantity=qty)
        for pid, qty in prepared_item_totals.items()
    ])

    OrderSnack.objects.bulk_create([
        OrderSnack(
            order=order,
            snack_id=s.id,
            snack_name=s.name,
            quantity=snack_totals[s.id],
            unit_price=s.selling_price,
        )
        for s in snacks.values()
    ])

    if payment_method == Order.PAYMENT_METHOD_COD:
        short = str(order.id)[:8]
        order.tracking_code = f"COD-{timezone.now().year}-{short}"
        order.save(update_fields=["tracking_code"])

        if phone:
            try:
                send_sms(
                    phone,
                    f"Order {order.order_number} placed. "
                    f"Tracking {order.tracking_code} – Swad of Tamil"
                )
            except Exception:
                pass

    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_PLACED,
        note="Order placed"
    )

    # Auto-confirm order immediately (simulate instant confirmation)
    order.status = Order.STATUS_CONFIRMED
    order.save(update_fields=["status"])
    
    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_CONFIRMED,
        note="Order auto-confirmed"
    )

    return order

@transaction.atomic
def confirm_order(order: Order):
    if order.status != Order.STATUS_PENDING:
        raise ValidationError("Only pending orders can be confirmed")

    ingredient_usage = {}

    items = (
        order.order_items
        .select_related("prepared_item")
        .prefetch_related("prepared_item__recipes__ingredient")
    )

    for item in items:
        for recipe in item.prepared_item.recipes.all():
            ingredient_usage[recipe.ingredient_id] = (
                ingredient_usage.get(recipe.ingredient_id, ZERO)
                + recipe.quantity * item.quantity
            )

    ingredients = {
        i.id: i
        for i in Ingredient.objects
        .select_for_update()
        .filter(id__in=ingredient_usage.keys())
    }

    for ing_id, required in ingredient_usage.items():
        ing = ingredients[ing_id]
        if ing.stock_qty < required:
            raise ValidationError(
                f"{ing.name} insufficient (need {required}, have {ing.stock_qty})"
            )

    for ing_id, required in ingredient_usage.items():
        ing = ingredients[ing_id]
        ing.stock_qty -= required
        ing.save(update_fields=["stock_qty"])

    order.status = Order.STATUS_CONFIRMED
    order.save(update_fields=["status"])

    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_CONFIRMED,
        note="Stock deducted"
    )

@transaction.atomic
def cancel_order(order: Order):
    if order.status == Order.STATUS_CANCELLED:
        return

    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=["status"])

    OrderEvent.objects.create(
        order=order,
        action=Order.STATUS_CANCELLED,
        note="Cancelled by admin"
    )
