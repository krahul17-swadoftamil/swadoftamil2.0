# Deprecation Task: _stock_qty Removal (Phase 1)

## Summary
Deprecated the `_stock_qty` field to eliminate dual stock truth and make the IngredientStockLedger the single, authoritative source of ingredient quantities.

## Changes Made

### 1. **Field Definition Update** (backend/ingredients/models.py:78-91)
**Before:**
```python
_stock_qty = models.DecimalField(
    # ... editable=True (default)
    help_text="DEPRECATED: Stock calculated from ledger entries"
)
```

**After:**
```python
_stock_qty = models.DecimalField(
    # ... editable=False,
    help_text="⚠️  DEPRECATED: Kept for migration safety only..."
)
```

**Impact:**
- Field cannot be edited in Django admin or forms
- Database still contains it (for migration compatibility)
- All lookups bypass this field

### 2. **Stock Property Refactoring** (backend/ingredients/models.py:196-231)
**Before:**
```python
@property
def stock_qty(self):
    if not self.pk:
        return self._stock_qty  # Used cached field
    return self.stock_ledger.aggregate(...)['total'] or QTY0
```

**After:**
```python
@property
def stock_qty(self):
    # Always returns 0 for new items, queries ledger for saved items
    if not self.pk:
        return QTY0
    return self.stock_ledger.aggregate(...)['total'] or QTY0
```

**Plus: Deprecated Setter**
```python
@stock_qty.setter
def stock_qty(self, value):
    """DEPRECATED: Create IngredientStockLedger entries instead."""
    warnings.warn(..., DeprecationWarning)
    # Still works for backward compat, creates ADJUSTMENT entry
```

**Impact:**
- Property ALWAYS queries ledger (never cached or field-based)
- Direct assignment triggers DeprecationWarning
- Programmatic code still works but logs warning

### 3. **Removed update_stock_from_ledger()** (backend/ingredients/models.py:260-271)
**Before:**
```python
def update_stock_from_ledger(self):
    new_stock = self.stock_ledger.aggregate(...)['total'] or QTY0
    self._stock_qty = new_stock
    self.save(update_fields=['_stock_qty'])
```

**After:**
```python
def update_stock_from_ledger(self):
    """DEPRECATED: This method is no longer needed."""
    warnings.warn(..., DeprecationWarning)
    # Method now does nothing except warn
```

**Impact:**
- Any code calling this shows DeprecationWarning
- Method kept for backward compatibility (won't break imports)
- Will be removed in Phase 2

### 4. **Simplified save() Logic** (backend/ingredients/models.py:276-287)
**Before:**
```python
def save(self, *args, **kwargs):
    # ...captured old_qty from _stock_qty snapshot
    with transaction.atomic():
        super().save(*args, **kwargs)
        if old_qty != self.stock_qty:
            IngredientMovement.objects.create(...)
```

**After:**
```python
def save(self, *args, **kwargs):
    # ...no snapshot comparison
    with transaction.atomic():
        super().save(*args, **kwargs)
    # Movement logging handled by signals on IngredientStockLedger
```

**Impact:**
- Removed coupling between Ingredient and IngredientMovement
- Movement history now flows from ledger signals only
- Eliminates phantom movements from _stock_qty snapshot issues

### 5. **Documentation Updates** (backend/ingredients/models.py:32-41)
Added deprecation notice to Ingredient docstring:
```python
"""
...
⚠️  DEPRECATION: _stock_qty field is kept for migration safety but NO LONGER USED.
ALL stock calculations use the stock_qty property (queries ledger directly).
See DEPRECATION_GUIDE.md for removal timeline.
"""
```

## Files Modified
- ✅ [backend/ingredients/models.py](backend/ingredients/models.py)
- ✅ [DEPRECATION_GUIDE.md](DEPRECATION_GUIDE.md) (new)

## Validation
✅ `python manage.py check` - System check identified **no issues**
✅ `stock_qty` property returns correct values
✅ Field marked as non-editable
✅ Deprecation warnings in place

## Backward Compatibility
- ✅ Existing code that reads `ingredient.stock_qty` still works
- ✅ Database column still exists (safe for migrations)
- ✅ Code that sets `stock_qty` property still works (with warning)
- ✅ `_stock_qty` field accessible for migration/reporting

## What Gets Removed (Phase 2 - Target: v1.6-1.7)
1. `_stock_qty` field definition
2. `stock_qty.setter` logic
3. `update_stock_from_ledger()` method
4. `_stock_qty` column in database migration

## What Works Going Forward
✅ All reads: `ingredient.stock_qty`
✅ All writes: Create `IngredientStockLedger` entries
✅ Audit trail: Full ledger history
✅ Properties: `is_low_stock()`, `total_value`, etc.

## Developer Migration Guide
See [DEPRECATION_GUIDE.md](DEPRECATION_GUIDE.md) for:
- Phase-by-phase timeline
- Code examples (old vs. new way)
- Affected areas to update
- Testing strategy
