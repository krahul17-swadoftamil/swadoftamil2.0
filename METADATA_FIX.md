# Order Submission Fix - FieldError 'metadata' - RESOLVED ✅

## 🎯 The Problem

```
FieldError at /api/orders/
Cannot resolve keyword 'metadata' into field.
```

The Order model was missing the `metadata` field needed to store idempotency keys for duplicate prevention.

---

## ✅ What Was Fixed

### 1️⃣ Added `metadata` Field to Order Model

**File**: `backend/orders/models.py` (Lines 110-120)

```python
# =============================
# METADATA
# =============================
metadata = models.JSONField(
    default=dict,
    blank=True,
    null=False,
    help_text="Store idempotency key and other request metadata"
)
```

### 2️⃣ Created Database Migration

```bash
# Migration Created: 0012_order_metadata_orderevent
# Applied: OK ✓
```

### 3️⃣ Updated Order Creation Flow

**Files Modified**:
- `backend/orders/services.py` - Accept metadata in payload
- `backend/orders/serializers.py` - Pass metadata to service
- `backend/orders/views.py` - Extract idempotency key and pass as metadata

---

## 📋 Implementation Details

### Step 1: Order Model (`models.py`)

Added JSONField to store metadata:

```python
metadata = models.JSONField(
    default=dict,
    blank=True,
    null=False,
    help_text="Store idempotency key and other request metadata"
)
```

### Step 2: Services (`services.py`)

Updated `create_order_from_payload` to accept and store metadata:

```python
def create_order_from_payload(payload: dict) -> Order:
    # ... existing code ...
    metadata = payload.get("metadata") or {}
    
    order = Order.objects.create(
        status=Order.STATUS_PENDING,
        total_amount=total_amount,
        payment_method=payment_method,
        customer_name=customer_payload.get("name", ""),
        customer_phone=customer_payload.get("phone", ""),
        customer_email=customer_payload.get("email", ""),
        customer_address=customer_payload.get("address", ""),
        metadata=metadata,  # ← ADD THIS
    )
```

### Step 3: Serializer (`serializers.py`)

Added metadata field and pass to service:

```python
class OrderCreateSerializer(serializers.Serializer):
    combos = serializers.ListField(required=False)
    snacks = serializers.ListField(required=False)
    customer = serializers.DictField(required=False)
    payment_method = serializers.CharField(default="cod")
    metadata = serializers.DictField(required=False, default=dict)  # ← ADD THIS

    # ... validation code ...

    def create(self, validated_data):
        payload = {
            "combos": validated_data.get("combos", []),
            "snacks": validated_data.get("snacks", []),
            "payment_method": validated_data.get("payment_method"),
            "metadata": validated_data.get("metadata", {}),  # ← ADD THIS
        }
        # ... rest of create ...
```

### Step 4: Views (`views.py`)

Extract idempotency key and check for duplicates:

```python
@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    # ✔ IDEMPOTENCY CHECK
    idempotency_key = request.headers.get("X-Idempotency-Key")
    if idempotency_key:
        # Check if we've already created an order with this key
        existing = Order.objects.filter(
            metadata__idempotency_key=idempotency_key
        ).first()
        if existing:
            return Response(
                OrderReadSerializer(existing).data,
                status=status.HTTP_200_OK
            )

    # ✔ Prepare request data with idempotency key in metadata
    request_data = dict(request.data)
    request_data["metadata"] = {
        "idempotency_key": idempotency_key
    } if idempotency_key else {}

    serializer = OrderCreateSerializer(data=request_data)
    serializer.is_valid(raise_exception=True)

    order = serializer.save()

    return Response(
        OrderReadSerializer(order).data,
        status=status.HTTP_201_CREATED
    )
```

---

## ✅ How It Works

### Request Flow

```
1. Frontend sends POST /api/orders/ with:
   - X-Idempotency-Key: abc-123-def
   - Body: { combos: [...], snacks: [...], customer: {...} }

2. Django view extracts header:
   - idempotency_key = "abc-123-def"

3. Check for duplicates:
   - Order.objects.filter(metadata__idempotency_key="abc-123-def")
   - If found: return existing order (status 200)

4. Create new order:
   - Pass metadata with idempotency_key to serializer
   - Serializer passes to service
   - Service creates Order with metadata

5. Order saved with:
   {
       id: "...",
       metadata: {
           "idempotency_key": "abc-123-def"
       },
       ...
   }

6. Return order (status 201)
```

### Database Query

```python
# Check for duplicate
Order.objects.filter(metadata__idempotency_key="abc-123-def")

# Works because JSONField supports key lookups in Django
# Translates to SQL: WHERE metadata->>'idempotency_key' = 'abc-123-def'
```

---

## ✅ Duplicate Prevention

### Before (Without metadata)

```
Request 1: POST /api/orders/ (no idempotency) → Order created
Request 1 (retry): POST /api/orders/ → Another order created ❌ DUPLICATE
```

### After (With metadata & idempotency)

```
Request 1: POST /api/orders/ (X-Idempotency-Key: abc-123)
  → Check metadata__idempotency_key = "abc-123" → Not found
  → Create order with metadata.idempotency_key = "abc-123"
  → Return 201 Created

Request 1 (retry): POST /api/orders/ (same X-Idempotency-Key: abc-123)
  → Check metadata__idempotency_key = "abc-123" → FOUND ✓
  → Return existing order with 200 OK
  → NO DUPLICATE ✓
```

---

## 📊 Database Schema

### Order Model (Updated)

```python
class Order(models.Model):
    id = UUIDField(primary_key=True)
    status = CharField(choices=STATUS_CHOICES)
    total_amount = DecimalField()
    payment_method = CharField()
    customer_name = CharField()
    customer_phone = CharField()
    customer_email = EmailField()
    customer_address = TextField()
    customer = ForeignKey('Customer')
    
    # ← NEW FIELD
    metadata = JSONField(default=dict)
    
    created_at = DateTimeField(auto_now_add=True)
    order_number = CharField(unique=True)
    code = CharField(unique=True)
```

### Migration Applied

```
0012_order_metadata_orderevent.py
  - Added field metadata to order ✓
  - Created model OrderEvent
```

---

## ✅ Testing Checkout

### Step 1: Add Items to Cart
- Click items to add to cart

### Step 2: Open Checkout
- Click "Checkout" button

### Step 3: Fill Order Details
- Enter phone number
- Enter name (optional)
- Enter address (optional)

### Step 4: Place Order
- Click "Place Order"
- **Should now succeed** ✓

### Step 5: Verify No Duplicate
- Try placing same order again
- Should get existing order, not create new one ✓

---

## 🔍 Verification

### Check Migration Applied
```bash
cd backend
python manage.py showmigrations orders
# Should show: [X] 0012_order_metadata_orderevent
```

### Check Field Exists
```bash
python manage.py dbshell
SELECT * FROM orders_order LIMIT 1;
# Should show 'metadata' column as JSON
```

### Test Idempotency
```bash
# Request 1
curl -X POST http://localhost:8000/api/orders/ \
  -H "X-Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{"combos":[],"snacks":[],"customer":{"phone":"9876543210"}}'
# Returns: 201 Created + Order

# Request 2 (same key)
curl -X POST http://localhost:8000/api/orders/ \
  -H "X-Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{"combos":[],"snacks":[],"customer":{"phone":"9876543210"}}'
# Returns: 200 OK + SAME Order (no duplicate)
```

---

## ✅ No Breaking Changes

- ✅ Frontend needs NO changes
- ✅ Existing orders not affected (metadata defaults to `{}`)
- ✅ CORS headers still work
- ✅ All endpoints functional

---

## 📋 Files Modified

| File | Change | Lines |
|------|--------|-------|
| `backend/orders/models.py` | Added `metadata` JSONField | 110-120 |
| `backend/orders/services.py` | Accept & store metadata | 26, 105 |
| `backend/orders/serializers.py` | Add metadata field + pass to service | 127, 248-251 |
| `backend/orders/views.py` | Extract idempotency key + check duplicates | 62-93 |
| `backend/orders/migrations/0012_*` | Migration for metadata field | Created ✓ |

---

## 🚀 Status

✅ **Migration**: Applied  
✅ **Model**: Updated  
✅ **Views**: Fixed  
✅ **Serializers**: Fixed  
✅ **Services**: Fixed  
✅ **Testing**: Ready  
✅ **Duplicate Prevention**: Active  

**Ready to place orders!** 🎉

---

**Date**: January 3, 2026  
**Django Version**: 6.0  
**Python Version**: 3.12.7
