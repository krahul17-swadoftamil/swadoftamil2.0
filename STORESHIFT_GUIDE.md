# StoreShift Model — Multi-Shift Timing System

## Overview
The `StoreShift` model defines operating time windows (shifts) for the restaurant. This replaces the old single `open_time`/`close_time` logic and supports multiple overlapping or non-overlapping shifts.

---

## Model Definition

```python
class StoreShift(models.Model):
    name = models.CharField(max_length=20)      # "Morning", "Evening", etc.
    start_time = models.TimeField()             # 09:30
    end_time = models.TimeField()               # 14:00
    is_active = models.BooleanField()           # Toggle to enable/disable
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
```

---

## Default Shifts (Swad of Tamil)

| Shift | Time | Status |
|-------|------|--------|
| Morning | 09:30 – 14:00 | ✓ Active |
| Evening | 18:00 – 22:00 | ✓ Active |

---

## Available Methods

### Instance Methods

#### `shift.is_currently_active`
Check if this specific shift is active right now.

```python
morning = StoreShift.objects.get(name="Morning")
if morning.is_currently_active:
    print("Morning shift is running now")
```

---

### Class Methods

#### `StoreShift.get_active_shifts()`
Get all active shifts (ordered by start time).

```python
active = StoreShift.get_active_shifts()
for shift in active:
    print(f"{shift.name}: {shift.start_time} - {shift.end_time}")
```

#### `StoreShift.current_shift()`
Get the shift currently in progress, or `None`.

```python
now = StoreShift.current_shift()
if now:
    print(f"Currently in {now.name} shift")
else:
    print("Store is closed")
```

#### `StoreShift.is_open_now()`
Check if **any** shift is currently active.

```python
if StoreShift.is_open_now():
    print("Store is open now")
else:
    print("All shifts closed")
```

---

## Usage Examples

### Order Placement (API)
```python
# Accept orders only if a shift is active
from core.models import StoreShift

if StoreShift.is_open_now():
    # Create order
    order = Order.objects.create(...)
else:
    raise ValidationError("Store is closed. Open shifts: " + str(StoreShift.get_active_shifts()))
```

### Kitchen Dashboard
```python
# Show current shift and time remaining
current = StoreShift.current_shift()
if current:
    print(f"Working on {current.name} shift until {current.end_time}")
```

### Delivery Scheduling
```python
# Only allow deliveries during active shifts
delivery_shift = StoreShift.current_shift()
if delivery_shift:
    delivery.scheduled_shift = delivery_shift
    delivery.save()
```

### Admin Toggle
The admin interface allows staff to:
- View all shifts with times
- Enable/disable shifts without deleting
- See real-time status ("RUNNING NOW" 🟢)
- Edit shift times (changes apply immediately)

---

## Special Cases

### Overnight Shifts
If a shift spans midnight (e.g., 22:00 → 06:00):

```python
StoreShift.objects.create(
    name="Late Night",
    start_time=time(22, 0),   # 10 PM
    end_time=time(6, 0),      # 6 AM (next day)
    is_active=True
)
```

The `is_currently_active` logic automatically handles this:
```
if start_time < end_time:
    # Normal case: 09:30 → 14:00
    check: start <= now <= end
else:
    # Overnight case: 22:00 → 06:00
    check: now >= start OR now <= end
```

---

## Admin Interface

**Location:** `/admin/core/storeshift/`

**List View Shows:**
- Shift name
- Time range (e.g., "09:30 – 14:00")
- Is Active status (✓/⊗)
- Currently Running? (🟢 RUNNING NOW / ⊗ Not Running)
- Last updated

**Editable Columns:**
- `is_active` — Toggle shift availability

**Detail View Shows:**
- All shift details
- Real-time "RUNNING NOW" indicator
- Timestamps (created/updated)

---

## Migration Info

**Migration File:** `core/migrations/0005_storeshift.py`
**Table Name:** `core_storeshift`

---

## Related Models

- **StoreStatus:** Manual on/off override (is_open boolean)
- **Order:** Uses `StoreShift.is_open_now()` for validation
- **Delivery:** May reference current shift for scheduling

---

## Future Enhancements

1. **Shift-specific breaks:** Add break times within shifts
2. **Shift capacity:** Track max orders per shift
3. **Staff scheduling:** Link employees to specific shifts
4. **Delivery shifts:** Separate delivery operating hours
5. **Dynamic availability:** Different shifts on different days of week

---

## Database State (After Setup)

```
Morning   | 09:30:00 | 14:00:00 | Active ✓
Evening   | 18:00:00 | 22:00:00 | Active ✓
```

Both shifts are ready to use. Staff can toggle `is_active` in admin to close individual shifts without deleting them.
