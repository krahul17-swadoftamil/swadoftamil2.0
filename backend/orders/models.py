from decimal import Decimal
import uuid

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from menu.models import Combo, PreparedItem

ZERO = Decimal("0.00")

class Order(models.Model):
    """
    Immutable business event.
    Created once, never edited.
    """

    # =============================
    # IDENTIFIER
    # =============================
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # =============================
    # STATUS
    # =============================
    STATUS_PLACED = "placed"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_PLACED, "Placed"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PLACED,
        db_index=True
    )

    # =============================
    # SCHEDULING (for orders placed when store closed)
    # =============================
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this order should be prepared/delivered if placed when store closed"
    )

    is_scheduled = models.BooleanField(
        default=False,
        help_text="Whether this order was scheduled for later due to store being closed"
    )

    # =============================
    # BILLING SNAPSHOT
    # =============================
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)]
    )

    payment_method = models.CharField(
        max_length=16,
        choices=(
            ("online", "Online"),
            ("cod", "Cash on Delivery"),
        ),
        default="online",
        db_index=True,
    )

    PAYMENT_METHOD_ONLINE = "online"
    PAYMENT_METHOD_COD = "cod"

    tracking_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True
    )

    # Estimated delivery time in minutes
    eta_minutes = models.PositiveIntegerField(
        default=37,  # 30-45 min average
        help_text="Estimated time to delivery in minutes"
    )

    # =============================
    # SCHEDULING (SCALABLE)
    # =============================
    is_scheduled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this order is scheduled for later preparation"
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the order should be prepared/delivered"
    )

    # =============================
    # CUSTOMER SNAPSHOT (OPTIONAL)
    # =============================
    customer_name = models.CharField(
        max_length=120,
        blank=True,
        default=""
    )

    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    customer_email = models.EmailField(
        blank=True,
        default=""
    )

    customer_address = models.TextField(
        blank=True,
        default=""
    )

    # Optional FK (never required)
    customer = models.ForeignKey(
        "accounts.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    # =============================
    # METADATA
    # =============================
    metadata = models.JSONField(
        default=dict,
        blank=True,
        null=False,
        help_text="Store idempotency key and other request metadata"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    order_number = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )

    code = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return self.order_number or str(self.id)[:8]

    # =============================
    # CODE GENERATION
    # =============================
    def save(self, *args, **kwargs):
        from django.utils import timezone
        from core.utils import generate_and_set_code

        year = timezone.now().year
        prefix = f"SOT-{year}"

        if not self.order_number:
            for _ in range(5):
                try:
                    generate_and_set_code(self, prefix, "order_number", 6)
                    break
                except Exception:
                    continue

        if not self.code and self.order_number:
            self.code = self.order_number

        super().save(*args, **kwargs)

    # =============================
    # ORDER CONFIRMATION & STOCK DEDUCTION
    # =============================
    def confirm_order(self):
        """
        Confirm the order and deduct ingredient stock.
        This creates ledger entries for all consumed ingredients.
        """
        from django.db import transaction
        from ingredients.models import IngredientStockLedger
        
        if self.status != self.STATUS_PLACED:
            raise ValidationError(f"Cannot confirm order with status: {self.status}")
        
        with transaction.atomic():
            # Deduct stock for combos
            for order_combo in self.order_combos.all():
                self._deduct_combo_stock(order_combo, IngredientStockLedger)
            
            # Deduct stock for standalone prepared items
            for order_item in self.order_items.all():
                self._deduct_prepared_item_stock(order_item, IngredientStockLedger)
            
            # Deduct stock for snacks (FIFO)
            for order_snack in self.order_snacks.all():
                self._deduct_snack_stock(order_snack)
            
            # Update order status
            self.status = self.STATUS_CONFIRMED
            self.save(update_fields=['status'])

    def _deduct_combo_stock(self, order_combo, LedgerModel):
        """Deduct stock for a combo in the order"""
        combo = order_combo.combo
        combo_quantity = order_combo.quantity
        
        for combo_item in combo.items.all():
            prepared_item = combo_item.prepared_item
            prepared_item_quantity = combo_item.quantity * combo_quantity
            
            self._deduct_prepared_item_stock_for_quantity(
                prepared_item, prepared_item_quantity, LedgerModel, combo
            )

    def _deduct_prepared_item_stock(self, order_item, LedgerModel):
        """Deduct stock for a standalone prepared item"""
        prepared_item = order_item.prepared_item
        quantity = order_item.quantity
        
        self._deduct_prepared_item_stock_for_quantity(
            prepared_item, quantity, LedgerModel, None
        )

    def _deduct_prepared_item_stock_for_quantity(self, prepared_item, quantity, LedgerModel, combo):
        """Deduct stock for a specific quantity of prepared item"""
        for recipe in prepared_item.recipe_items.all():
            # Calculate consumption based on production mode
            if prepared_item.production_mode == prepared_item.PER_SERVING:
                # Direct per-serving consumption
                consumption = recipe.quantity * quantity
            else:  # BATCH mode
                # Calculate how many batches needed for this quantity
                servings_per_batch = prepared_item.batch_output_quantity / prepared_item.serving_size
                batches_needed = quantity / servings_per_batch
                consumption = recipe.quantity * batches_needed
            
            # Convert to base unit
            consumption_base = recipe.ingredient.to_base_unit(consumption, recipe.quantity_unit)
            
            # Create ledger entry
            LedgerModel.objects.create(
                ingredient=recipe.ingredient,
                change_type=LedgerModel.CONSUMPTION,
                quantity_change=-consumption_base,  # Negative for consumption
                unit=recipe.ingredient.unit,  # Base unit
                related_order=self,
                related_prepared_item=prepared_item,
                related_combo=combo,
                note=f"Order {self.order_number}: {prepared_item.name} × {quantity}"
            )

    def _deduct_snack_stock(self, order_snack):
        """Deduct stock for snacks using FIFO (oldest batch first)"""
        from snacks.models import Snack
        
        try:
            snack = Snack.objects.get(id=order_snack.snack_id)
        except Snack.DoesNotExist:
            raise ValidationError(f"Snack {order_snack.snack_id} not found")
        
        quantity_needed = order_snack.quantity
        
        # Use FIFO: consume from oldest batches first
        while quantity_needed > 0:
            batch = snack.next_consumable_batch()
            if not batch:
                raise ValidationError(f"Insufficient stock for snack: {snack.name}")
            
            # Consume as much as possible from this batch
            consume_qty = min(quantity_needed, batch.units_remaining)
            batch.consume(consume_qty)
            quantity_needed -= consume_qty

    # =============================
    # FLAGS
    # =============================
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

class OrderAddon(models.Model):
    """
    Addons for order items (extra toppings, customizations, etc.)
    """
    order = models.ForeignKey(
        Order,
        related_name="order_addons",
        on_delete=models.CASCADE
    )

    # Reference to the item this addon belongs to
    order_item_type = models.CharField(
        max_length=16,
        choices=[
            ("global", "Global Order Addon"),
            ("combo", "Combo"),
            ("item", "Prepared Item"),
            ("snack", "Snack"),
        ]
    )

    # IDs for the parent item
    combo_id = models.UUIDField(null=True, blank=True)
    prepared_item_id = models.UUIDField(null=True, blank=True)
    snack_id = models.BigIntegerField(null=True, blank=True)

    # Addon details
    addon_name = models.CharField(max_length=120)
    addon_category = models.CharField(max_length=50, blank=True)  # e.g., "Toppings", "Spice Level"
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO
    )

    class Meta:
        indexes = [models.Index(fields=["order"])]

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.addon_name} × {self.quantity}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="order_items",
        on_delete=models.CASCADE
    )

    prepared_item = models.ForeignKey(
        PreparedItem,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [models.Index(fields=["order"])]

    def __str__(self):
        return f"{self.prepared_item.name} × {self.quantity}"

class OrderCombo(models.Model):
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
        indexes = [models.Index(fields=["order"])]

    def __str__(self):
        return f"{self.combo.name} × {self.quantity}"

class OrderSnack(models.Model):
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
        indexes = [models.Index(fields=["order"])]

    @property
    def total_price(self):
        return self.unit_price * self.quantity

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        "accounts.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="carts",
    )

    session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO
    )

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

class CartLine(models.Model):
    TYPE_COMBO = "combo"
    TYPE_ITEM = "item"
    TYPE_SNACK = "snack"

    cart = models.ForeignKey(
        Cart,
        related_name="lines",
        on_delete=models.CASCADE
    )

    type = models.CharField(
        max_length=16,
        choices=[
            (TYPE_COMBO, "Combo"),
            (TYPE_ITEM, "PreparedItem"),
            (TYPE_SNACK, "Snack"),
        ]
    )

    combo = models.ForeignKey(
        Combo,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    prepared_item = models.ForeignKey(
        PreparedItem,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    snack_id = models.BigIntegerField(null=True, blank=True)
    snack_name = models.CharField(max_length=120, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

class OrderEvent(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="events",
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=32)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

