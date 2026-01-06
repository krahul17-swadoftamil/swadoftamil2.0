# 📜 SWAD OF TAMIL — BUSINESS RULES

**This document is LAW for the system. If code doesn't follow these rules, it's a bug.**

---

## 1️⃣ STOCK EXISTS ONLY IN INGREDIENT

**Rule:** The ONE AND ONLY source of ingredient quantities is the `Ingredient` model.

```
Ingredient.stock_qty = SUM of all IngredientStockLedger entries
```

### What This Means:
- ✅ Query Ingredient.stock_qty (it auto-calculates from ledger)
- ❌ Never query `_stock_qty` field directly
- ❌ Never store stock in PreparedItem, Combo, or Order
- ❌ Never cache stock in memory (always query fresh)

### Why:
- **Single point of truth** = no conflicting quantities
- **Audit trail** = every change logged immutably
- **Real-time accuracy** = stock always current

### Example:
```python
# ✅ CORRECT
tomato = Ingredient.objects.get(name="Tomato")
current_stock = tomato.stock_qty  # Always fresh from ledger

# ❌ WRONG
# Don't do this:
current_stock = tomato._stock_qty  # Deprecated field
current_stock = cache.get('tomato_stock')  # Stale data
```

---

## 2️⃣ RECIPES NEVER DEDUCT STOCK

**Rule:** Creating or editing a recipe does NOT change ingredient quantities.

### What This Means:
- ✅ Add recipes freely (flour + eggs + salt = cake)
- ❌ Stock only deducts when ORDER is completed
- ❌ Admin cannot manually deduct via recipe form
- ❌ Saving a recipe has ZERO impact on quantities

### Why:
- Recipes are **templates**, not transactions
- Stock deduction must be **intentional** (via order completion)
- Recipe changes must never affect inventory

### Example:
```python
# Creating/editing this recipe does NOT deduct stock
cake_recipe = PreparedItemRecipe.objects.create(
    prepared_item=cake,
    ingredient=flour,
    quantity_in_base_unit=Decimal("0.500"),
)
# Stock unchanged! ✓
```

---

## 3️⃣ ORDERS DEDUCT STOCK, NOT ADMIN

**Rule:** The ONLY legitimate way to reduce ingredient stock is via **Order Completion**.

### What This Means:
- ✅ Order placed → staff completes it → `complete_order(order)` called → stock deducted
- ✅ Admin can log manual adjustments via ADJUSTMENT ledger entries
- ❌ Admin cannot manually deduct via "CONSUMPTION" change type
- ❌ Stock never deducts from recipe editing, batch creation, or dashboard actions

### Ledger Entry Types:
| Type | Who | When | Permission |
|------|-----|------|-----------|
| OPENING | Admin | Initial setup | Init only |
| PURCHASE | Admin | Vendor delivery | Staff with invoice |
| **CONSUMPTION** | Backend only | Order completion | Orders service only |
| ADJUSTMENT | Admin | Damage/expiry/recount | Finance staff |
| WASTAGE | Staff | Production loss | Kitchen staff |

### Why:
- Orders = legal contracts (must be honored in system)
- Admin adjustments = transparency + approval trail
- Prevents accidental deductions

### Example:
```python
# ✅ CORRECT — Order completion
from orders.services import complete_order
order = Order.objects.get(id=123)
complete_order(order)  # Creates CONSUMPTION entries

# ❌ WRONG — Admin trying to deduct
# Don't do this in admin form:
IngredientStockLedger.objects.create(
    ingredient=flour,
    change_type=IngredientStockLedger.CONSUMPTION,  # Blocked!
    quantity_change=Decimal("-1"),
)
```

---

## 4️⃣ BATCH RECIPE QUANTITIES = PER BATCH

**Rule:** When a PreparedItem uses BATCH mode, recipe quantities are per-batch, not per-serving.

### What This Means:
- ✅ BATCH mode: "Make 50 servings → requires 500g flour"
- ✅ PER_SERVING mode: "Make 1 serving → requires 10g flour"
- ❌ Never mix units (e.g., "10g per serving" then use as batch total)
- ❌ `batch_output_quantity` is REQUIRED for BATCH mode

### How to Set Up:
```python
# BATCH MODE — Quantities are per-batch
cake = PreparedItem.objects.create(
    name="Birthday Cake",
    mode=PreparedItem.MODE_BATCH,
    batch_output_quantity=50,  # REQUIRED! Must be > 1
)

# Recipe: per 50-serving batch
PreparedItemRecipe.objects.create(
    prepared_item=cake,
    ingredient=flour,
    quantity_in_base_unit=Decimal("5.000"),  # 5 kg for 50 servings
)

# PER_SERVING MODE — Quantities are per single serving
curry = PreparedItem.objects.create(
    name="Chicken Curry",
    mode=PreparedItem.MODE_PER_SERVING,
    # no batch_output_quantity needed
)

# Recipe: per 1 serving
PreparedItemRecipe.objects.create(
    prepared_item=curry,
    ingredient=flour,
    quantity_in_base_unit=Decimal("0.100"),  # 100g per serving
)
```

### Why:
- Batch productions need different math than per-serving
- Prevents "50 servings each needs 5kg" confusion
- Admin UI blocks incomplete BATCH configurations

### Admin Enforcement:
When editing PreparedItem in admin:
- ✅ Can edit recipes in PER_SERVING mode
- ❌ Cannot edit recipes in BATCH mode unless `batch_output_quantity` is set

---

## 5️⃣ AVAILABILITY IS ALWAYS FLOORED

**Rule:** Available quantity MUST use integer division (⌊stock / serving_size⌋), never floating point.

### What This Means:
```
Stock: 2.5 kg
Recipe per serving: 0.3 kg
Availability: ⌊2.5 / 0.3⌋ = ⌊8.33⌋ = 8 servings (not 8.33!)
```

- ✅ Use `//` (floor division) in Python
- ✅ Cannot sell 0.33 of a serving
- ❌ Never round (could sell 0.01 extra)
- ❌ Never use floating point as final answer

### Example:
```python
# ✅ CORRECT — Floor division
availability = int(ingredient.stock_qty // recipe.quantity_per_serving)

# ❌ WRONG
availability = ingredient.stock_qty / recipe.quantity_per_serving  # Float!
availability = round(ingredient.stock_qty / recipe.quantity_per_serving)  # Rounds!
availability = ceil(ingredient.stock_qty / recipe.quantity_per_serving)  # Over-sells!
```

### Why:
- Cannot partially fulfill a serving
- Prevents selling phantom inventory
- Ensures exact deduction at order completion

---

## 6️⃣ ADJUSTMENTS ≠ CONSUMPTION

**Rule:** Manual stock changes use ADJUSTMENT, not CONSUMPTION.

### Correct Uses:
| Entry Type | Example | Who | Approval |
|-----------|---------|-----|----------|
| CONSUMPTION | Order complete: 1 kg flour deducted | Backend/Orders | Automatic (trusted) |
| ADJUSTMENT | Found 2kg extra during recount | Finance | Manager approval |
| ADJUSTMENT | Discarded 0.5kg expired milk | Kitchen | Waste log |
| ADJUSTMENT | Corrected ledger after audit | Finance | Audit trail |

### Why This Split:
- **CONSUMPTION** = linked to orders (automatic, auditable)
- **ADJUSTMENT** = manual corrections (requires documentation)
- Reports can filter by type
- Different approval workflows

### Example:
```python
# ✅ CORRECT — During inventory recount
IngredientStockLedger.objects.create(
    ingredient=flour,
    change_type=IngredientStockLedger.ADJUSTMENT,  # Not CONSUMPTION
    quantity_change=Decimal("2.000"),
    unit=flour.unit,
    note="Physical recount found extra stock"
)

# ❌ WRONG
# Never use CONSUMPTION manually:
IngredientStockLedger.objects.create(
    ingredient=flour,
    change_type=IngredientStockLedger.CONSUMPTION,  # Blocked in admin forms
    quantity_change=Decimal("-1.000"),
)
```

---

## 7️⃣ LEDGER IS IMMUTABLE AUDIT TRAIL

**Rule:** IngredientStockLedger entries MUST NEVER be edited or deleted.

### What This Means:
- ✅ Create new ledger entries to correct mistakes
- ✅ Query historical ledger to understand stock changes
- ❌ Never UPDATE or DELETE existing entries
- ❌ Never manually set `_stock_qty` field

### Why:
- Every entry is a **legal record** (auditable, traceable)
- Deleting breaks stock calculations
- Updates hide the truth
- Finance/compliance require immutability

### Example:
```python
# ✅ CORRECT — Fix a mistake by creating opposite entry
wrong_entry = IngredientStockLedger.objects.get(id=123)
# Don't edit it!

# Instead, create correction:
IngredientStockLedger.objects.create(
    ingredient=wrong_entry.ingredient,
    change_type=IngredientStockLedger.ADJUSTMENT,
    quantity_change=-wrong_entry.quantity_change,  # Reverse it
    unit=wrong_entry.unit,
    note=f"Correcting entry {wrong_entry.id}"
)

# ❌ WRONG
wrong_entry.quantity_change = Decimal("100")
wrong_entry.save()  # NEVER!

wrong_entry.delete()  # NEVER!
```

---

## 8️⃣ PREPARED ITEM AVAILABILITY = INTELLIGENT CALCULATION

**Rule:** Availability automatically considers recipes, stock, and mode.

### What This Means:
```python
available = PreparedItem.available_quantity  # Smart property

# PER_SERVING mode:
# Checks: "How many complete servings can we make with current stock?"

# BATCH mode:
# Checks: "Can we make a complete batch with current stock?"
```

### Real Example:
```
Menu Item: Samosa (PER_SERVING)
Recipe: 50g flour per samosa
Current Stock: 10 kg flour
Available: ⌊10000g / 50g⌋ = 200 samosas

Menu Item: Biryani (BATCH)
Recipe: 5kg rice per 10-serving batch
Current Stock: 15 kg rice
Available: ⌊15 / 5⌋ = 3 complete batches (30 servings)
```

### Why:
- Availability always **truthful** (matches actual deduction logic)
- Prevents over-selling
- Updates in real-time as stock changes

---

## 9️⃣ COST CALCULATIONS REQUIRE STOCK

**Rule:** Cannot compute dish cost if any ingredient is out of stock.

### What This Means:
- ✅ Cost recipes when all ingredients have stock
- ✅ Use fallback pricing IF explicitly enabled AND fallback cost exists
- ❌ Never price a dish with zero-stock ingredient
- ❌ Never rely on estimated/old costs

### Why:
- Cost accuracy is critical for profitability
- Out-of-stock ingredients = cannot fulfill order = cost invalid
- Fallback pricing is optional safety valve only

### Example:
```python
# ✅ CORRECT
try:
    cost = samosa.cost_per_unit()
except ValidationError:
    # Out of stock or no fallback — cannot cost this item
    message = "Cannot cost samosa: ingredient missing"

# ❌ WRONG
# Never guess costs or use cached prices
cost = samosa.old_cost  # What if prices changed?
cost = estimate_cost()  # What if stock is zero?
```

---

## 🔟 ADMIN FORMS ENFORCE RULES

**Rule:** Django admin forms block rule violations at the UI level.

### What's Blocked:
- ✅ Cannot create CONSUMPTION ledger entry (form validation)
- ✅ Cannot edit recipes in BATCH mode without `batch_output_quantity`
- ✅ Cannot save Ingredient with negative stock
- ✅ Cannot create Combo with incomplete recipes
- ✅ Cannot mark order complete if not all items have recipes

### Why:
- **Defense in depth**: forms + models + services all validate
- User-friendly errors (not backend crashes)
- Consistent enforcement across web/API/scripts

### Example:
```python
# Admin tries to create CONSUMPTION entry
# Form validation catches it:
# "CONSUMPTION entries are created by order completion, not manually"

# Admin tries to edit BATCH recipe without batch_output_quantity
# Admin form disables the inline recipe editor:
# "Set batch_output_quantity before editing recipes"
```

---

## 📋 IMPLEMENTATION CHECKLIST

When building features, verify:

- [ ] Stock reads use `ingredient.stock_qty` property
- [ ] Stock writes create `IngredientStockLedger` entries
- [ ] Recipes are templates (never deduct stock)
- [ ] Only `complete_order()` creates CONSUMPTION entries
- [ ] BATCH recipes have `batch_output_quantity` > 1
- [ ] Availability uses floor division (`//`)
- [ ] Adjustments use `ADJUSTMENT` type, not `CONSUMPTION`
- [ ] Ledger entries are never edited/deleted
- [ ] Cost calculations fail fast if out of stock
- [ ] Admin forms validate business rules

---

## 🆘 COMMON MISTAKES

### ❌ "I'll store stock in PreparedItem for speed"
**Why it breaks:** Dual truth. When you update Ingredient, PreparedItem is stale.

### ❌ "I'll deduct stock in the recipe save() method"
**Why it breaks:** Recipes are templates! Saving a recipe doesn't mean you made the dish.

### ❌ "I'll use floating point availability"
**Why it breaks:** 8.33 servings is impossible. You can only make 8.

### ❌ "Admin can manually log CONSUMPTION"
**Why it breaks:** CONSUMPTION is for legal orders only. Manual changes = ADJUSTMENT.

### ❌ "I'll delete the wrong ledger entry"
**Why it breaks:** Audit trail corrupted. Create a correcting entry instead.

### ❌ "I'll cache stock to speed up queries"
**Why it breaks:** Stock changes in real-time. Cache becomes stale.

---

## 📞 QUESTIONS?

If you're unsure:
1. Check this RULES.md
2. Look at existing implementations (orders/services.py, menu/kitchen_batch.py)
3. Ask before building

**These rules aren't suggestions. They're load-bearing. Breaking them silently corrupts the system.**
