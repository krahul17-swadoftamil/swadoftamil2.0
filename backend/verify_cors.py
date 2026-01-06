#!/usr/bin/env python
"""
Verify CORS configuration for x-idempotency-key header.
Run this after restarting Django.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings

print("\n" + "="*70)
print("CORS CONFIGURATION VERIFICATION")
print("="*70)

# Check CORS middleware
middleware_list = settings.MIDDLEWARE
cors_middleware_installed = any('CorsMiddleware' in m for m in middleware_list)

print(f"\n✓ CORS Middleware Installed: {cors_middleware_installed}")
print(f"  Position: {[i for i, m in enumerate(middleware_list) if 'CorsMiddleware' in m]}")

# Check CORS settings
print(f"\n✓ CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
print(f"✓ CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")

# Check custom header
cors_headers = getattr(settings, 'CORS_ALLOW_HEADERS', [])
idempotency_allowed = 'x-idempotency-key' in [h.lower() for h in cors_headers]

print(f"\n✓ CORS_ALLOW_HEADERS configured: {bool(cors_headers)}")
print(f"✓ x-idempotency-key allowed: {idempotency_allowed}")

if cors_headers:
    print(f"\n  Headers allowed:")
    for h in sorted(cors_headers):
        print(f"    - {h}")

# Check allowed origins
allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
print(f"\n✓ CORS_ALLOWED_ORIGINS: {allowed_origins if allowed_origins else '(DEBUG=True, all origins allowed)'}")

print("\n" + "="*70)
if cors_middleware_installed and idempotency_allowed:
    print("✅ CORS configuration is CORRECT")
    print("\nYou can now:")
    print("  - POST to /api/orders/ with x-idempotency-key header")
    print("  - POST to /api/orders/cart/ with custom headers")
    print("  - Make requests from http://localhost:5173")
else:
    print("❌ CORS configuration is INCOMPLETE")

print("="*70 + "\n")
