from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum

from .models import Snack, SnackBatch
from django.urls import reverse
from django.utils import timezone


# ======================================================
# SNACK ADMIN — RETAIL CATALOG
# ======================================================
class SnackBatchInline(admin.TabularInline):
    model = SnackBatch
    extra = 0
    fields = ("batch_code", "supplier_name", "batch_cost", "packs_produced", "cost_per_pack", "units_remaining", "received", "received_date", "produced_at", "expiry_date")
    readonly_fields = ("cost_per_pack",)

@admin.register(Snack)
class SnackAdmin(admin.ModelAdmin):
    """
    Ready-to-sell retail snacks.
    - Not tied to ERP ingredients
    - Global catalog items
    - Stock-controlled
    """

    # ------------------------------
    # LIST VIEW
    # ------------------------------
    list_display = (
        "image_thumb",
        "code",
        "name",
        "category",
        "is_best_buy",
        "selling_price",
        "margin_display",
        "mrq_buying",
        "stock_qty",
        "stock_status",
        "is_featured",
        "is_active",
    )

    list_filter = (
        "category",
        "is_active",
        "is_featured",
        "is_veg",
        "is_spicy",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = ("-created_at",)
    list_per_page = 25
    show_full_result_count = False

    # ------------------------------
    # READONLY
    # ------------------------------
    readonly_fields = (
        "uuid",
        "code",
        "created_at",
        "updated_at",
        "image_preview",
        "profit_display",
        "cost_per_pack_display",
        "margin_display",
        "stock_qty",
    )

    inlines = (SnackBatchInline,)

    # ==================================================
    # DISPLAY HELPERS (available on SnackAdmin)
    # ==================================================

    @admin.display(description="Image")
    def image_thumb(self, obj):
        if not getattr(obj, 'image', None):
            return "—"
        return format_html(
            "<img src='{}' style='width:48px;height:48px;"
            "object-fit:cover;border-radius:6px;'/>",
            obj.image.url,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not getattr(obj, 'image', None):
            return "—"
        return format_html(
            "<img src='{}' style='width:140px;height:140px;"
            "object-fit:cover;border-radius:12px;"
            "box-shadow:0 6px 16px rgba(0,0,0,.35);'/>",
            obj.image.url,
        )

    @admin.display(description="Cost / pack")
    def cost_per_pack_display(self, obj):
        try:
            c = obj.cost_per_pack()
            return f"₹{c:.2f}"
        except Exception:
            return "—"

    @admin.display(description="Margin %")
    def margin_display(self, obj):
        try:
            m = obj.margin_percent
            return f"{m:.1f}%" if m is not None else "—"
        except Exception:
            return "—"

    @admin.display(description="Buying")
    def mrq_buying(self, obj):
        try:
            return "₹{:.2f}".format(obj.buying_price)
        except Exception:
            return "—"

    @admin.display(description="Stock")
    def stock_status(self, obj):
        if not obj.is_active:
            return format_html("<strong style='color:#9e9e9e'>{}</strong>", "Inactive")

        if obj.stock_qty <= 0:
            return format_html("<strong style='color:#e53935'>{}</strong>", "Sold Out")

        if obj.stock_qty <= 5:
            return format_html("<strong style='color:#fb8c00'>{}</strong>", "Low")

        return format_html("<strong style='color:#43a047'>{}</strong>", "Available")

    @admin.display(description="Profit")
    def profit_display(self, obj):
        try:
            profit = float(obj.profit)
            return format_html("<strong>₹{:.2f}</strong>", profit)
        except Exception:
            return "—"

    # ------------------------------
    # FORM LAYOUT
    # ------------------------------
    fieldsets = (
        (
            "Snack Details",
            {
                "fields": (
                    "name",
                    "code",
                    "description",
                    "category",
                    "badge_text",
                    "is_best_buy",
                    "offers",
                )
            },
        ),
        (
            "Image",
            {
                "fields": (
                    "image",
                    "animated_image",
                    "image_preview",
                )
            },
        ),
        (
            "Pricing & Stock",
            {
                "fields": (
                    "weight_label",
                    "pack_size",
                    "selling_price",
                    "buying_price",
                    "mrp",
                    "locked_cost_per_pack",
                    "cost_per_pack_display",
                    "margin_display",
                )
            },
        ),
        (
            "Food Attributes",
            {
                "fields": (
                    "is_veg",
                    "is_spicy",
                    "is_featured",
                )
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",),
            },
        ),
        (
            "System (Read-only)",
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )





@admin.register(SnackBatch)
class SnackBatchAdmin(admin.ModelAdmin):
    list_display = ("snack", "batch_code", "supplier_name", "received", "received_date", "produced_at", "packs_produced", "units_remaining", "cost_per_pack")
    list_filter = ("snack", "received")
    search_fields = ("batch_code", "snack__name", "supplier_name")
    readonly_fields = ("cost_per_pack",)

    actions = ("mark_as_received",)

    @admin.action(description="Mark selected batches as received and add units to stock")
    def mark_as_received(self, request, queryset):
        updated = 0
        for b in queryset:
            if not b.received:
                try:
                    b.received = True
                    b.received_date = b.received_date or timezone.now().date()
                    b.save(update_fields=['received', 'received_date'])
                    snack = b.snack
                    snack.stock_qty = (snack.stock_qty or 0) + int(b.units_remaining)
                    snack.save(update_fields=['stock_qty'])
                    updated += 1
                except Exception:
                    continue
        self.message_user(request, f"Marked {updated} batch(es) as received and updated stock.")

    # ==================================================
    # DISPLAY HELPERS
    # ==================================================

    @admin.display(description="Image")
    def image_thumb(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            "<img src='{}' style='width:48px;height:48px;"
            "object-fit:cover;border-radius:6px;'/>",
            obj.image.url,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            "<img src='{}' style='width:140px;height:140px;"
            "object-fit:cover;border-radius:12px;"
            "box-shadow:0 6px 16px rgba(0,0,0,.35);'/>",
            obj.image.url,
        )

    @admin.display(description="Cost / pack")
    def cost_per_pack_display(self, obj):
        try:
            c = obj.cost_per_pack()
            return f"₹{c:.2f}"
        except Exception:
            return "—"

    @admin.display(description="Margin %")
    def margin_display(self, obj):
        try:
            m = obj.margin_percent
            return f"{m:.1f}%" if m is not None else "—"
        except Exception:
            return "—"

    @admin.display(description="Stock")
    def stock_status(self, obj):
        if not obj.is_active:
            return format_html("<strong style='color:#9e9e9e'>{}</strong>", "Inactive")

        if obj.stock_qty <= 0:
            return format_html("<strong style='color:#e53935'>{}</strong>", "Sold Out")

        if obj.stock_qty <= 5:
            return format_html("<strong style='color:#fb8c00'>{}</strong>", "Low")

        return format_html("<strong style='color:#43a047'>{}</strong>", "Available")

    @admin.display(description="Buying")
    def mrq_buying(self, obj):
        try:
            return "₹{:.2f}".format(obj.buying_price)
        except Exception:
            return "—"

    @admin.display(description="Profit")
    def profit_display(self, obj):
        try:
            profit = float(obj.profit)
            return format_html("<strong>₹{:.2f}</strong>", profit)
        except Exception:
            return "—"

    # ==================================================
    # SAFETY (AUDIT PRESERVATION)
    # ==================================================
    def has_delete_permission(self, request, obj=None):
        """
        Snack records are audit-critical.
        Disable delete; use is_active instead.
        """
        # Allow deletes from admin (change back if audit preservation required)
        return True


@admin.action(description="Resync stock for selected snacks from batches")
def resync_stock(modeladmin, request, queryset):
    updated = 0
    for snack in queryset:
        try:
            total = snack.batches.filter(received=True).aggregate(Sum('units_remaining'))['units_remaining__sum'] or 0
            total = int(total)
            if snack.stock_qty != total:
                snack.stock_qty = total
                snack.save(update_fields=['stock_qty'])
                updated += 1
        except Exception:
            continue
    modeladmin.message_user(request, f"Resynced stock for {updated} snack(s).")


# Attach action to SnackAdmin
SnackAdmin.actions = getattr(SnackAdmin, 'actions', ()) + ('resync_stock',)
