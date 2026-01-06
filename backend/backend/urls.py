from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

from analytics.views import download_report

"""
Root URL Configuration — Swad of Tamil

API-first backend powering:
• React + Vite frontend
• Kitchen & POS
• ERP & ingredient discipline
"""

# ======================================================
# SERVICE STATUS
# ======================================================

def api_status(request):
    """Lightweight service availability endpoint"""
    return JsonResponse({"status": "open"})


# ======================================================
# URL PATTERNS
# ======================================================

urlpatterns = [

    # ------------------------------
    # ROOT
    # ------------------------------
    path("", lambda request: JsonResponse({"message": "Welcome to Swad of Tamil API", "admin": "/admin/", "api": "/api/"})),

    # ------------------------------
    # HEALTH / STATUS
    # ------------------------------
    path("api/status/", api_status),

    # ------------------------------
    # DJANGO REST AUTH
    # ------------------------------
    path("auth/", include("dj_rest_auth.urls")),

    # ------------------------------
    path("admin/", admin.site.urls),

    # Admin-protected analytics download
    re_path(
        r"^admin/analytics/download/(?P<filename>[^/]+)$",
        admin.site.admin_view(download_report),
        name="admin_download_report",
    ),

    # ------------------------------
    # API ROOT
    # ------------------------------
    path(
        "api/",
        include([

            # AUTH / ACCOUNTS
            path("auth/", include("accounts.urls")),
            path("customers/", include("accounts.customer_urls")),

            # ERP / INGREDIENTS
            path("ingredients/", include("ingredients.urls")),

            # MENU (COMBOS, PREPARED ITEMS)
            path("menu/", include("menu.urls")),

            # ORDERS & CHECKOUT
            path("orders/", include("orders.urls")),

            # SNACKS (PACKED / RETAIL)
            path("snacks/", include("snacks.urls")),

            # SYSTEM / INTERNAL
            path("system/", include("core.urls")),
        ]),
    ),
]

# ======================================================
# MEDIA FILES (DEVELOPMENT ONLY)
# ======================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
