"""
Kitchen Batch Service

Handles batch preparation tracking for items prepared before orders.

Purpose:
- Sambar, chutneys, and other pre-prep items are made in batches
- When a batch is prepared, we log ingredient consumption
- Uses ADJUSTMENT ledger entries (not CONSUMPTION - which is order-based only)
- Maintains operational clarity without breaking audit rules

Example:
    Kitchen prepares 50L of Sambar in the morning
    → KitchenBatch created
    → Ingredient ledger updated with ADJUSTMENT entries
    → Stock levels decrease
    → Orders consume from prepared stock
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from ingredients.models import IngredientStockLedger


def create_kitchen_batch(prepared_item, batch_size, note_prefix="Kitchen batch prep"):
    """
    Log a batch preparation as ADJUSTMENT ledger entries.
    
    Args:
        prepared_item: PreparedItem instance being prepared
        batch_size: Quantity prepared (in PreparedItem.serving_size units)
        note_prefix: Custom prefix for ledger note (default: "Kitchen batch prep")
    
    Returns:
        List of created IngredientStockLedger entries
    
    Raises:
        ValidationError: If prepared_item has no recipe
    """
    if not prepared_item.recipe_items.exists():
        raise ValidationError(f"Cannot batch prepare '{prepared_item.name}' - no recipe defined.")
    
    batch_size = Decimal(str(batch_size))
    
    if batch_size <= 0:
        raise ValidationError("Batch size must be greater than 0.")
    
    ledger_entries = []
    
    with transaction.atomic():
        for recipe in prepared_item.recipe_items.all():
            # Calculate total ingredient needed for this batch
            # recipe.quantity is per serving, batch_size is in servings
            total_quantity_needed = recipe.quantity * batch_size
            
            # Convert to ingredient base unit
            required_base = recipe.ingredient.to_base_unit(
                total_quantity_needed,
                recipe.quantity_unit
            )
            
            # Create ADJUSTMENT ledger entry (negative = consumption, but as adjustment)
            entry = IngredientStockLedger.objects.create(
                ingredient=recipe.ingredient,
                change_type=IngredientStockLedger.ADJUSTMENT,
                quantity_change=-required_base,  # Negative = stock deduction
                unit=recipe.ingredient.unit,
                related_prepared_item=prepared_item,
                note=f"{note_prefix}: {prepared_item.name} × {batch_size} {prepared_item.unit}"
            )
            ledger_entries.append(entry)
    
    return ledger_entries


def log_kitchen_batch_info(prepared_item, batch_size):
    """
    Generate a human-readable batch prep summary.
    
    Useful for kitchen displays or logs.
    """
    summary = {
        "prepared_item": prepared_item.name,
        "batch_size": f"{batch_size} {prepared_item.unit}",
        "timestamp": timezone.now().isoformat(),
        "ingredients": []
    }
    
    for recipe in prepared_item.recipe_items.all():
        total_qty = recipe.quantity * Decimal(str(batch_size))
        summary["ingredients"].append({
            "name": recipe.ingredient.name,
            "quantity": f"{total_qty} {recipe.quantity_unit}",
            "unit": recipe.ingredient.unit,
        })
    
    return summary
