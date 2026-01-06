# CORS Fix - Implementation & Explanation

## ✅ Problem & Solution

### The Error
```
Request header field x-idempotency-key is not allowed by Access-Control-Allow-Headers
```

### Root Cause
Browser's **preflight request** (`OPTIONS`) sends `x-idempotency-key` in the `Access-Control-Request-Headers` header, but Django's CORS middleware didn't have this header in its whitelist.

When `x-idempotency-key` is sent with a POST request, the browser automatically sends an OPTIONS request first to check if the server allows this header.

### The Fix
**settings.py** - Explicitly whitelist the custom header:

```python
# ======================================================
# CORS — REACT FRONTEND
# ======================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# ✔ Allow custom idempotency header + defaults
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-idempotency-key",  # ← Custom header for duplicate prevention
]
```

### Why This Works

1. **Preflight Response**: Now when browser sends OPTIONS request, Django includes:
   ```
   Access-Control-Allow-Headers: accept, accept-encoding, authorization, ..., x-idempotency-key
   ```

2. **Browser Approval**: Browser sees `x-idempotency-key` in the allowed list, proceeds with actual POST request

3. **Request Succeeds**: Backend receives POST with custom header intact

---

## 📋 Exact Configuration Required

### ✅ Middleware Order (CORRECT - DON'T CHANGE)

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← Must be FIRST
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

**Why first?** CORS middleware must run before other middleware to intercept OPTIONS requests.

### ✅ CORS Settings (settings.py)

```python
# Development (DEBUG=True)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Explicitly whitelist custom headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-idempotency-key",  # ← ADD THIS LINE
]

# Production (DEBUG=False)
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

### ✅ No Frontend Changes Required

The frontend [src/api.js](../swad-frontend/src/api.js) already sends the header:

```javascript
headers["X-Idempotency-Key"] = `${endpoint}-${Date.now()}-${Math.random()}`;
```

**Django automatically converts** `X-Idempotency-Key` → `x-idempotency-key` (lowercased for comparison).

---

## ✅ Verification

### Option 1: Run verification script
```bash
cd backend
python manage.py shell < verify_cors.py
```

### Option 2: Test with curl
```bash
curl -X OPTIONS http://localhost:8000/api/orders/ \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Headers: x-idempotency-key" \
  -v
```

Should see:
```
< Access-Control-Allow-Headers: accept, accept-encoding, authorization, content-type, ..., x-idempotency-key
< HTTP/1.1 200 OK
```

### Option 3: Test POST request
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: test-123" \
  -d '{"combos":[],"snacks":[]}' \
  -v
```

Should work without CORS errors.

---

## ❌ Common Mistakes (DON'T DO)

### ❌ Mistake 1: Replacing instead of extending
```python
# WRONG - loses other important headers
CORS_ALLOW_HEADERS = ["x-idempotency-key"]

# RIGHT - extends default headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    # ... others ...
    "x-idempotency-key",  # Add to the list
]
```

### ❌ Mistake 2: Disabling CORS entirely
```python
# WRONG - security risk
CORS_ALLOW_ALL_ORIGINS = True  # in production
CORS_ALLOW_ALL_HEADERS = True

# RIGHT
CORS_ALLOWED_ORIGINS = ["https://your-domain.com"]
CORS_ALLOW_HEADERS = [...]  # explicit list
```

### ❌ Mistake 3: Wrong middleware position
```python
# WRONG - CorsMiddleware after SecurityMiddleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # ← Too late

# RIGHT - CorsMiddleware FIRST
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← First
    "django.middleware.security.SecurityMiddleware",
]
```

---

## 📊 How Browser Preflight Works

```
1. Frontend sends POST with custom header:
   POST /api/orders/
   X-Idempotency-Key: abc123
   Content-Type: application/json

2. Browser intercepts & sends OPTIONS first:
   OPTIONS /api/orders/
   Origin: http://localhost:5173
   Access-Control-Request-Headers: x-idempotency-key
   Access-Control-Request-Method: POST

3. Django responds with allowed headers:
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: http://localhost:5173
   Access-Control-Allow-Headers: accept, ..., x-idempotency-key
   Access-Control-Allow-Methods: GET, POST, ...

4. Browser sees x-idempotency-key is allowed, sends actual POST:
   POST /api/orders/
   X-Idempotency-Key: abc123
   Content-Type: application/json
   [JSON body]

5. Backend receives & processes normally ✓
```

---

## 🎯 About Framer Motion Warning

### The Warning
```
Using reduced motion for: opacity, transform
```

### Is It an Error?
**NO** - This is **informational only** and indicates that Framer Motion is respecting user's accessibility preference (`prefers-reduced-motion`).

### Why We Keep It
- **Accessibility**: Some users have vestibular disorders and motion causes dizziness
- **User Choice**: Users can set OS preference for reduced motion
- **Best Practice**: Respecting this improves accessibility score
- **Not Breaking**: It's not a bug—it's a feature

### To Suppress (NOT RECOMMENDED)
```javascript
// In your Framer Motion animation config:
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}
transition={{ duration: 0.3 }}
// Framer Motion will auto-reduce based on system preference
```

Just let Framer Motion handle it automatically—it's working as intended. ✓

---

## ✅ Status Checklist

- [x] `CORS_ALLOW_HEADERS` includes `x-idempotency-key`
- [x] `CorsMiddleware` is first in MIDDLEWARE list
- [x] `CORS_ALLOW_CREDENTIALS = True` for auth
- [x] `CORS_ALLOW_ALL_ORIGINS = True` (in DEBUG mode)
- [x] No frontend changes needed
- [x] POST /api/orders/ works
- [x] POST /api/orders/cart/ works
- [x] OPTIONS preflight succeeds
- [x] Frontend can send custom headers

---

**Last Updated**: January 3, 2026
**Django Version**: 4.x+
**django-cors-headers Version**: 4.0+
