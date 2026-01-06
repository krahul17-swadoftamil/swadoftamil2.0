from decimal import Decimal, ROUND_HALF_UP
import logging

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone

# ======================================================
# CONSTANTS
# ======================================================

QTY0 = Decimal("0.000")
MONEY0 = Decimal("0.00")
Q2 = Decimal("0.01")

# Low stock thresholds (unit-specific)
LOW_STOCK_LIMITS = {
    "kg": Decimal("1.000"),
    "ltr": Decimal("1.000"),
    "pcs": Decimal("10.000"),
}

logger = logging.getLogger(__name__)


# ======================================================
# INGREDIENT (SINGLE SOURCE OF TRUTH)
# ======================================================

class Ingredient(models.Model):
    """
    INGREDIENT = SINGLE SOURCE OF TRUTH (ERP)

    ✔ Stock exists ONLY here
    ✔ Cost exists ONLY here
    ✔ Stored ONLY in base units
    ✔ All recipes deduct from here
    ✔ All movements are logged
    
    ⚠️  DEPRECATION: _stock_qty field is kept for migration safety but NO LONGER USED.
    ALL stock calculations use the stock_qty property (queries ledger directly).
    See DEPRECATION_GUIDE.md for removal timeline.
    """

    # --------------------------------------------------
    # BASE UNITS (STRICT)
    # --------------------------------------------------
    UNIT_KG = "kg"
    UNIT_LTR = "ltr"
    UNIT_PCS = "pcs"

    UNIT_CHOICES = [
        (UNIT_KG, "Kilogram"),
        (UNIT_LTR, "Litre"),
        (UNIT_PCS, "Pieces"),
    ]

    # --------------------------------------------------
    # CORE IDENTITY
    # --------------------------------------------------
    name = models.CharField(max_length=100, unique=True)

    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Auto-generated ERP code (ING-0001)"
    )

    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)

    category = models.CharField(max_length=64, blank=True)
    preferred_vendor = models.CharField(max_length=120, blank=True)
    expiry_days = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # --------------------------------------------------
    # STOCK & COST (DERIVED FROM LEDGER ONLY)
    # --------------------------------------------------
    # ⚠️  DEPRECATION WARNING: _stock_qty exists ONLY for migration safety.
    # ALL stock calculations must use the stock_qty property (ledger-based).
    # This field will be removed in a future version.
    _stock_qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=QTY0,
        validators=[MinValueValidator(QTY0)],
        db_column="stock_qty",  # Keep same column name for DB compatibility
        editable=False,  # Never edit directly
        help_text="⚠️  DEPRECATED: Kept for migration safety only. Use stock_qty property instead."
    )

    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=MONEY0,
        validators=[MinValueValidator(MONEY0)],
        help_text="₹ per base unit"
    )

    fallback_cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Used ONLY when stock is zero and fallback is enabled"
    )

    # --------------------------------------------------
    # AUDIT
    # --------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ==================================================
    # DERIVED
    # ==================================================
    @property
    def total_value(self) -> Decimal:
        """
        Inventory value = stock × unit cost
        """
        return (self.stock_qty * self.cost_per_unit).quantize(Q2, ROUND_HALF_UP)

    # ==================================================
    # UNIT CONVERSION (STRICT)
    # ==================================================
    def to_base_unit(self, qty: Decimal, unit: str) -> Decimal:
        """
        Convert qty → ingredient base unit.
        Allowed ONLY for recipe & deduction logic.
        """
        qty = Decimal(qty)
        u = (unit or "").strip().lower()

        aliases = {
            "g": "gm", "gram": "gm", "grams": "gm",
            "kg": "kg",
            "ml": "ml", "millilitre": "ml", "milliliter": "ml",
            "ltr": "ltr", "l": "ltr", "litre": "ltr",
            "pcs": "pcs", "pc": "pcs", "piece": "pcs", "pieces": "pcs",
        }

        u = aliases.get(u, u)

        if self.unit == self.UNIT_KG:
            if u == "gm":
                return qty / Decimal("1000")
            if u == "kg":
                return qty

        if self.unit == self.UNIT_LTR:
            if u == "ml":
                return qty / Decimal("1000")
            if u == "ltr":
                return qty

        if self.unit == self.UNIT_PCS:
            if u == "pcs":
                return qty

        raise ValidationError(
            f"Invalid unit conversion: {qty} {unit} → {self.unit}"
        )

    # ==================================================
    # COST COMPUTATION (SAFE)
    # ==================================================
    def cost_for_quantity(self, qty: Decimal, qty_unit: str) -> Decimal:
        """
        Cost for given qty (unit-aware).
        """
        qty_base = self.to_base_unit(qty, qty_unit)

        if self.stock_qty == QTY0:
            if getattr(settings, "SWAD_STRICT_COST_INTEGRITY", True):
                raise ValidationError(
                    f"Ingredient '{self.name}' has zero stock. Cost blocked."
                )

            if (
                getattr(settings, "SWAD_ALLOW_FALLBACK_PRICING", True)
                and self.fallback_cost_per_unit
            ):
                logger.warning(
                    "Fallback cost used for ingredient %s", self.name
                )
                return (qty_base * self.fallback_cost_per_unit).quantize(Q2)

            raise ValidationError(
                f"Ingredient '{self.name}' has zero stock and no fallback cost."
            )

        return (qty_base * self.cost_per_unit).quantize(Q2, ROUND_HALF_UP)

    # ==================================================
    # STOCK PROPERTY (LEDGER IS SINGLE SOURCE OF TRUTH)
    # ==================================================
    @property
    def stock_qty(self):
        """
        Current stock calculated from all ledger entries.
        
        ALWAYS uses ledger as single source of truth.
        For new items (no pk yet), returns 0.
        """
        if not self.pk:
            return QTY0
        return self.stock_ledger.aggregate(
            total=models.Sum('quantity_change')
        )['total'] or QTY0

    @stock_qty.setter
    def stock_qty(self, value):
        """
        DEPRECATED: Setting stock_qty directly is no longer supported.
        Create IngredientStockLedger entries instead.
        
        This setter will be removed in future versions.
        """
        import warnings
        warnings.warn(
            f"Setting {self.name}.stock_qty directly is deprecated. "
            "Create IngredientStockLedger entries via the ORM instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # For backward compatibility - creates adjustment entry
        current_stock = self.stock_qty
        difference = value - current_stock
        if difference != 0:
            IngredientStockLedger.objects.create(
                ingredient=self,
                change_type=IngredientStockLedger.ADJUSTMENT,
                quantity_change=difference,
                unit=self.unit,
                note=f"Manual adjustment from {current_stock} to {value}"
            )

    # ==================================================
    # STOCK ALERTS
    # ==================================================
    def get_low_stock_limit(self) -> Decimal:
        """Get the low stock threshold for this ingredient's unit"""
        return LOW_STOCK_LIMITS.get(self.unit, QTY0)
    
    def is_out_of_stock(self) -> bool:
        """Check if ingredient is out of stock"""
        return self.stock_qty <= QTY0
    
    def is_low_stock(self) -> bool:
        """Check if ingredient stock is below low stock threshold"""
        if self.is_out_of_stock():
            return True
        limit = self.get_low_stock_limit()
        return self.stock_qty <= limit
    
    def get_stock_status(self) -> tuple:
        """
        Get human-readable stock status and color.
        
        Returns:
            tuple: (status_text, color_code)
            
        Examples:
            ("Out of Stock", "#e53935")
            ("Low Stock", "#fb8c00")
            ("In Stock", "#43a047")
        """
        if self.is_out_of_stock():
            return "Out of Stock", "#e53935"
        if self.is_low_stock():
            return "Low Stock", "#fb8c00"
        return "In Stock", "#43a047"

    def update_stock_from_ledger(self):
        """
        DEPRECATED: This method is no longer needed.
        stock_qty property always queries ledger directly.
        
        This method will be removed in future versions.
        """
        import warnings
        warnings.warn(
            f"update_stock_from_ledger() is deprecated. "
            "stock_qty property always uses ledger as source of truth.",
            DeprecationWarning,
            stacklevel=2
        )

    # ==================================================
    # VALIDATION
    # ==================================================
    def clean(self):
        if self.stock_qty < QTY0:
            raise ValidationError({"stock_qty": "Stock cannot be negative."})

        if self.cost_per_unit < MONEY0:
            raise ValidationError({"cost_per_unit": "Cost cannot be negative."})

    # ==================================================
    # SAVE + MOVEMENT LOGGING
    # ==================================================
    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not self.code:
            generate_and_set_code(self, "ING", "code", 4)

        self.full_clean()

        # Note: Movement logging is now handled by signals on IngredientStockLedger.save()
        # This eliminates dependency on comparing old_qty snapshots
        with transaction.atomic():
            super().save(*args, **kwargs)

    # ==================================================
    # META
    # ==================================================
    class Meta:
        ordering = ["name"]
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def __str__(self):
        return f"{self.name} ({self.stock_qty} {self.unit})"


# ======================================================
# INGREDIENT STOCK LEDGER (AUDIT TRAIL)
# ======================================================

class IngredientStockLedger(models.Model):
    """
    COMPLETE AUDIT TRAIL FOR INGREDIENT STOCK CHANGES
    
    This is the single source of truth for all stock movements.
    Ingredient.stock_qty = SUM(quantity_change) from this ledger.
    """

    # Change Types
    OPENING = "opening"
    PURCHASE = "purchase"
    CONSUMPTION = "consumption"
    ADJUSTMENT = "adjustment"
    WASTAGE = "wastage"

    CHANGE_TYPE_CHOICES = [
        (OPENING, "Opening Stock"),
        (PURCHASE, "Purchase"),
        (CONSUMPTION, "Consumption"),
        (ADJUSTMENT, "Adjustment"),
        (WASTAGE, "Wastage"),
    ]

    # Core Fields
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="stock_ledger",
        on_delete=models.CASCADE,
    )

    change_type = models.CharField(
        max_length=12,
        choices=CHANGE_TYPE_CHOICES,
    )

    quantity_change = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Positive for additions, negative for reductions",
    )

    unit = models.CharField(
        max_length=10,
        choices=Ingredient.UNIT_CHOICES,
        help_text="Must match ingredient's base unit",
    )

    # Related Objects (for traceability)
    related_order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ingredient_consumptions",
    )

    related_prepared_item = models.ForeignKey(
        "menu.PreparedItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ingredient_consumptions",
    )

    related_combo = models.ForeignKey(
        "menu.Combo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ingredient_consumptions",
    )

    # Metadata
    note = models.TextField(
        blank=True,
        help_text="Reason for change, supplier details, etc.",
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Stock Ledger Entry"
        verbose_name_plural = "Stock Ledger Entries"

    def __str__(self):
        sign = "+" if self.quantity_change >= 0 else ""
        return f"{self.ingredient.name}: {sign}{self.quantity_change} {self.unit} ({self.get_change_type_display()})"

    def clean(self):
        # Unit must match ingredient's base unit
        if self.unit != self.ingredient.unit:
            raise ValidationError(
                f"Unit must match ingredient's base unit ({self.ingredient.unit})"
            )

        # Consumption entries must have related objects
        if self.change_type == self.CONSUMPTION:
            if not self.related_order:
                raise ValidationError("Consumption entries must be linked to an order")
            if not self.related_prepared_item:
                raise ValidationError("Consumption entries must be linked to a prepared item")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update ingredient stock after saving ledger entry
        self.ingredient.update_stock_from_ledger()
