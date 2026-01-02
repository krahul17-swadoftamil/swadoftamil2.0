from decimal import Decimal
import re
from uuid import UUID

from django.db import transaction
from django.core.exceptions import ValidationError

from orders.models import Order, OrderCombo, OrderItem, OrderSnack
from accounts.sms import send_sms
from menu.models import Combo, PreparedItem
from ingredients.models import Ingredient
from snacks.models import Snack
from accounts.models import Customer

ZERO = Decimal("0.00")


# ======================================================
# CREATE ORDER (PENDING SNAPSHOT)
# ======================================================
@transaction.atomic
def create_order_from_payload(payload: dict) -> Order:
    """
    Creates a PENDING order snapshot.

    RULES:
    ✔ UUID-safe
    ✔ No stock deduction
    ✔ No ingredient deduction
    ✔ Atomic
    """

    combos_payload = payload.get("combos") or []
    snacks_payload = payload.get("snacks") or []
    customer_payload = payload.get("customer") or {}

    if not combos_payload and not snacks_payload:
        raise ValidationError("Order must contain at least one combo or snack")

    # --------------------------------------------------
    # NORMALIZE COMBOS (UUID ONLY)
    # --------------------------------------------------
    combo_map = {}

    for row in combos_payload:
        raw_id = row.get("id") or row.get("combo_id") or row.get("combo")
        quantity = int(row.get("quantity", 1))

        if not raw_id:
            raise ValidationError("combo_id missing")

        try:
            combo_id = UUID(str(raw_id))
        except Exception:
            raise ValidationError("Invalid combo UUID")

        if quantity < 1:
            raise ValidationError("Combo quantity must be ≥ 1")

        combo_map.setdefault(combo_id, {
            "quantity": 0,
            "addons": [],
        })

        combo_map[combo_id]["quantity"] += quantity
        combo_map[combo_id]["addons"].extend(row.get("addons", []))

    # --------------------------------------------------
    # FETCH COMBOS
    # --------------------------------------------------
    combos = {
        c.id: c
        for c in Combo.objects.filter(
            id__in=combo_map.keys(),
            is_active=True
        )
    }

    if len(combos) != len(combo_map):
        raise ValidationError("One or more combos are invalid or inactive")

    total_amount = ZERO
    prepared_item_totals = {}
    order_combos = []

    # --------------------------------------------------
    # BUILD COMBO SNAPSHOT
    # --------------------------------------------------
    for combo_id, data in combo_map.items():
        combo = combos[combo_id]
        combo_qty = data["quantity"]

        total_amount += combo.selling_price * combo_qty

        order_combos.append(
            OrderCombo(combo=combo, quantity=combo_qty)
        )

        # Base items
        for item in combo.items.all():
            prepared_item_totals[item.prepared_item_id] = (
                prepared_item_totals.get(item.prepared_item_id, 0)
                + item.quantity * combo_qty
            )

        # Addons
        for addon in data["addons"]:
            pid = addon.get("prepared_item_id") or addon.get("id")
            aqty = int(addon.get("quantity", 1))

            if not pid:
                raise ValidationError("prepared_item_id missing in addon")
            if aqty < 1:
                raise ValidationError("Addon quantity must be ≥ 1")

            prepared_item_totals[int(pid)] = (
                prepared_item_totals.get(int(pid), 0) + aqty
            )

    # --------------------------------------------------
    # VALIDATE PREPARED ITEMS
    # --------------------------------------------------
    valid_ids = set(
        PreparedItem.objects.filter(
            id__in=prepared_item_totals.keys()
        ).values_list("id", flat=True)
    )

    missing = set(prepared_item_totals.keys()) - valid_ids
    if missing:
        raise ValidationError(f"Invalid prepared_item_id(s): {missing}")

    # --------------------------------------------------
    # NORMALIZE SNACKS
    # --------------------------------------------------
    snack_totals = {}

    for row in snacks_payload:
        snack_id = row.get("snack_id") or row.get("id")
        quantity = int(row.get("quantity", 1))

        if not snack_id:
            raise ValidationError("snack_id missing")
        if quantity < 1:
            raise ValidationError("Snack quantity must be ≥ 1")

        snack_totals[int(snack_id)] = (
            snack_totals.get(int(snack_id), 0) + quantity
        )

    snacks = {}
    if snack_totals:
        snacks = {
            s.id: s
            for s in Snack.objects.filter(
                id__in=snack_totals.keys(),
                is_active=True
            )
        }

        if len(snacks) != len(snack_totals):
            raise ValidationError("One or more snacks are invalid or inactive")

        for sid, qty in snack_totals.items():
            total_amount += snacks[sid].selling_price * qty

    # --------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------
    payment_method = (payload.get("payment_method") or "online").lower()

    order = Order.objects.create(
        status=Order.STATUS_PENDING,
        total_amount=total_amount,
        payment_method=payment_method,
    )

    # --------------------------------------------------
    # CUSTOMER SNAPSHOT (OPTIONAL)
    # --------------------------------------------------
    phone = (customer_payload.get("phone") or "").strip()

    if phone:
        if not re.match(r"^\+?[0-9]{6,15}$", phone):
            raise ValidationError("Invalid phone format")

        customer, _ = Customer.objects.get_or_create(
            phone=phone,
            defaults={
                "name": customer_payload.get("name", "").strip(),
                "email": customer_payload.get("email", "").strip(),
            },
        )

        order.customer = customer
        order.save(update_fields=["customer"])

    # --------------------------------------------------
    # SAVE SNAPSHOTS
    # --------------------------------------------------
    for oc in order_combos:
        oc.order = order
    OrderCombo.objects.bulk_create(order_combos)

    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            prepared_item_id=pid,
            quantity=qty
        )
        for pid, qty in prepared_item_totals.items()
    ])

    if snack_totals:
        OrderSnack.objects.bulk_create([
            OrderSnack(
                order=order,
                snack_id=s.id,
                snack_name=s.name,
                quantity=qty,
                unit_price=s.selling_price,
            )
            for sid, qty in snack_totals.items()
            for s in [snacks[sid]]
        ])

    # --------------------------------------------------
    # Build a concise, human-readable `code` from order lines
    # Format: c-<combo>-<qty>-i-<item>-<qty>-s-<snack>-<qty>-<ORDERNUMBER>
    # Append `order_number` to guarantee uniqueness while keeping the
    # visible prefix compact and meaningful.
    def _slug(x: str) -> str:
        x = re.sub(r"[^a-zA-Z0-9]+", "-", (x or "").strip().lower())
        return x.strip("-")[:12]

    tokens = []

    for oc in order.order_combos.select_related("combo").all():
        label = getattr(oc.combo, "code", None) or getattr(oc.combo, "name", "combo")
        tokens.append(f"c-{_slug(label)}{oc.quantity}")

    for oi in order.order_items.select_related("prepared_item").all():
        label = getattr(oi.prepared_item, "name", "item")
        tokens.append(f"i-{_slug(label)}{oi.quantity}")

    for osn in order.order_snacks.all():
        tokens.append(f"s-{_slug(osn.snack_name)}{osn.quantity}")

    if tokens:
        prefix = "-".join(tokens)
        # keep the visible code reasonably short
        prefix = prefix[:60]
        order.code = f"{prefix}-{order.order_number}"
        order.save(update_fields=["code"])

    # --------------------------------------------------
    # Cash-on-delivery: generate simple tracking and notify customer
    # --------------------------------------------------
    if payment_method == Order.PAYMENT_METHOD_COD:
        # tracking code: COD-<year>-<shortorder>
        from django.utils import timezone
        short = str(order.order_number or order.id)[:8]
        tracking = f"COD-{timezone.now().year}-{short}"
        order.tracking_code = tracking
        order.save(update_fields=["tracking_code"]) 

        # send WhatsApp/SMS notification when possible
        cust_phone = None
        try:
            cust_phone = (customer_payload.get("phone") or "").strip()
        except Exception:
            cust_phone = None

        if cust_phone:
            msg = (
                f"Your order {order.code} is placed with Cash on Delivery. "
                f"Tracking: {order.tracking_code}. We will contact you before delivery. - Swad"
            )
            try:
                send_sms(cust_phone, msg)
            except Exception:
                # log inside send_sms; swallow here to avoid failing order creation
                pass

    return order


# ======================================================
# CONFIRM ORDER
# ======================================================
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
        ing.id: ing
        for ing in Ingredient.objects
        .select_for_update()
        .filter(id__in=ingredient_usage.keys())
    }

    for ing_id, required in ingredient_usage.items():
        ing = ingredients[ing_id]
        if ing.stock_qty < required:
            raise ValidationError(
                f"{ing.name} insufficient "
                f"(need {required}, have {ing.stock_qty})"
            )

    for ing_id, required in ingredient_usage.items():
        ing = ingredients[ing_id]
        ing.stock_qty -= required
        ing.save(update_fields=["stock_qty"])

    order.status = Order.STATUS_CONFIRMED
    order.save(update_fields=["status"])


# ======================================================
# CANCEL ORDER
# ======================================================
@transaction.atomic
def cancel_order(order: Order):
    if order.status == Order.STATUS_CANCELLED:
        return

    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=["status"])
