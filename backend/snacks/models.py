# ======================================================
# Imports & Constants
# ======================================================

import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

ZERO = Decimal("0.00")
Q2 = Decimal("0.01")


# ======================================================
# BASE MODEL (SHARED)
# ======================================================

class BaseModel(models.Model):
    """
    Minimal shared base model.
    """

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # Human-friendly generated code (per-entity)
    code = models.CharField(max_length=16, unique=True, db_index=True, editable=False, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active"])


# ======================================================
# SNACK (READY-TO-SELL PRODUCT)
# ======================================================

class Snack(BaseModel):
    """
    Ready-made packaged snack.

    RULES:
    ✔ No ingredients
    ✔ No recipes
    ✔ Stock comes ONLY from SnackBatch
    """

    CATEGORY_CHOICES = [
        ("mixture", "Mixture"),
        ("chips", "Chips"),
        ("sweet", "Sweet"),
        ("savory", "Savory"),
    ]

    REGION_CHOICES = [
        ("chettinad", "Chettinad"),
        ("andhra", "Andhra"),
        ("kerala", "Kerala"),
        ("karnataka", "Karnataka"),
        ("tamil_nadu", "Tamil Nadu"),
        ("other", "Other"),
    ]

    # ---------- CORE ----------
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    region = models.CharField(
        max_length=20,
        choices=REGION_CHOICES,
        default="other",
        help_text="Regional origin for branding and curation"
    )

    # ---------- MEDIA ----------
    image = models.ImageField(
        upload_to="snacks/",
        blank=True,
        null=True
    )

    # Optional animated image (gif/webp) for richer product cards
    animated_image = models.ImageField(
        upload_to="snacks/animated/",
        blank=True,
        null=True,
        help_text="Optional animated preview (gif/webp) used on product cards",
    )

    weight_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. 200g, 500g, 1kg"
    )

    # ---------- PACK ----------
    pack_size = models.CharField(
        max_length=32,
        help_text="Fixed pack size (e.g. 50g, 100g). Required."
    )

    locked_cost_per_pack = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional locked cost per pack."
    )

    # ---------- PRICING ----------
    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)]
    )

    buying_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        help_text="Fallback cost if no batch exists"
    )

    mrp = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)]
    )

    # ---------- ORDER RULES ----------
    min_order_qty = models.PositiveIntegerField(
        default=1,
        help_text="Minimum quantity required for delivery (trust & UX)"
    )

    # Marketing / UI fields (non-breaking defaults)
    offers = models.TextField(blank=True, default="", help_text="Promotional offer text shown on product card")
    is_best_buy = models.BooleanField(default=False, help_text="Flag to show a prominent badge on frontend")
    badge_text = models.CharField(max_length=32, blank=True, help_text="Optional custom badge text (e.g. Best Buy)")


    # ---------- STOCK (DERIVED) ----------
    stock_qty = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Derived from received SnackBatches"
    )

    # ---------- FLAGS ----------
    is_veg = models.BooleanField(default=True)
    is_spicy = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    source_name = models.CharField(
        max_length=120,
        blank=True,
        help_text="Wholesaler / Partner (internal)"
    )

    # ---------- PAIRING SUGGESTIONS ----------
    pairs_with = models.JSONField(
        default=list,
        help_text="e.g. ['Idli', 'Sambar'] - items this snack pairs well with"
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "weight_label")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not getattr(self, 'code', None):
            for _ in range(3):
                try:
                    generate_and_set_code(self, "SN", "code", 4)
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)

    # ---------- VALIDATION ----------
    def clean(self):
        if not self.pack_size:
            raise ValidationError({
                "pack_size": "pack_size is mandatory for all snacks."
            })

    # ---------- COST LOGIC ----------
    @property
    def latest_batch(self):
        return self.batches.filter(received=True).order_by("-produced_at").first()

    def next_consumable_batch(self):
        """
        FIFO: Consume oldest received batch first to minimize expiry risk.
        Returns the oldest batch with remaining units.
        """
        return self.batches.filter(
            received=True, units_remaining__gt=0
        ).order_by("produced_at").first()

    def cost_per_pack(self) -> Decimal:
        """
        Cost precedence:
        1) locked_cost_per_pack
        2) latest received batch cost
        3) buying_price
        """
        if self.locked_cost_per_pack is not None:
            return self.locked_cost_per_pack

        batch = self.latest_batch
        if batch and batch.cost_per_pack is not None:
            return batch.cost_per_pack

        return self.buying_price or ZERO

    # ---------- PROFIT & AVAILABILITY ----------
    @property
    def profit(self) -> Decimal:
        return (self.selling_price - self.cost_per_pack()).quantize(Q2)

    @property
    def margin_percent(self):
        cost = self.cost_per_pack()
        if cost == 0:
            return None
        return float(((self.selling_price - cost) / cost) * 100)

    @property
    def is_available(self):
        return self.is_active and self.stock_qty > 0

    @property
    def availability_status(self):
        if not self.is_active:
            return "Inactive"
        if self.stock_qty == 0:
            return "Sold Out"
        return "Available"

    @property
    def image_url(self):
        return self.image.url if self.image else None


# ======================================================
# SNACK BATCH (LOCKED COST + STOCK SOURCE)
# ======================================================

class SnackBatch(models.Model):
    """
    Production / purchase batch.

    ✔ cost_per_pack locked
    ✔ units_remaining authoritative
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    snack = models.ForeignKey(
        Snack,
        related_name="batches",
        on_delete=models.CASCADE
    )

    batch_code = models.CharField(max_length=32, blank=True)

    # ---------- FINANCIAL ----------
    batch_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)]
    )

    packs_produced = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    cost_per_pack = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    # ---------- INVENTORY ----------
    units_remaining = models.PositiveIntegerField()
    received = models.BooleanField(default=False)
    received_date = models.DateField(null=True, blank=True)

    supplier_name = models.CharField(max_length=120, blank=True)

    produced_at = models.DateTimeField(default=timezone.now, db_index=True)
    expiry_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-produced_at"]

    def __str__(self):
        return f"{self.snack.name} — {self.batch_code or str(self.id)[:8]}"

    # ---------- SAVE LOGIC ----------
    def save(self, *args, **kwargs):
        is_create = self._state.adding

        if is_create:
            self.cost_per_pack = (
                self.batch_cost / Decimal(self.packs_produced)
            ).quantize(Q2, rounding=ROUND_HALF_UP)

            if not self.units_remaining:
                self.units_remaining = self.packs_produced

        super().save(*args, **kwargs)

        if self.received and not self.received_date:
            self.received_date = timezone.now().date()
            super().save(update_fields=["received_date"])

    # ---------- CONSUME ----------
    def consume(self, qty: int):
        if qty <= 0:
            return
        if self.units_remaining < qty:
            raise ValidationError("Insufficient batch stock")
        self.units_remaining -= qty
        self.save(update_fields=["units_remaining"])


# ======================================================
# SIGNAL: RECOMPUTE SNACK STOCK
# ======================================================

@receiver(post_save, sender=SnackBatch)
@receiver(post_delete, sender=SnackBatch)
def recompute_snack_stock(sender, instance, **kwargs):
    snack = instance.snack
    total = (
        snack.batches
        .filter(received=True)
        .aggregate(models.Sum("units_remaining"))
        .get("units_remaining__sum")
        or 0
    )

    total = int(total)
    if snack.stock_qty != total:
        snack.stock_qty = total
        snack.save(update_fields=["stock_qty"])


# ======================================================
# SNACK COMBO (BUNDLE PRODUCT)
# ======================================================

class SnackCombo(BaseModel):
    """
    Bundled snack packages for revenue generation.

    Example: "Evening Tea Box" - 1 Murukku + 1 Mixture + 1 Sweet = ₹129
    """

    # ---------- CORE ----------
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    # ---------- MEDIA ----------
    image = models.ImageField(
        upload_to="combos/",
        blank=True,
        null=True
    )

    # ---------- PRICING ----------
    selling_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)]
    )

    # ---------- FLAGS ----------
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not getattr(self, 'code', None):
            for _ in range(3):
                try:
                    generate_and_set_code(self, "CB", "code", 4)
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)

    @property
    def is_available(self):
        """Combo is available if all constituent snacks are available and active."""
        return (
            self.is_active and
            all(item.snack.is_available for item in self.items.all())
        )

    @property
    def availability_status(self):
        if not self.is_active:
            return "Inactive"
        if not self.is_available:
            return "Out of Stock"
        return "Available"

    @property
    def total_items(self):
        """Total number of individual snack packs in this combo."""
        return sum(item.quantity for item in self.items.all())

    @property
    def image_url(self):
        return self.image.url if self.image else None


# ======================================================
# SNACK COMBO ITEM (LINK SNACKS TO COMBO)
# ======================================================

class SnackComboItem(models.Model):
    """
    Individual snack within a combo bundle.
    """

    id = models.BigAutoField(primary_key=True)

    combo = models.ForeignKey(
        SnackCombo,
        related_name="items",
        on_delete=models.CASCADE
    )

    snack = models.ForeignKey(
        Snack,
        related_name="combo_items",
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of packs of this snack in the combo"
    )

    class Meta:
        unique_together = ("combo", "snack")
        ordering = ["combo", "snack__name"]

    def __str__(self):
        return f"{self.combo.name} — {self.quantity}x {self.snack.name}"

    def clean(self):
        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")
