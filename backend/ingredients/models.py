from decimal import Decimal, ROUND_HALF_UP
import logging
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
from django.conf import settings


QTY0 = Decimal("0.000")
MONEY0 = Decimal("0.00")
Q2 = Decimal("0.01")


class Ingredient(models.Model):
    """
    INGREDIENT = SINGLE SOURCE OF TRUTH (ERP)

    ✔ Stock exists ONLY here
    ✔ Cost exists ONLY here
    ✔ Stored ONLY in base units
    ✔ All recipes deduct from here
    """

    # -----------------------------
    # BASE UNITS
    # -----------------------------
    UNIT_KG = "kg"     # rice, dal, vegetables
    UNIT_LTR = "ltr"   # oil, water
    UNIT_PCS = "pcs"   # coconut, drumstick

    UNIT_CHOICES = [
        (UNIT_KG, "Kilogram"),
        (UNIT_LTR, "Litre"),
        (UNIT_PCS, "Pieces"),
    ]

    # -----------------------------
    # CORE FIELDS
    # -----------------------------
    name = models.CharField(
        max_length=100,
        unique=True
    )

    # Permanent auto-generated code (human-friendly)
    code = models.CharField(max_length=16, unique=True, db_index=True, editable=False, null=True, blank=True)

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES
    )

    # Additional metadata
    category = models.CharField(max_length=64, blank=True, help_text="Optional ingredient category")
    expiry_days = models.PositiveIntegerField(null=True, blank=True, help_text="Shelf life in days (optional)")
    preferred_vendor = models.CharField(max_length=120, blank=True, help_text="Preferred vendor name (optional)")

    # Stock stored ONLY in base unit
    stock_qty = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=QTY0,
        validators=[MinValueValidator(QTY0)]
    )

    # Cost per base unit (₹ / kg, ₹ / ltr, ₹ / pcs)
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=MONEY0,
        validators=[MinValueValidator(MONEY0)]
    )

    # Optional fallback unit cost to use when stock_qty == 0 (enterprise fallback)
    fallback_cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional: use this unit cost when stock is zero and fallback pricing is enabled.",
    )

    is_active = models.BooleanField(default=True)

    # -----------------------------
    # AUDIT
    # -----------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -----------------------------
    # DERIVED (READ-ONLY)
    # -----------------------------
    @property
    def total_value(self) -> Decimal:
        """
        Total inventory value = stock × cost
        """
        return (self.stock_qty * self.cost_per_unit).quantize(
            Q2, rounding=ROUND_HALF_UP
        )

    # -----------------------------
    # UNIT CONVERSION
    # -----------------------------
    def to_base_unit(self, qty: Decimal, unit: str) -> Decimal:
        """
        Convert given quantity into ingredient's base unit.
        Used ONLY during order confirmation.
        """
        qty = Decimal(qty)

        # normalize incoming unit strings
        u = (unit or "").strip().lower()

        # aliases
        aliases = {
            "g": "gm",
            "gram": "gm",
            "grams": "gm",
            "kg": "kg",
            "kilogram": "kg",
            "kilograms": "kg",
            "ml": "ml",
            "millilitre": "ml",
            "milliliter": "ml",
            "ltr": "ltr",
            "l": "ltr",
            "litre": "ltr",
            "liters": "ltr",
            "pcs": "pcs",
            "pc": "pcs",
            "piece": "pcs",
            "pieces": "pcs",
        }

        if u in aliases:
            u = aliases[u]

        # conversion factors to base unit
        # base unit is self.unit (kg, ltr, pcs)
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

        raise ValueError(
            f"Invalid unit conversion: {qty} {unit} → {self.unit}"
        )

    def cost_for_quantity(self, qty: Decimal, qty_unit: str) -> Decimal:
        """
        Convert qty (expressed in qty_unit) to the ingredient's base unit,
        then return the cost for that quantity using `cost_per_unit`.
        """
        qty = Decimal(qty)
        # Convert to base unit (kg / ltr / pcs)
        qty_base = self.to_base_unit(qty, qty_unit)
        # If stock_qty is zero, either raise or use fallback per project settings.
        from django.conf import settings

        if self.stock_qty == Decimal("0"):
            logger = logging.getLogger(__name__)
            # If strict integrity is enabled, raise to force admin to replenish stock.
            if getattr(settings, "SWAD_STRICT_COST_INTEGRITY", True):
                raise ValueError(
                    f"Ingredient '{self.name}' has zero stock_qty; cost computation is blocked by STRICT_COST_INTEGRITY."
                )

            # Otherwise, allow fallback when configured
            if getattr(settings, "SWAD_ALLOW_FALLBACK_PRICING", True) and self.fallback_cost_per_unit:
                logger.warning(
                    "Using fallback_cost_per_unit for ingredient %s because stock_qty=0",
                    self.name,
                )
                return (qty_base * self.fallback_cost_per_unit).quantize(Q2, rounding=ROUND_HALF_UP)

            # No fallback available — log and raise to avoid silent wrong pricing
            logger.warning(
                "No fallback_cost_per_unit for ingredient %s and stock_qty=0; raising error",
                self.name,
            )
            raise ValueError(
                f"Ingredient '{self.name}' has zero stock_qty and no fallback price configured."
            )

        cost = (qty_base * self.cost_per_unit).quantize(Q2, rounding=ROUND_HALF_UP)
        return cost

    # -----------------------------
    # META
    # -----------------------------
    class Meta:
        ordering = ["name"]
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def __str__(self):
        return f"{self.name} — {self.stock_qty} {self.unit}"

    def clean(self):
        """
        Centralize strict ERP validation at the model level.
        Enforce non-negative costs/stock and handle zero-stock policy based on settings.
        """
        # Non-negative checks
        if self.stock_qty < Decimal("0"):
            raise ValidationError({"stock_qty": "Stock quantity cannot be negative."})

        if self.cost_per_unit < Decimal("0"):
            raise ValidationError({"cost_per_unit": "Cost per unit cannot be negative."})

        # Zero-stock policy
        if self.stock_qty == Decimal("0"):
            strict = getattr(settings, "SWAD_STRICT_COST_INTEGRITY", True)
            allow_fallback = getattr(settings, "SWAD_ALLOW_FALLBACK_PRICING", True)

            if strict:
                raise ValidationError({
                    "stock_qty": (
                        "Stock quantity is ZERO. Replenish stock or set fallback_cost_per_unit before saving."
                    )
                })

            if not allow_fallback and not self.fallback_cost_per_unit:
                raise ValidationError({
                    "stock_qty": (
                        "Stock quantity is ZERO and fallback pricing is not allowed. Cannot save."
                    )
                })

    def save(self, *args, **kwargs):
        # Ensure model-level validation runs for all save paths
        from core.utils import generate_and_set_code

        # Generate code if missing (best-effort). We keep null=True here
        # so migrations/backfill can run without blocking.
        if not self.code:
            # Human-friendly codes: ING-0001
            for _ in range(3):
                try:
                    generate_and_set_code(self, "ING", "code", 4)
                    break
                except Exception:
                    continue

        self.full_clean()

        # Record stock movement when stock_qty changes.
        movement_reason = kwargs.pop('movement_reason', None)
        movement_note = kwargs.pop('movement_note', None)
        skip_movement = kwargs.pop('skip_movement', False)

        old_qty = None
        if self.pk and not skip_movement:
            try:
                old = Ingredient.objects.get(pk=self.pk)
                old_qty = Decimal(old.stock_qty)
            except Ingredient.DoesNotExist:
                old_qty = None

        result = super().save(*args, **kwargs)

        if old_qty is not None and old_qty != Decimal(self.stock_qty) and not skip_movement:
            delta = Decimal(self.stock_qty) - old_qty
            try:
                from .models_move import IngredientMovement
            except Exception:
                IngredientMovement = None

            if IngredientMovement:
                IngredientMovement.objects.create(
                    ingredient=self,
                    change_qty=delta,
                    reason=(movement_reason or IngredientMovement.REASON_ADJUSTMENT),
                    note=movement_note or "",
                    resulting_qty=Decimal(self.stock_qty),
                )

        return result

    @property
    def movements(self):
        return self.ingredientmovement_set.order_by("-timestamp")

    @property
    def total_added(self):
        return self.ingredientmovement_set.filter(change_qty__gt=0).aggregate(models.Sum('change_qty'))['change_qty__sum'] or Decimal('0')

    @property
    def total_used(self):
        s = self.ingredientmovement_set.filter(change_qty__lt=0).aggregate(models.Sum('change_qty'))['change_qty__sum']
        return (s or Decimal('0'))
