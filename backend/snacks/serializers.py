from rest_framework import serializers
from .models import Snack, SnackCombo, SnackComboItem


# ======================================================
# SNACK SERIALIZER — FRONTEND CONTRACT SAFE
# ======================================================
class SnackSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for packaged snacks.

    CONTRACT RULES:
    ✔ Numeric prices (no ₹, no strings)
    ✔ Absolute image URL or null
    ✔ Never throws frontend-breaking values
    ✔ Stable field names
    """

    # ---------- MEDIA ----------
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    animated_image = serializers.SerializerMethodField()

    # ---------- DERIVED ----------
    is_available = serializers.ReadOnlyField()
    availability_status = serializers.ReadOnlyField()

    profit = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    expiry_date = serializers.SerializerMethodField()

    class Meta:
        model = Snack
        fields = (
            "id",
            "uuid",

            # -----------------------------
            # Identity
            # -----------------------------
            "name",
            "description",
            "category",
            "region",

            # -----------------------------
            # Media
            # -----------------------------
            "image_url",
            "thumbnail_url",

            # -----------------------------
            # Packaging
            # -----------------------------
            "weight_label",
            "pack_size",
            "animated_image",

            # -----------------------------
            # Pricing & stock (NUMERIC)
            # -----------------------------
            "selling_price",
            "mrp",
            "stock_qty",
            "min_order_qty",

            # -----------------------------
            # Flags
            # -----------------------------
            "is_veg",
            "is_spicy",
            "is_featured",
            "is_active",
            "offers",
            "is_best_buy",
            "badge_text",
            "pairs_with",

            # -----------------------------
            # Derived
            # -----------------------------
            "is_available",
            "availability_status",
            "profit",
            "average_rating",
            "review_count",
            "expiry_date",
        )

        read_only_fields = fields

    # --------------------------------------------------
    # IMAGE (ABSOLUTE URL OR NULL)
    # --------------------------------------------------
    def get_image_url(self, obj):
        """
        Returns:
        - absolute image URL (string)
        - or None

        Never returns broken paths.
        """
        if not obj.image:
            return None

        request = self.context.get("request")
        url = obj.image.url

        return request.build_absolute_uri(url) if request else url

    def get_thumbnail_url(self, obj):
        """Return thumbnail URL (smaller version for lists/cards)"""
        full_url = self.get_image_url(obj)
        if full_url:
            # For now, return the same URL - can be enhanced with actual thumbnails later
            return full_url
        return None


    def get_animated_image(self, obj):
        """Return absolute animated image URL or None."""
        if not getattr(obj, "animated_image", None):
            return None
        request = self.context.get("request")
        url = obj.animated_image.url
        return request.build_absolute_uri(url) if request else url

    # --------------------------------------------------
    # PROFIT (FLOAT-SAFE FOR FRONTEND)
    # --------------------------------------------------
    def get_profit(self, obj):
        """
        Frontend-safe numeric profit.
        """
        try:
            return float(obj.profit)
        except Exception:
            return 0.0

    # --------------------------------------------------
    # REVIEWS (PLACEHOLDER — SAFE DEFAULTS)
    # --------------------------------------------------
    def get_average_rating(self, obj):
        # Review system not implemented yet
        return 0.0

    def get_review_count(self, obj):
        return 0

    # --------------------------------------------------
    # EXPIRY DATE (FROM NEXT CONSUMABLE BATCH)
    # --------------------------------------------------
    def get_expiry_date(self, obj):
        """
        Return expiry date from the next consumable batch (FIFO).
        Returns date string in YYYY-MM-DD format or None.
        """
        batch = obj.next_consumable_batch()
        if batch and batch.expiry_date:
            return batch.expiry_date.isoformat()
        return None


# ======================================================
# SNACK COMBO ITEM SERIALIZER
# ======================================================
class SnackComboItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual items within a combo.
    
    CONTRACT: Strict schema for frontend consumption.
    """

    name = serializers.CharField(source="snack.name", read_only=True)
    unit = serializers.SerializerMethodField()
    display_text = serializers.SerializerMethodField()

    class Meta:
        model = SnackComboItem
        fields = (
            "id",
            "name",
            "quantity",
            "unit",
            "display_text",
        )
        read_only_fields = fields

    def get_unit(self, obj):
        """Derive unit from snack pack_size or default to pcs."""
        pack_size = obj.snack.pack_size.lower() if obj.snack.pack_size else ""
        if "g" in pack_size or "kg" in pack_size:
            return "g"
        elif "ml" in pack_size or "l" in pack_size:
            return "ml"
        else:
            return "pcs"

    def get_display_text(self, obj):
        """Generate display text: quantity + name (+ pack_size if available)."""
        base_text = f"{obj.quantity} {obj.snack.name}"
        if obj.snack.pack_size:
            return f"{base_text} ({obj.snack.pack_size})"
        return base_text


# ======================================================
# SNACK COMBO SERIALIZER
# ======================================================
class SnackComboSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for snack combo bundles.

    CONTRACT RULES:
    ✔ Numeric prices (no ₹, no strings)
    ✔ Absolute image URL or null
    ✔ Never throws frontend-breaking values
    ✔ Stable field names
    """

    # ---------- MEDIA ----------
    image_url = serializers.SerializerMethodField()

    # ---------- DERIVED ----------
    is_available = serializers.ReadOnlyField()
    availability_status = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()

    # ---------- RELATIONS ----------
    items = SnackComboItemSerializer(many=True, read_only=True)

    class Meta:
        model = SnackCombo
        fields = (
            "id",
            "uuid",
            "code",

            # -----------------------------
            # Identity
            # -----------------------------
            "name",
            "description",

            # -----------------------------
            # Media
            # -----------------------------
            "image_url",

            # -----------------------------
            # Pricing
            # -----------------------------
            "selling_price",

            # -----------------------------
            # Flags
            # -----------------------------
            "is_featured",
            "is_active",

            # -----------------------------
            # Derived
            # -----------------------------
            "is_available",
            "availability_status",
            "total_items",

            # -----------------------------
            # Relations
            # -----------------------------
            "items",
        )

        read_only_fields = fields

    # --------------------------------------------------
    # IMAGE (ABSOLUTE URL OR NULL)
    # --------------------------------------------------
    def get_image_url(self, obj):
        """
        Returns:
        - absolute image URL (string)
        - or None

        Never returns broken paths.
        """
        if not obj.image:
            return None

        request = self.context.get("request")
        url = obj.image.url

        return request.build_absolute_uri(url) if request else url
