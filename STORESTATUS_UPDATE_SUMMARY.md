# StoreStatus Update Summary

## ✅ Updated: StoreStatus → Master Switch Only

**Status:** COMPLETE  
**Migration:** `core/migrations/0006_rename_is_open_to_is_enabled.py`  
**Purpose:** Emergency/manual override control only  

---

## Changes Made

### 1. **Field Renamed** (backend/core/models.py)
**Before:**
```python
is_open = models.BooleanField(
    help_text="Manual override. Turn OFF to force close store."
)
```

**After:**
```python
is_enabled = models.BooleanField(
    help_text="MASTER SWITCH: Turn OFF to force close store (emergency/festival/power cut)"
)
```

### 2. **Property Renamed**
**Before:**
```python
@property
def is_currently_open(self):
    return self.is_open
```

**After:**
```python
@property
def is_master_switch_on(self):
    return self.is_enabled
```

### 3. **Docstring Updated**
**Before:** "Single-row model to control store availability"
**After:** "MASTER SWITCH — Emergency/Manual Override Control"

### 4. **Purpose Clarified**
StoreStatus is now **exclusively** for:
- ✅ Emergency close (power outage)
- ✅ Festival close (Diwali/Pongal)
- ✅ Manual override (any urgent situation)
- ❌ **NOT** for timing (that's StoreShift)

### 5. **Admin Interface Updated** (backend/core/admin.py)
- Field name: `is_open` → `is_enabled`
- Section title: "Master Switch Control"
- Description: "Emergency override. Turn OFF to force close store."
- Status display: "ENABLED/DISABLED"

---

## How It Works Now

### Master Switch Logic
```python
# Store can accept orders ONLY if:
master_switch_on = StoreStatus.objects.get().is_master_switch_on  # True/False
shifts_active = StoreShift.is_open_now()                          # True/False
can_accept_orders = master_switch_on and shifts_active            # Both must be True
```

### Example Scenarios

| Master Switch | Shifts Active | Result | Use Case |
|---------------|---------------|--------|----------|
| ✅ ON | ✅ Active | 🟢 Open | Normal operation |
| ❌ OFF | ✅ Active | 🔴 Closed | Emergency/festival |
| ✅ ON | ❌ None | 🔴 Closed | Outside shift hours |
| ❌ OFF | ❌ None | 🔴 Closed | Double-closed |

---

## Integration Pattern

### Order Validation
```python
from core.models import StoreStatus, StoreShift

def validate_order_placement():
    master = StoreStatus.objects.get().is_master_switch_on
    shifts = StoreShift.is_open_now()
    
    if not master:
        raise ValidationError("Store is closed for emergency/maintenance")
    if not shifts:
        raise ValidationError("Store is outside operating hours")
```

### API Response
```json
{
  "master_switch_enabled": true,
  "shifts_active": false,
  "store_open": false,
  "message": "Closed for festival"
}
```

---

## Files Modified

- ✅ `backend/core/models.py` — Updated StoreStatus model
- ✅ `backend/core/admin.py` — Updated admin interface
- ✅ Database — Migration applied successfully

---

## Verification Results

✅ Migration applied: `0006_rename_is_open_to_is_enabled`  
✅ Django system check: **0 issues**  
✅ Model properties work: `is_master_switch_on`, `status_label`  
✅ Admin interface updated: Shows "ENABLED/DISABLED"  
✅ Existing data preserved: Field rename successful  

---

## Usage Guidelines

### For Staff
- **Normal operation:** Keep master switch ENABLED
- **Emergency:** Turn OFF immediately with note
- **Planned close:** Turn OFF in advance with customer message
- **Daily timing:** Use StoreShift toggles instead

### For Developers
- **Always check both:** Master switch + active shifts
- **Error messages:** Use StoreStatus.note for user-friendly text
- **API endpoints:** Expose status via dedicated endpoint
- **Logging:** Consider logging master switch changes

---

## Related Documentation

- [STORESHIFT_GUIDE.md](STORESHIFT_GUIDE.md) — Timing system
- [RULES.md](RULES.md) — Business rules
- [STORESTATUS_UPDATE.md](STORESTATUS_UPDATE.md) — This update

---

## Next Steps (Optional)

1. **Order integration:** Add master switch check to Order.save()
2. **API endpoint:** Create `/api/store/status/` endpoint
3. **Frontend:** Show appropriate closed messages
4. **Audit log:** Track master switch changes
5. **Notifications:** Alert staff when toggled
