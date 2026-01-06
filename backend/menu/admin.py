from decimal import Decimal

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    PreparedItem,
    PreparedItemRecipe,
    Combo,
    ComboItem,
    MarketingOffer,
    KitchenBatch,
)

ZERO = Decimal("0.00")


# ======================================================
# COMMON HELPERS
# ======================================================

def rupees(value):
    try:
        return f"₹{Decimal(value):.2f}" if value is not None else "—"
    except Exception:
        return "—"


def image_tag(url, size=60, radius=10, shadow=False):
    if not url:
        return "—"

    shadow_css = "box-shadow:0 6px 16px rgba(0,0,0,.35);" if shadow else ""

    return format_html(
        "<img src='{}' style='width:{}px;height:{}px;"
        "object-fit:cover;border-radius:{}px;{}'/>",
        url,
        size,
        size,
        radius,
        shadow_css,
    )


# ======================================================
# PREPARED ITEM → INGREDIENT INLINE
# ======================================================

class PreparedItemRecipeInline(admin.TabularInline):
    """
    Ingredient truth for ONE PreparedItem unit.
    Ingredient stock is deducted elsewhere (service).
    """
    model = PreparedItemRecipe
    extra = 1
    min_num = 1
    validate_min = True

    autocomplete_fields = ("ingredient",)
    fields = ("ingredient", "quantity", "quantity_unit")


# ======================================================
# PREPARED ITEM ADMIN
# ======================================================

@admin.register(PreparedItem)
class PreparedItemAdmin(admin.ModelAdmin):
    """
    PreparedItem:
    - NOT sellable standalone
    - Cost derived from ingredients
    - Used only inside Combos
    """

    list_display = (
        "image_thumb",
        "code",
        "name",
        "recipe_status_view",
        "production_mode",
        "unit",
        "serving_size",
        "selling_price",
        "cost_price_cached",
        "available_quantity_view",
        "margin_view",
        "is_active",
    )

    list_filter = ("is_active", "unit")
    search_fields = ("name", "code")
    ordering = ("name",)

    readonly_fields = (
        "code",
        "cost_price_cached",
        "available_quantity_view",
        "margin_view",
        "image_preview",
    )

    inlines = (PreparedItemRecipeInline,)

    fieldsets = (
        (
            "Prepared Item",
            {
                "fields": (
                    "name",
                    "code",
                    "description",
                    "production_mode",
                    "batch_output_quantity",
                    "unit",
                    "serving_size",
                    "selling_price",
                    "main_image",
                    "image_preview",
                    "is_active",
                )
            },
        ),
        (
            "ERP (Read Only)",
            {
                "fields": (
                    "cost_price_cached",
                    "margin_view",
                )
            },
        ),
    )

    # ---------------- DISPLAY ----------------

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=44,
            radius=8,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=180,
            radius=16,
            shadow=True,
        )

    @admin.display(description="Recipe")
    def recipe_status_view(self, obj):
        if obj.recipe_items.exists():
            return format_html("<strong style='color:green'>✅ Complete</strong>")
        else:
            return format_html("<strong style='color:red'>⚠ Incomplete</strong>")

    @admin.display(description="Available Qty")
    def available_quantity_view(self, obj):
        if not obj.recipe_items.exists():
            return format_html("<strong style='color:red'>⚠ Incomplete</strong>")

        qty = obj.available_quantity
        mode = "servings" if obj.production_mode == obj.PER_SERVING else "servings (batch)"

        color = "red" if qty == 0 else "orange" if qty < 10 else "green"

        return format_html(
            "<strong style='color:{}'>{} {}</strong>",
            color,
            qty,
            mode,
        )

    @admin.display(description="Margin")
    def margin_view(self, obj):
        if obj.cost_price_cached <= ZERO:
            return "—"

        margin = obj.selling_price - obj.cost_price_cached
        color = "green" if margin >= ZERO else "red"

        return format_html(
            "<strong style='color:{}'>{}</strong>",
            color,
            rupees(margin),
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        obj.recompute_and_cache_cost()
        self.message_user(
            request,
            "Cost recalculated based on ingredient recipe.",
            level=messages.INFO,
        )

    def get_inline_instances(self, request, obj=None):
        if obj and obj.production_mode == PreparedItem.BATCH:
            if not obj.batch_output_quantity:
                self.message_user(
                    request,
                    "Batch output quantity must be set before adding recipe items.",
                    level=messages.ERROR,
                )
                return []
        return super().get_inline_instances(request, obj)


# ======================================================
# COMBO → PREPARED ITEM INLINE
# ======================================================

class ComboItemInline(admin.TabularInline):
    """
    Combo composition:
    PreparedItem × quantity
    """
    model = ComboItem
    extra = 1
    min_num = 1
    validate_min = True

    autocomplete_fields = ("prepared_item",)
    ordering = ("display_order",)

    fields = (
        "prepared_item",
        "display_order",
        "quantity",
        "cost_cached",
        "preview",
    )

    readonly_fields = ("cost_cached", "preview")

    @admin.display(description="Item")
    def preview(self, obj):
        pi = obj.prepared_item
        if pi and pi.main_image:
            return image_tag(
                pi.main_image.url,
                size=48,
                radius=8,
            )
        return "—"


# ======================================================
# COMBO ADMIN
# ======================================================

@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    """
    Combo:
    - ONLY sellable product
    - Cost derived from PreparedItems
    - Ingredient logic never runs here
    """

    list_display = (
        "image_thumb",
        "name",
        "code",
        "serve_persons",
        "selling_price",
        "total_cost_view",
        "profit_view",
        "available_quantity_view",
        "is_active",
        "is_featured",
    )

    list_filter = ("is_active", "is_featured")
    search_fields = ("name", "code")
    ordering = ("name",)

    readonly_fields = (
        "code",
        "combo_version",
        "image_preview",
        "total_cost_view",
        "profit_view",
        "available_quantity_view",
    )

    inlines = (ComboItemInline,)

    fieldsets = (
        (
            "Combo",
            {
                "fields": (
                    "name",
                    "description",
                    "serve_persons",
                    "combo_version",
                    "code",
                    "main_image",
                    "image_preview",
                    "is_active",
                    "is_featured",
                )
            },
        ),
        (
            "Pricing (Derived)",
            {
                "fields": (
                    "selling_price",
                    "total_cost_view",
                    "profit_view",
                )
            },
        ),
    )

    # ---------------- DISPLAY ----------------

    @admin.display(description="Image")
    def image_thumb(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=44,
            radius=8,
        )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return image_tag(
            obj.main_image.url if obj.main_image else None,
            size=180,
            radius=16,
            shadow=True,
        )

    @admin.display(description="Total Cost")
    def total_cost_view(self, obj):
        return rupees(obj.total_cost)

    @admin.display(description="Profit")
    def profit_view(self, obj):
        profit = obj.profit
        color = "green" if profit >= ZERO else "red"

        return format_html(
            "<strong style='color:{}'>{}</strong>",
            color,
            rupees(profit),
        )

    @admin.display(description="Available Qty")
    def available_quantity_view(self, obj):
        qty = obj.available_quantity
        if qty == 0:
            color = "red"
        elif qty < 10:
            color = "orange"
        else:
            color = "green"
        return format_html(
            "<strong style='color:{}'>{}</strong>",
            color,
            qty,
        )


# ======================================================
# MARKETING OFFER ADMIN
# ======================================================

@admin.register(MarketingOffer)
class MarketingOfferAdmin(admin.ModelAdmin):
    """
    MarketingOffer:
    - Manage promotional offers
    - Control active status and dates
    - Set priority for display order
    """

    list_display = (
        "title",
        "short_text",
        "discount_percentage",
        "discount_amount",
        "is_active",
        "toggle_active_button",
        "is_currently_active",
        "priority",
        "start_date",
        "end_date",
    )

    list_filter = ("is_active", "priority", "start_date", "end_date")
    search_fields = ("title", "description", "short_text")
    ordering = ("-priority", "-created_at")

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "description", "short_text"),
        }),
        ("Discount Details", {
            "fields": ("discount_percentage", "discount_amount"),
            "description": "Choose either percentage or fixed amount discount",
        }),
        ("Scheduling", {
            "fields": ("is_active", "start_date", "end_date", "priority"),
            "description": "Control when and how prominently this offer appears",
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Currently Active", boolean=True)
    def is_currently_active(self, obj):
        return obj.is_currently_active

    @admin.display(description="Toggle", ordering="is_active")
    def toggle_active_button(self, obj):
        url = reverse("admin:marketingoffer_toggle_active", args=[obj.pk])
        if obj.is_active:
            return format_html(
                '<a href="{}" '
                'style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;display:inline-block;">'
                'TURN OFF</a>',
                url
            )
        else:
            return format_html(
                '<a href="{}" '
                'style="background:#28a745;color:white;padding:3px 8px;border-radius:3px;text-decoration:none;font-size:11px;display:inline-block;">'
                'TURN ON</a>',
                url
            )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/toggle/',
                self.admin_site.admin_view(self.toggle_active_view),
                name='marketingoffer_toggle_active',
            ),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request, pk):
        """Toggle the active status of a marketing offer"""
        try:
            offer = self.get_queryset(request).get(pk=pk)
            offer.is_active = not offer.is_active
            offer.save()
            
            status_text = "activated" if offer.is_active else "deactivated"
            self.message_user(
                request,
                f"Offer '{offer.title}' has been {status_text}.",
                messages.SUCCESS if offer.is_active else messages.WARNING,
            )
        except MarketingOffer.DoesNotExist:
            self.message_user(request, "Offer not found.", messages.ERROR)
        
        return redirect('admin:menu_marketingoffer_changelist')

    # ---------------- ACTIONS ----------------

    actions = ["activate_offers", "deactivate_offers"]

    @admin.action(description="Activate selected offers")
    def activate_offers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully activated {updated} offer(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Deactivate selected offers")
    def deactivate_offers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully deactivated {updated} offer(s).",
            messages.WARNING,
        )


# ======================================================
# KITCHEN BATCH ADMIN
# ======================================================

@admin.register(KitchenBatch)
class KitchenBatchAdmin(admin.ModelAdmin):
    """
    Log batch preparations for items made before orders.
    
    Sambar, chutney, and other pre-prep items are made in batches.
    This tracks when batches are prepared and auto-creates ledger entries.
    """
    
    list_display = (
        "timestamp_display",
        "prepared_item",
        "batch_size_display",
        "notes_short",
        "ledger_created",
    )
    
    list_filter = ("prepared_item", "timestamp")
    search_fields = ("prepared_item__name", "notes")
    ordering = ["-timestamp"]
    
    readonly_fields = ("created_at", "ledger_status")
    
    fieldsets = (
        ("Batch Details", {
            "fields": ("prepared_item", "batch_size", "timestamp", "notes"),
        }),
        ("Status", {
            "fields": ("ledger_status", "created_at"),
        }),
    )
    
    @admin.display(description="When", ordering="timestamp")
    def timestamp_display(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M")
    
    @admin.display(description="Size")
    def batch_size_display(self, obj):
        return f"{obj.batch_size} {obj.prepared_item.unit}"
    
    @admin.display(description="Notes")
    def notes_short(self, obj):
        if obj.notes:
            return obj.notes[:40] + "..." if len(obj.notes) > 40 else obj.notes
        return "—"
    
    @admin.display(description="Ledger Entries Created")
    def ledger_created(self, obj):
        from ingredients.models import IngredientStockLedger
        count = IngredientStockLedger.objects.filter(
            related_prepared_item=obj.prepared_item,
            change_type=IngredientStockLedger.ADJUSTMENT,
            note__contains="Kitchen batch"
        ).count()
        return format_html(
            f"<strong style='color:green'>{count} entries</strong>"
        )
    
    @admin.display(description="Ledger Status")
    def ledger_status(self, obj):
        from ingredients.models import IngredientStockLedger
        entries = IngredientStockLedger.objects.filter(
            related_prepared_item=obj.prepared_item,
            change_type=IngredientStockLedger.ADJUSTMENT,
            note__contains="Kitchen batch"
        )
        if entries.exists():
            return format_html(
                f"<strong style='color:green'>✓ {entries.count()} ledger entries created</strong><br/>"
                f"<small>Stock automatically deducted via ADJUSTMENT entries</small>"
            )
        return format_html(
            f"<strong style='color:orange'>No ledger entries yet</strong><br/>"
            f"<small>Create entries using the action button</small>"
        )
    
    actions = ["create_ledger_entries"]
    
    @admin.action(description="Create ledger entries for selected batches")
    def create_ledger_entries(self, request, queryset):
        created_count = 0
        error_count = 0
        
        for batch in queryset:
            try:
                entries = batch.create_ledger_entries()
                created_count += len(entries)
            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Error creating ledger for {batch}: {str(e)}",
                    messages.ERROR,
                )
        
        if created_count > 0:
            self.message_user(
                request,
                f"Created {created_count} ledger entries for {len(queryset)} batch(es).",
                messages.SUCCESS,
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"{error_count} batch(es) had errors.",
                messages.WARNING,
            )

