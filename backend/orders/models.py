from decimal import Decimal
import uuid

from django.db import models
from django.core.validators import MinValueValidator

from menu.models import Combo, PreparedItem

ZERO = Decimal("0.00")


# ======================================================
# ORDER (IMMUTABLE BUSINESS EVENT)
# ======================================================
class Order(models.Model):
    """
    Order = single immutable business event.

    GOLDEN RULES:
    ❌ No ingredient deduction
    ❌ No cost calculation
    ❌ No combo expansion logic
    ✔ Snapshot + status only
    """

    # -----------------------------
    # STATUS
    # -----------------------------
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    # -----------------------------
    # BILLING SNAPSHOT
    # -----------------------------
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)]
    )

    # -----------------------------
    # CUSTOMER SNAPSHOT (IMPORTANT)
    # -----------------------------
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    customer_address = models.TextField()

    # Optional future linkage (never required for order creation)
    customer = models.ForeignKey(
        "accounts.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    # Human-friendly stable order code and order number.
    # `order_number` will be like SOT-2025-000123 and is the canonical human id.
    code = models.CharField(max_length=32, unique=True, db_index=True, editable=False, null=True, blank=True)
    order_number = models.CharField(max_length=32, unique=True, db_index=True, editable=False, null=True, blank=True)
    # Payment method and tracking (optional)
    PAYMENT_METHOD_ONLINE = "online"
    PAYMENT_METHOD_COD = "cod"

    PAYMENT_METHOD_CHOICES = (
        (PAYMENT_METHOD_ONLINE, "Online"),
        (PAYMENT_METHOD_COD, "Cash on Delivery"),
    )

    payment_method = models.CharField(
        max_length=16,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_ONLINE,
        db_index=True,
    )

    tracking_code = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Order {str(self.id)[:8]}"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        from core.utils import generate_and_set_code

        # Compose year-prefixed SOT code: SOT-<year>-<6-digit seq>
        year = timezone.now().year
        sot_prefix = f"SOT-{year}"

        # Generate canonical order_number if missing (immutable once set)
        if not getattr(self, 'order_number', None):
            for _ in range(6):
                try:
                    generate_and_set_code(self, sot_prefix, 'order_number', 6)
                    break
                except Exception:
                    continue

        # Backwards compatibility: if `code` is missing, keep it equal to order_number
        if not getattr(self, 'code', None) and getattr(self, 'order_number', None):
            self.code = self.order_number

        super().save(*args, **kwargs)

    # -----------------------------
    # STATUS FLAGS (READ-ONLY)
    # -----------------------------
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_confirmed(self):
        return self.status == self.STATUS_CONFIRMED

    @property
    def is_cancelled(self):
        return self.status == self.STATUS_CANCELLED


# ======================================================
# ORDER COMBO (LEVEL-1 SNAPSHOT)
# ======================================================
class OrderCombo(models.Model):
    """
    Snapshot of combos ordered.

    ✔ Invoice
    ✔ UI display
    ✔ Sales reporting

    ❌ NEVER used for stock or ingredient deduction
    """

    order = models.ForeignKey(
        Order,
        related_name="order_combos",
        on_delete=models.CASCADE
    )

    combo = models.ForeignKey(
        Combo,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ("order", "combo")
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.combo.name} × {self.quantity}"


# ======================================================
# ORDER ITEM (ERP AUTHORITY)
# ======================================================
class OrderItem(models.Model):
    """
    Flattened PreparedItem snapshot.

    THIS IS ERP GOLD:
    ✔ Used for ingredient deduction
    ✔ Immutable
    ✔ Audit-safe
    ✔ No combo logic inside
    """

    order = models.ForeignKey(
        Order,
        related_name="order_items",
        on_delete=models.CASCADE
    )

    prepared_item = models.ForeignKey(
        PreparedItem,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ("order", "prepared_item")
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.prepared_item.name} × {self.quantity}"


# ======================================================
# ORDER SNACK (PRICE-ONLY SNAPSHOT)
# ======================================================
class OrderSnack(models.Model):
    """
    Snapshot of snack items.

    ✔ Price-only
    ✔ No ingredients
    ✔ No stock logic
    ✔ Fully isolated from ERP logic
    """

    order = models.ForeignKey(
        Order,
        related_name="order_snacks",
        on_delete=models.CASCADE
    )

    snack_id = models.BigIntegerField()
    snack_name = models.CharField(max_length=120)

    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)]
    )

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.snack_name} × {self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity


# ======================================================
# CART & CART LINES (EPHEMERAL CUSTOMER CART)
# ======================================================
class Cart(models.Model):
    """
    Lightweight persisted cart. Stores a snapshot of items a customer
    or anonymous session intends to purchase. This is separate from
    immutable `Order` and can be modified freely.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to customer when available (optional)
    customer = models.ForeignKey(
        "accounts.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="carts",
    )

    # Optional session key for anonymous carts
    session_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    # Totals and metadata
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart {str(self.id)[:8]} ({self.customer or self.session_key or 'anon'})"


class CartLine(models.Model):
    """
    Single cart line. Mirrors order snapshot structure but remains editable.
    Fields accommodate combos, prepared items and snacks.
    """

    TYPE_COMBO = "combo"
    TYPE_ITEM = "item"
    TYPE_SNACK = "snack"

    TYPE_CHOICES = [
        (TYPE_COMBO, "Combo"),
        (TYPE_ITEM, "PreparedItem"),
        (TYPE_SNACK, "Snack"),
    ]

    cart = models.ForeignKey(Cart, related_name="lines", on_delete=models.CASCADE)

    type = models.CharField(max_length=16, choices=TYPE_CHOICES)

    # Optional foreign keys depending on type
    combo = models.ForeignKey(Combo, null=True, blank=True, on_delete=models.PROTECT)
    prepared_item = models.ForeignKey(PreparedItem, null=True, blank=True, on_delete=models.PROTECT)

    # Snack snapshot (price-only)
    snack_id = models.BigIntegerField(null=True, blank=True)
    snack_name = models.CharField(max_length=120, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["cart"])]

    def __str__(self):
        label = self.snack_name if self.type == self.TYPE_SNACK else (
            self.combo.name if self.combo else (self.prepared_item.name if self.prepared_item else "line")
        )
        return f"{label} × {self.quantity}"

class Address(models.Model):
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    line1 = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.line1} ({self.pincode})"