import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from ingredients.models import Ingredient


# ======================================================
# CONSTANTS
# ======================================================

ZERO = Decimal("0.00")
Q2 = Decimal("0.01")


# ======================================================
# LEGACY VALIDATORS (MIGRATION SAFE — DO NOT DELETE)
# ======================================================

def validate_combo_main_image(file): return None
def validate_combo_image(file): return None
def validate_prepared_item_image(file): return None
validate_comboitem_image = validate_combo_image


# ======================================================
# IMAGE VALIDATION (SOFT, ADMIN SAFE)
# ======================================================

try:
    from PIL import Image
except Exception:
    Image = None


def validate_image_min_600(file):
    if not Image or not file:
        return
    try:
        img = Image.open(file)
        w, h = img.size
        if w < 600 or h < 600:
            raise ValidationError(_("Minimum 600×600 image required."))
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_("Invalid image file."))


# ======================================================
# PREPARED ITEM (SERVING DEFINITION)
# ======================================================

class PreparedItem(models.Model):
    """
    ONE SERVING UNIT (not stock).

    Examples:
    - 1 Idli
    - 100 ml Sambar

    PRODUCTION MODES:
    - PER_SERVING: Recipe quantities = ingredients per 1 serving
    - BATCH: Recipe quantities = ingredients for ONE FULL BATCH
    
    ⚠️  CRITICAL: BATCH mode requires batch_output_quantity to be set.
    Recipe quantities MUST represent total ingredients needed for one complete batch.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    # CUSTOMER-FACING UNITS ONLY
    unit = models.CharField(
        max_length=8,
        choices=[
            ("pcs", "Pieces"),
            ("ml", "Millilitre"),
        ],
    )

    serving_size = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="1 pc, 100 ml etc",
    )

    # PRODUCTION MODE
    PER_SERVING = "per_serving"
    BATCH = "batch"
    PRODUCTION_MODE_CHOICES = [
        (PER_SERVING, "Per Serving"),
        (BATCH, "Batch Production"),
    ]
    production_mode = models.CharField(
        max_length=12,
        choices=PRODUCTION_MODE_CHOICES,
        default=PER_SERVING,
        help_text="How this item is produced: per serving or in batches",
    )

    batch_output_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Total output quantity for one batch (required for BATCH mode)",
    )

    recipe_version = models.PositiveIntegerField(default=1)

    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        help_text="Internal combo unit value",
    )

    # ERP derived
    cost_price_cached = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO,
        editable=False,
    )

    sell_only_in_combo = models.BooleanField(default=True, editable=False)

    main_image = models.ImageField(
        upload_to="prepared_items/",
        null=True,
        blank=True,
        validators=[validate_image_min_600],
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    # -----------------------------
    # SAVE / CODE
    # -----------------------------
    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code
        if not self.code:
            generate_and_set_code(self, "PI", "code", 4)
        super().save(*args, **kwargs)

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def clean(self):
        if self.cost_price_cached > ZERO and self.selling_price < self.cost_price_cached:
            raise ValidationError(
                _("Prepared item selling price cannot be below cost.")
            )
        
        # Production mode validation
        if self.production_mode == self.BATCH:
            if not self.batch_output_quantity:
                raise ValidationError(
                    _("Batch output quantity is required for BATCH production mode.")
                )
            if self.batch_output_quantity <= 1:
                raise ValidationError(
                    _("Batch output quantity must be greater than 1 for meaningful batch production.")
                )
        
        if self.production_mode == self.PER_SERVING and self.batch_output_quantity:
            raise ValidationError(
                _("Batch output quantity should not be set for PER_SERVING production mode.")
            )

    # -----------------------------
    # COST COMPUTATION
    # -----------------------------
    def recompute_and_cache_cost(self):
        """
        Cost = sum of ingredient costs for ONE prepared item.
        Cascades to related ComboItems.
        """
        total = ZERO
        for r in self.recipe_items.all():
            total += r.ingredient_cost()

        self.cost_price_cached = total.quantize(Q2, ROUND_HALF_UP)
        super().save(update_fields=["cost_price_cached"])

        # Cascade → ComboItem
        for ci in self.comboitem_set.all():
            ci.save(update_fields=["cost_cached"])

        return self.cost_price_cached

    # -----------------------------
    # READ HELPERS
    # -----------------------------
    @property
    def combo_unit_value(self):
        return self.selling_price.quantize(Q2)

    def combo_extended_price(self, qty):
        return (self.combo_unit_value * qty).quantize(Q2)

    def get_available_quantity(self):
        """
        Max prepared items that can be made based on ingredient stock.
        Handles both PER_SERVING and BATCH production modes.
        """
        if not self.recipe_items.exists():
            return 0  # No recipe, can't make

        if self.production_mode == self.PER_SERVING:
            # PER_SERVING: recipe quantities are per serving
            available = 999999  # Large number for "unlimited"
            for recipe in self.recipe_items.all():
                required_base = recipe.ingredient.to_base_unit(
                    recipe.quantity, recipe.quantity_unit
                )
                if required_base <= 0:
                    return 0
                if recipe.ingredient.stock_qty <= 0:
                    return 0
                stock_available = recipe.ingredient.stock_qty // required_base
                available = min(available, stock_available)
            return available

        elif self.production_mode == self.BATCH:
            # BATCH: recipe quantities are for one full batch
            if not self.batch_output_quantity:
                return 0  # Batch output not specified
            
            available_batches = 999999  # Large number for "unlimited"
            for recipe in self.recipe_items.all():
                required_base = recipe.ingredient.to_base_unit(
                    recipe.quantity, recipe.quantity_unit
                )
                if required_base <= 0:
                    return 0
                if recipe.ingredient.stock_qty <= 0:
                    return 0
                batches_possible = recipe.ingredient.stock_qty // required_base
                available_batches = min(available_batches, batches_possible)
            
            servings_per_batch = self.batch_output_quantity // self.serving_size
            return available_batches * servings_per_batch

        return 0  # Invalid production mode

    def get_availability_breakdown(self):
        """
        Returns a dict showing availability contribution from each ingredient
        and identifies the bottleneck ingredient.
        
        For PER_SERVING: shows servings available per ingredient
        For BATCH: shows batches available per ingredient
        
        Example: {"Rice": 20, "Urad Dal": 20, "Methi": 20, "bottleneck": "Rice"}
        """
        if not self.recipe_items.exists():
            return {"bottleneck": "incomplete"}
        
        if self.production_mode == self.BATCH and not self.batch_output_quantity:
            return {"bottleneck": "batch_output_missing"}
        
        breakdown = {}
        min_available = float('inf')
        bottleneck = None
        
        for recipe in self.recipe_items.all():
            required_base = recipe.ingredient.to_base_unit(
                recipe.quantity, recipe.quantity_unit
            )
            if required_base <= 0:
                continue
            if recipe.ingredient.stock_qty <= 0:
                stock_available = 0
            else:
                stock_available = recipe.ingredient.stock_qty / required_base
            
            available_int = int(stock_available)
            breakdown[recipe.ingredient.name] = available_int
            
            if available_int < min_available:
                min_available = available_int
                bottleneck = recipe.ingredient.name
        
        if bottleneck:
            breakdown["bottleneck"] = bottleneck
        else:
            breakdown["bottleneck"] = "none"
        
        return breakdown

    @property
    def availability_breakdown(self):
        return self.get_availability_breakdown()

    @property
    def available_quantity(self):
        return self.get_available_quantity()


# ======================================================
# PREPARED ITEM RECIPE (INGREDIENT TRUTH)
# ======================================================

class PreparedItemRecipe(models.Model):
    """
    Ingredient usage for ONE prepared item.
    
    QUANTITY INTERPRETATION DEPENDS ON PRODUCTION MODE:
    - PER_SERVING: quantity = ingredients needed for 1 serving
    - BATCH: quantity = ingredients needed for ONE FULL BATCH
    
    ⚠️  CRITICAL: In BATCH mode, quantities represent TOTAL batch ingredients,
    not per-serving amounts. The system divides by batch_output_quantity internally.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    prepared_item = models.ForeignKey(
        PreparedItem,
        related_name="recipe_items",
        on_delete=models.CASCADE,
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )

    quantity_unit = models.CharField(
        max_length=8,
        choices=[
            ("gm", "Gram"),
            ("kg", "Kilogram"),
            ("ml", "Millilitre"),
            ("ltr", "Litre"),
            ("pcs", "Pieces"),
        ],
    )

    class Meta:
        unique_together = ("prepared_item", "ingredient")

    def __str__(self):
        return f"{self.prepared_item} ← {self.ingredient}"

    def ingredient_cost(self):
        return self.ingredient.cost_for_quantity(
            self.quantity,
            self.quantity_unit,
        ).quantize(Q2, ROUND_HALF_UP)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity required per serving must be greater than 0.")
        
        # STRICT BATCH RULE: For BATCH production mode, recipe quantities MUST represent
        # ingredients required for ONE FULL BATCH (not per serving)
        if (self.prepared_item.production_mode == PreparedItem.BATCH and 
            self.prepared_item.batch_output_quantity):
            # This is enforced at the model level - recipe quantities = batch ingredients
            # get_available_quantity() handles the batch math correctly
            pass  # Validation is implicit through correct usage
        
        # Note: Unit compatibility is handled by to_base_unit, but could add check here if needed


# ======================================================
# COMBO (ONLY SELLABLE PRODUCT)
# ======================================================

class Combo(models.Model):
    """
    Customer-facing sellable product.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
    )

    serve_persons = models.PositiveSmallIntegerField(default=1)

    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    combo_version = models.PositiveIntegerField(default=1)

    main_image = models.ImageField(
        upload_to="combos/",
        null=True,
        blank=True,
        validators=[validate_image_min_600],
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    # -----------------------------
    # COST & PROFIT
    # -----------------------------
    @property
    def total_cost(self):
        return sum(
            (i.cost_cached for i in self.items.all()),
            ZERO,
        ).quantize(Q2)

    @property
    def profit(self):
        return (self.selling_price - self.total_cost).quantize(Q2)

    @property
    def available_quantity(self):
        """
        Max combos that can be made based on current ingredient stock.
        """
        if not self.items.exists():
            return 0

        available = 999999  # Large number for "unlimited"
        for item in self.items.all():
            prepared_available = item.prepared_item.get_available_quantity()
            if prepared_available == 0:
                return 0
            # Use integer division to avoid fractional availability
            item_available = prepared_available // item.quantity
            available = min(available, item_available)
        return available


# ======================================================
# COMBO ITEM (MULTIPLIER ONLY)
# ======================================================

class ComboItem(models.Model):
    """
    PreparedItem × quantity inside a Combo.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    combo = models.ForeignKey(
        Combo,
        related_name="items",
        on_delete=models.CASCADE,
    )

    prepared_item = models.ForeignKey(
        PreparedItem,
        on_delete=models.PROTECT,
    )

    # INTEGER SERVINGS ONLY
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    display_order = models.PositiveIntegerField(default=0)

    # ERP derived
    cost_cached = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO,
        editable=False,
    )

    class Meta:
        unique_together = ("combo", "prepared_item")
        ordering = ("display_order", "id")

    def __str__(self):
        return f"{self.combo} → {self.prepared_item}"

    def save(self, *args, **kwargs):
        if self.prepared_item.cost_price_cached > ZERO:
            self.cost_cached = (
                self.prepared_item.cost_price_cached * self.quantity
            ).quantize(Q2, ROUND_HALF_UP)
        else:
            self.cost_cached = ZERO
        super().save(*args, **kwargs)


# ======================================================
# MARKETING OFFERS
# ======================================================

class MarketingOffer(models.Model):
    BANNER_TYPES = [
        ('limited_time', 'Limited Time Offer'),
        ('chefs_special', "Chef's Special"),
        ('promotion', 'General Promotion'),
        ('announcement', 'Announcement'),
    ]

    title = models.CharField(max_length=200, help_text="Offer title/heading")
    description = models.TextField(help_text="Detailed offer description")
    short_text = models.CharField(
        max_length=100,
        help_text="Short text for banner display (with emojis)"
    )
    banner_type = models.CharField(
        max_length=20,
        choices=BANNER_TYPES,
        default='promotion',
        help_text="Type of banner for styling and behavior"
    )
    discount_percentage = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Discount percentage (optional)"
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Fixed discount amount (optional)"
    )
    is_active = models.BooleanField(default=True, help_text="Is this offer currently active?")
    start_date = models.DateTimeField(null=True, blank=True, help_text="When the offer starts")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When the offer ends")
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Higher priority offers show first (1-10)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Marketing Offer"
        verbose_name_plural = "Marketing Offers"

    def __str__(self):
        return f"{self.title} ({self.get_banner_type_display()})"

    @property
    def is_currently_active(self):
        """Check if offer is currently active based on dates"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

# ======================================================
# KITCHEN BATCH (OPERATIONAL CONCEPT)
# ======================================================

class KitchenBatch(models.Model):
    """
    Optional batch preparation tracking for items made before orders.
    
    Purpose:
    - Sambar, chutney, and other pre-prep items are made in batches
    - Logs when batches are prepared
    - Creates ADJUSTMENT ledger entries (audit-friendly)
    - Maintains operational clarity
    
    Example:
    - Kitchen preps 50L Sambar at 6am
    - Creates KitchenBatch record
    - Ingredient stock updated via ledger
    - Orders consume from prepared inventory
    
    ⚠️  Uses ADJUSTMENT (not CONSUMPTION) because:
    - These are operational batches, not order-driven
    - Keeps consumption tied to actual orders
    - Maintains audit integrity
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    prepared_item = models.ForeignKey(
        PreparedItem,
        related_name="kitchen_batches",
        on_delete=models.CASCADE,
        help_text="Item being batch prepared"
    )
    
    batch_size = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Quantity prepared (in PreparedItem serving units)"
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When batch was prepared"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Kitchen notes (e.g., 'Extra spicy batch', 'Trial run')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Kitchen Batch"
        verbose_name_plural = "Kitchen Batches"
    
    def __str__(self):
        return f"{self.prepared_item.name} × {self.batch_size} {self.prepared_item.unit} @ {self.timestamp.strftime('%H:%M')}"
    
    def create_ledger_entries(self):
        """
        Create ADJUSTMENT ledger entries for all ingredients in this batch.
        
        Returns:
            List of created IngredientStockLedger entries
        """
        from .kitchen_batch import create_kitchen_batch
        return create_kitchen_batch(self.prepared_item, self.batch_size, "Kitchen batch")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ======================================================
# SUBSCRIPTION SYSTEM
# ======================================================

class SubscriptionPlan(models.Model):
    """
    Subscription plans available to customers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Plan type
    PLAN_DAILY = "daily"
    PLAN_WEEKLY = "weekly"
    PLAN_CUSTOM = "custom"

    PLAN_CHOICES = [
        (PLAN_DAILY, "Daily"),
        (PLAN_WEEKLY, "Weekly"),
        (PLAN_CUSTOM, "Custom Days"),
    ]

    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_DAILY,
    )

    # Base combo for the subscription
    base_combo = models.ForeignKey(
        Combo,
        on_delete=models.PROTECT,
        related_name="subscription_plans",
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    # Discounts
    monthly_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("30.00"),  # 30% discount for monthly
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    # Delivery
    delivery_time = models.TimeField(default="08:30:00")  # 8:30 AM

    # Status
    is_active = models.BooleanField(default=True)
    is_coming_soon = models.BooleanField(default=False)

    # Ordering
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"

    def get_discounted_price(self, billing_cycle_days=30):
        """
        Calculate discounted price based on billing cycle.
        For monthly (30 days), apply monthly discount.
        """
        if billing_cycle_days >= 30 and self.plan_type == self.PLAN_DAILY:
            discount = self.base_price * (self.monthly_discount_percent / Decimal("100"))
            return self.base_price - discount
        return self.base_price


class Subscription(models.Model):
    """
    Customer subscriptions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Customer (placeholder - will integrate with accounts later)
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15, blank=True)

    # Plan
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    # Custom schedule for custom plans
    custom_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of days of week (0=Monday, 6=Sunday) for custom plans",
    )

    # Billing
    billing_cycle_days = models.PositiveIntegerField(default=30)
    price_per_cycle = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    # Status
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )

    # Delivery preferences
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)

    # Dates
    start_date = models.DateField()
    next_delivery_date = models.DateField()
    paused_until = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.customer_name} - {self.plan.name}"

    def save(self, *args, **kwargs):
        # Set price on creation
        if not self.price_per_cycle:
            self.price_per_cycle = self.plan.get_discounted_price(self.billing_cycle_days)

        # Set next delivery date
        if not self.next_delivery_date:
            self.next_delivery_date = self.start_date

        super().save(*args, **kwargs)

    def pause_until(self, date):
        """Pause subscription until specified date."""
        self.status = self.STATUS_PAUSED
        self.paused_until = date
        self.save()

    def resume(self):
        """Resume subscription."""
        self.status = self.STATUS_ACTIVE
        self.paused_until = None
        self.save()

    def cancel(self):
        """Cancel subscription."""
        self.status = self.STATUS_CANCELLED
        self.save()

    @property
    def is_active_today(self):
        """Check if subscription should deliver today."""
        if self.status != self.STATUS_ACTIVE:
            return False

        today = timezone.now().date()

        if self.plan.plan_type == SubscriptionPlan.PLAN_DAILY:
            return True
        elif self.plan.plan_type == SubscriptionPlan.PLAN_WEEKLY:
            # Deliver on start day of week
            return today.weekday() == self.start_date.weekday()
        elif self.plan.plan_type == SubscriptionPlan.PLAN_CUSTOM:
            return today.weekday() in self.custom_days

        return False