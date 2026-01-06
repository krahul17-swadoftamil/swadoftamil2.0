# Deprecation Guide: _stock_qty Removal Plan

## Overview
This document outlines the long-term plan to remove the `_stock_qty` field and establish the ledger as the single source of truth for ingredient stock.

## Current Status
- ✅ Field marked as deprecated (editable=False)
- ✅ Property always queries ledger as source of truth
- ✅ `update_stock_from_ledger()` deprecated (triggers DeprecationWarning)
- ✅ Setter deprecated (triggers DeprecationWarning)
- ✅ Save logic no longer depends on `_stock_qty` snapshot

## Phase 1: Deprecation Warnings (CURRENT)
**Status:** ACTIVE (now through v1.5)
**Changes:**
- `_stock_qty` field marked `editable=False`
- Property always uses ledger queries (not `_stock_qty`)
- `update_stock_from_ledger()` shows DeprecationWarning
- `stock_qty` setter shows DeprecationWarning
- Ingredient.save() simplified: no `old_qty` comparison

**Developer Impact:**
- Can still read `_stock_qty` (for queries in edge cases)
- Database still syncs it (for safety/reporting)
- Warnings when code tries to set/update it

## Phase 2: Ledger-Only (Target: v1.6-1.7)
**When:** After 2-3 months of stable deprecation warnings
**Changes:**
- Remove `_stock_qty` field definition entirely
- Remove setter logic completely
- Remove `update_stock_from_ledger()` method
- Add database migration to drop column

**Developer Impact:**
- Any code trying to write `_stock_qty` breaks at runtime
- Must use IngredientStockLedger ORM for all changes
- All queries must use `stock_qty` property

## Phase 3: Full Removal (Target: v2.0)
**When:** Next major version
**Changes:**
- Potential query optimizations (materialized views, caching strategy)
- API simplification (fewer internal fields)

## Migration Path for Developers

### ❌ OLD WAY (DEPRECATED)
```python
# Don't do this anymore:
ingredient._stock_qty = Decimal("100")
ingredient.save()

ingredient.stock_qty = Decimal("50")  # Triggers warning

ingredient.update_stock_from_ledger()  # Triggers warning
```

### ✅ NEW WAY (REQUIRED)
```python
# Use ledger for all stock changes:
from ingredients.models import IngredientStockLedger

# For purchases:
IngredientStockLedger.objects.create(
    ingredient=ingredient,
    change_type=IngredientStockLedger.PURCHASE,
    quantity_change=Decimal("100"),
    unit=ingredient.unit,
    note="Vendor delivery"
)

# For adjustments:
IngredientStockLedger.objects.create(
    ingredient=ingredient,
    change_type=IngredientStockLedger.ADJUSTMENT,
    quantity_change=Decimal("-50"),
    unit=ingredient.unit,
    note="Damage/expiry during inspection"
)

# To read current stock (always correct):
current = ingredient.stock_qty  # Queries ledger directly
```

## Affected Code Areas

### Will Need Updates (Phase 2)
1. **Admin Queries:**
   - `IngredientAdmin.get_queryset()` - Any `.values_list('_stock_qty')`
   - Search filters based on `_stock_qty`

2. **API Serializers:**
   - Check `serializers.py` if `_stock_qty` is exposed

3. **Management Commands:**
   - Any scripts in `management/commands/` using `_stock_qty`

4. **Analytics/Reports:**
   - Dashboard queries using `_stock_qty` directly

### Safe to Keep
1. **Signal Handlers:**
   - IngredientStockLedger signals (create IngredientMovement)
   - Use these going forward for audit trails

2. **Property Access:**
   - `ingredient.stock_qty` - Always works
   - `ingredient.total_value` - Uses stock_qty property
   - `ingredient.is_low_stock()` - Uses stock_qty property

3. **Ledger Patterns:**
   - All `IngredientStockLedger` operations
   - All signal handling on ledger.save()

## Testing Strategy

### Phase 1 (Current)
- Monitor logs for DeprecationWarning messages
- Audit codebase for setter usage
- Count occurrences of `update_stock_from_ledger()`

### Phase 2
- Create test that fails if anyone tries to write `_stock_qty`
- Ensure ledger-only approach works for all stock scenarios
- Performance test: verify ledger SUM is fast enough

## References
- Ingredient model: [backend/ingredients/models.py](backend/ingredients/models.py)
- Ledger pattern: IngredientStockLedger.save() signals
- Related: [ORDER_COMPLETION_SERVICE.md](ORDER_COMPLETION_SERVICE.md) for ledger usage examples
