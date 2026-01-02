import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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
# PREPARED ITEM (COMBO ITEM — NOT STANDALONE)
# ======================================================

class PreparedItem(models.Model):
    """
    ONE production unit.
    Sellable ONLY as part of a Combo.

    Examples:
    - 1 Idli
    - 50 ml Sambar
    - 30 ml Chutney
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Human-friendly generated code
    code = models.CharField(max_length=12, unique=True, db_index=True, editable=False, null=True, blank=True)

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    unit = models.CharField(
        max_length=8,
        choices=[
            ("pcs", "Pieces"),
            ("gm", "Gram"),
            ("ml", "Millilitre"),
        ],
    )

    serving_size = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        help_text="Customer-facing serving (e.g. 1 pc, 50 ml)",
    )

    # Recipe versioning
    recipe_version = models.PositiveIntegerField(default=1)

    # --------------------------------------------------
    # COMBO CONTEXT SELLING VALUE
    # --------------------------------------------------
    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        help_text="Unit value used ONLY inside a Combo (not sold standalone)",
    )

    sell_only_in_combo = models.BooleanField(
        default=True,
        editable=False,
        help_text="Prepared items cannot be ordered standalone",
    )

    protein_per_unit = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    # --------------------------------------------------
    # ERP COST (DERIVED)
    # --------------------------------------------------
    cost_price_cached = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=ZERO,
        editable=False,
    )

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

    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not getattr(self, 'code', None):
            for _ in range(3):
                try:
                    generate_and_set_code(self, "PI", "code", 4)
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)

    # --------------------------------------------------
    # VALIDATION (DISCIPLINE)
    # --------------------------------------------------
    def clean(self):
        if self.selling_price < self.cost_price_cached:
            raise ValidationError(
                _("Combo unit price cannot be lower than cost price.")
            )

    # --------------------------------------------------
    # ERP CORE
    # --------------------------------------------------
    def recompute_and_cache_cost(self):
        """
        Cost = sum of ingredient costs for ONE unit.
        """
        total = ZERO
        for r in self.recipe_items.all():
            total += r.ingredient_cost()

        self.cost_price_cached = total.quantize(Q2, ROUND_HALF_UP)
        super().save(update_fields=["cost_price_cached"])
        return self.cost_price_cached

    # --------------------------------------------------
    # COMBO HELPERS (READ-ONLY)
    # --------------------------------------------------
    @property
    def combo_unit_value(self):
        """
        Selling value of ONE unit inside a Combo.
        """
        return self.selling_price.quantize(Q2)

    def combo_extended_price(self, qty):
        """
        Value contribution inside a Combo.
        """
        return (self.combo_unit_value * qty).quantize(Q2)


# ======================================================
# PREPARED ITEM RECIPE (INGREDIENT TRUTH)
# ======================================================

class PreparedItemRecipe(models.Model):
    """
    Ingredient → PreparedItem mapping.
    Quantities are for ONE prepared item unit.
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
        validators=[MinValueValidator(ZERO)],
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
        default="gm",
    )

    class Meta:
        unique_together = ("prepared_item", "ingredient")

    def __str__(self):
        return f"{self.prepared_item} ← {self.ingredient}"

    def ingredient_cost(self):
        cost = self.ingredient.cost_for_quantity(
            self.quantity,
            self.quantity_unit,
        )
        return cost.quantize(Q2, ROUND_HALF_UP)


# ======================================================
# COMBO (ONLY CUSTOMER-SELLABLE PRODUCT)
# ======================================================
class Combo(models.Model):
    """
    Customer-facing product.

    RULES:
    ✔ Only Combo can be ordered
    ✔ Combos NEVER touch ingredients directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
    )

    serve_persons = models.PositiveSmallIntegerField(default=1)

    # Combo serving metadata
    serving_unit = models.CharField(
        max_length=8,
        choices=[
            ("pcs", "Pieces"),
            ("gm", "Gram"),
            ("ml", "Millilitre"),
        ],
        blank=True,
    )

    serving_size = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(ZERO)],
        help_text="Customer-facing serving size for the combo (optional)",
    )

    code = models.CharField(max_length=16, unique=True, db_index=True, editable=False, null=True, blank=True)

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

    # -------------------------------
    # COST & PROFIT (BACKEND ONLY)
    # -------------------------------
    @property
    def total_cost(self):
        return sum(
            (i.cost_cached for i in self.items.all()),
            ZERO,
        ).quantize(Q2)

    @property
    def profit(self):
        return (self.selling_price - self.total_cost).quantize(Q2)


# ======================================================
# COMBO ITEM (MULTIPLIER — NO PRICING POWER)
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

    quantity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
    )

    display_order = models.PositiveIntegerField(default=0)

    # ERP derived only
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
        """
        Cost = prepared_item cost × quantity.
        Selling logic NEVER happens here.
        """
        if self.prepared_item.cost_price_cached > ZERO:
            self.cost_cached = (
                self.prepared_item.cost_price_cached * self.quantity
            ).quantize(Q2, ROUND_HALF_UP)
        else:
            self.cost_cached = ZERO

        super().save(*args, **kwargs)
