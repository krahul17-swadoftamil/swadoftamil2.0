from rest_framework import serializers
from .models import Snack


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
    image = serializers.SerializerMethodField()
    animated_image = serializers.SerializerMethodField()

    # ---------- DERIVED ----------
    is_available = serializers.ReadOnlyField()
    availability_status = serializers.ReadOnlyField()

    profit = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

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

            # -----------------------------
            # Media
            # -----------------------------
            "image",

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
            "buying_price",
            "mrp",
            "stock_qty",

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

            # -----------------------------
            # Derived
            # -----------------------------
            "is_available",
            "availability_status",
            "profit",
            "average_rating",
            "review_count",
        )

        read_only_fields = fields

    # --------------------------------------------------
    # IMAGE (ABSOLUTE URL OR NULL)
    # --------------------------------------------------
    def get_image(self, obj):
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
