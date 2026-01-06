# StoreStatus Update: Master Switch Only

## Overview
StoreStatus has been updated to be a **master switch** for emergency/manual overrides only. Timing logic has been moved to StoreShift.

---

## Before vs After

### ❌ BEFORE (Misused)
```python
class StoreStatus(models.Model):
    is_open = models.BooleanField()        # Did timing + override
    open_time = models.TimeField()         # ❌ REMOVED
    close_time = models.TimeField()        # ❌ REMOVED
    note = models.CharField()

    @property
    def is_currently_open(self):           # Complex timing logic
        # Handle same-day, overnight, manual override...
```

### ✅ AFTER (Correct)
```python
class StoreStatus(models.Model):
    is_enabled = models.BooleanField()     # Master switch only
    note = models.CharField()              # Emergency message

    @property
    def is_master_switch_on(self):         # Simple boolean
        return self.is_enabled
```

---

## Purpose: Emergency/Manual Override

StoreStatus is now **exclusively** for:

### Emergency Situations
- **Power outage:** Turn OFF immediately
- **Water supply issue:** Turn OFF until fixed
- **Staff shortage:** Turn OFF for safety
- **Equipment failure:** Turn OFF until repaired

### Planned Closures
- **Festival holidays:** Turn OFF for Diwali/Pongal
- **Maintenance:** Turn OFF for deep cleaning
- **Owner absence:** Turn OFF when no management present

### Manual Override
- **Weather emergency:** Turn OFF for safety
- **Local event:** Turn OFF for traffic/parking issues
- **Health inspection:** Turn OFF if needed

---

## How It Works

### Master Switch Logic
```python
# Store can operate ONLY if:
# 1. Master switch is ON (StoreStatus.is_enabled = True)
# 2. AND at least one shift is active (StoreShift.is_open_now() = True)

def can_accept_orders():
    master_switch = StoreStatus.objects.get().is_master_switch_on
    shifts_active = StoreShift.is_open_now()
    return master_switch and shifts_active
```

### Example Scenarios

#### Normal Operation
```
StoreStatus.is_enabled = True    ✅
StoreShift.is_open_now() = True  ✅
Result: Store accepts orders     ✅
```

#### Emergency Close
```
StoreStatus.is_enabled = False   ❌ (Emergency!)
StoreShift.is_open_now() = True  ✅
Result: Store closed             ❌
```

#### Shift Closed
```
StoreStatus.is_enabled = True    ✅
StoreShift.is_open_now() = False ❌ (No active shifts)
Result: Store closed             ❌
```

#### Both Closed
```
StoreStatus.is_enabled = False   ❌
StoreShift.is_open_now() = False ❌
Result: Store closed             ❌
```

---

## Admin Interface

**Location:** `/admin/core/storestatus/`

**Purpose:** Emergency control panel

**Features:**
- Big red "ENABLED/DISABLED" status
- Note field for customer message
- Single toggle for emergency situations
- Clear "Master Switch Control" section

**When to Use:**
- Staff should **rarely** touch this
- Only for true emergencies or planned closures
- Normal daily operations use StoreShift toggles

---

## Integration Points

### Order Creation
```python
# In Order.save() or API endpoint:
from core.models import StoreStatus, StoreShift

def can_accept_order():
    master = StoreStatus.objects.get().is_master_switch_on
    shifts = StoreShift.is_open_now()
    return master and shifts

if not can_accept_order():
    raise ValidationError("Store is currently closed")
```

### Frontend Display
```javascript
// API endpoint: /api/store/status/
{
  "master_switch": true,      // StoreStatus.is_enabled
  "shifts_active": false,     // StoreShift.is_open_now()
  "can_accept_orders": false, // master_switch && shifts_active
  "message": "Closed for festival"  // StoreStatus.note
}
```

### Kitchen Dashboard
```python
# Show status prominently:
master = StoreStatus.objects.get()
if not master.is_enabled:
    # Show big red "EMERGENCY CLOSED" banner
    # Display note to staff
```

---

## Migration Details

**Migration:** `core/migrations/0006_rename_is_open_to_is_enabled.py`
- Renames `is_open` → `is_enabled`
- Preserves existing data
- Updates help text and logic

---

## Code Changes

### Files Modified
- ✅ `backend/core/models.py` — Updated StoreStatus model
- ✅ `backend/core/admin.py` — Updated admin interface
- ✅ Database — Field renamed via migration

### Backward Compatibility
- ✅ Existing data preserved
- ✅ Admin interface updated
- ✅ Property names changed (old ones removed)

---

## Testing Checklist

- [x] Migration applies successfully
- [x] Admin interface shows "ENABLED/DISABLED"
- [x] Master switch logic works
- [x] Integration with StoreShift works
- [x] Django system check passes

---

## Usage Guidelines

### For Staff
1. **Normal operation:** Leave master switch ON
2. **Emergency:** Turn OFF immediately, add note
3. **Planned close:** Turn OFF in advance with note
4. **Reopen:** Turn ON when situation resolved

### For Developers
1. **Check both:** Always verify `master_switch && shifts_active`
2. **Error messages:** Use StoreStatus.note for user-friendly messages
3. **Logging:** Log master switch changes for audit trail
4. **API:** Expose status via dedicated endpoint

---

## Related Models

- **StoreShift:** Handles timing (when store should be open)
- **Order:** Should check both master switch + active shifts
- **Frontend:** Should show appropriate closed messages

---

## Future Enhancements

1. **Audit log:** Track who toggles master switch and when
2. **Scheduled overrides:** Auto-toggle for planned closures
3. **Multiple switches:** Separate switches for different closures
4. **Notifications:** Alert staff when master switch is toggled
