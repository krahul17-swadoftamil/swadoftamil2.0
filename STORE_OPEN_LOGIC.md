# Store Open Logic — Single Source of Truth

## Overview
Two authoritative functions for determining if the store is open:

1. **`is_store_open()`** — Simple boolean answer
2. **`get_store_status()`** — Complete status dictionary

**Location:** `backend/core/utils.py`

---

## `is_store_open()` Function

### Purpose
**SINGLE SOURCE OF TRUTH** for "Can the store accept orders right now?"

This is the ONLY function frontend, API, and order logic should trust.

### Logic
```python
def is_store_open() -> bool:
    # 1. Master switch must be ENABLED
    if not StoreStatus.is_enabled:
        return False
    
    # 2. At least one shift must be ACTIVE
    if not StoreShift.is_open_now():
        return False
    
    # Both conditions met = store is open
    return True
```

### Usage Examples

#### Order Validation
```python
from core.utils import is_store_open

def create_order(items):
    if not is_store_open():
        raise ValidationError("Store is currently closed")
    
    # Proceed with order creation
    order = Order.objects.create(...)
```

#### API Endpoint
```python
from core.utils import is_store_open

@api_view(['GET'])
def check_store_status(request):
    return Response({
        'store_open': is_store_open()
    })
```

#### Frontend Polling
```javascript
// Poll every 30 seconds
setInterval(async () => {
    const response = await fetch('/api/store/open');
    const data = await response.json();
    
    if (data.store_open) {
        showOrderButton();
    } else {
        hideOrderButton();
        showClosedMessage();
    }
}, 30000);
```

---

## `get_store_status()` Function

### Purpose
Get complete store status information for detailed UI/API responses.

### Returns
```python
{
    'is_open': bool,           # Can accept orders? (same as is_store_open())
    'master_switch': bool,     # StoreStatus.is_enabled
    'shifts_active': bool,     # StoreShift.is_open_now()
    'current_shift': str|None, # Name of active shift or None
    'message': str|None,       # StoreStatus.note (customer message)
}
```

### Usage Examples

#### Complete API Response
```python
from core.utils import get_store_status

@api_view(['GET'])
def store_status(request):
    status = get_store_status()
    return Response(status)
```

**Response:**
```json
{
  "is_open": false,
  "master_switch": true,
  "shifts_active": false,
  "current_shift": null,
  "message": "Closed for festival"
}
```

#### Admin Dashboard
```python
status = get_store_status()

if status['is_open']:
    print(f"🟢 Store OPEN - Running {status['current_shift']} shift")
else:
    if not status['master_switch']:
        print(f"🔴 EMERGENCY CLOSED: {status['message']}")
    else:
        print("🟡 CLOSED - Outside operating hours")
```

#### Kitchen Display
```python
status = get_store_status()

if status['current_shift']:
    print(f"Current shift: {status['current_shift']}")
    print("Orders expected: YES")
else:
    print("No active shift")
    print("Orders expected: NO")
```

---

## Decision Matrix

| Master Switch | Shifts Active | is_open | Scenario |
|---------------|---------------|---------|----------|
| ✅ ON | ✅ Active | 🟢 True | Normal operation |
| ❌ OFF | ✅ Active | 🔴 False | Emergency closed |
| ✅ ON | ❌ None | 🔴 False | Outside hours |
| ❌ OFF | ❌ None | 🔴 False | Double closed |

---

## Error Handling

### StoreStatus Missing
If no StoreStatus exists in database:
- `is_store_open()` → `False` (safe default)
- `get_store_status()` → `master_switch: False, message: "Store status not configured"`

### StoreShift Issues
- Handles overnight shifts correctly
- Returns `None` for `current_shift` when no shift active
- Gracefully handles database errors

---

## Performance

### Caching Strategy
```python
# Optional: Cache for 30 seconds
from django.core.cache import cache

def is_store_open_cached():
    key = 'store_open_status'
    result = cache.get(key)
    if result is None:
        result = is_store_open()
        cache.set(key, result, 30)  # 30 second cache
    return result
```

### Database Queries
- `is_store_open()`: 2 queries (StoreStatus + StoreShift check)
- `get_store_status()`: 2 queries (same as above)
- Consider caching for high-traffic scenarios

---

## Integration Points

### Order Creation
```python
# orders/views.py
from core.utils import is_store_open

class OrderCreateView(APIView):
    def post(self, request):
        if not is_store_open():
            return Response(
                {'error': 'Store is currently closed'},
                status=400
            )
        # Create order...
```

### Frontend Components
```javascript
// React component
import { useStoreStatus } from './api';

function OrderButton() {
    const { is_open, message } = useStoreStatus();
    
    if (!is_open) {
        return <div className="closed">Store Closed: {message}</div>;
    }
    
    return <button>Place Order</button>;
}
```

### WebSocket Updates
```python
# Send real-time updates
from channels.layers import get_channel_layer

def broadcast_store_status():
    status = get_store_status()
    channel_layer = get_channel_layer()
    channel_layer.group_send(
        'store_status',
        {'type': 'status_update', 'data': status}
    )
```

---

## Testing

### Unit Tests
```python
from core.utils import is_store_open, get_store_status

def test_store_closed_emergency():
    # Turn off master switch
    StoreStatus.objects.update(is_enabled=False)
    
    assert is_store_open() == False
    status = get_store_status()
    assert status['is_open'] == False
    assert status['master_switch'] == False

def test_store_open_normal():
    # Enable master switch, activate a shift
    StoreStatus.objects.update(is_enabled=True)
    StoreShift.objects.update(is_active=True)
    
    # Mock current time to be within shift
    # ... time mocking logic ...
    
    assert is_store_open() == True
```

### Integration Tests
```python
def test_order_creation_respects_store_status():
    # Close store
    StoreStatus.objects.update(is_enabled=False)
    
    # Attempt order creation
    response = client.post('/api/orders/', order_data)
    assert response.status_code == 400
    assert 'closed' in response.data['error'].lower()
```

---

## Migration Guide

### Before (Scattered Logic)
```python
# ❌ DON'T DO THIS
def can_place_order():
    status = StoreStatus.objects.get()
    shifts = StoreShift.objects.filter(is_active=True)
    now = timezone.now().time()
    # Complex logic duplicated everywhere...
```

### After (Single Source)
```python
# ✅ DO THIS
from core.utils import is_store_open

def can_place_order():
    return is_store_open()
```

---

## Files Modified

- ✅ `backend/core/utils.py` — Added `is_store_open()` and `get_store_status()`
- ✅ `backend/core/models.py` — Removed duplicate functions

---

## Next Steps

1. **API Endpoint:** Create `/api/store/status/` using `get_store_status()`
2. **Order Integration:** Add `is_store_open()` check to Order model
3. **Frontend:** Update UI to use the new status functions
4. **WebSocket:** Real-time status updates for live UI
5. **Caching:** Add Redis caching for high-traffic scenarios
