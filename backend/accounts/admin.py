from django.contrib import admin
from django.utils.html import format_html

from .models import Customer, OTP, SMSSetting, Employee


# ======================================================
# CUSTOMER ADMIN
# ======================================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Customer lifecycle & LTV view.
    Phone-first identity.
    """

    list_display = (
        "code",
        "phone",
        "name",
        "email",
        "status_badge",
        "total_orders",
        "created_at",
    )

    list_filter = ("is_active",)
    search_fields = ("phone", "name", "email", "code")
    ordering = ("-created_at",)

    readonly_fields = (
        "uuid",
        "code",
        "created_at",
        "updated_at",
        "first_order_at",
        "last_order_at",
        "total_orders",
    )

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "phone",
                    "name",
                    "email",
                    "is_active",
                    "code",
                )
            },
        ),
        (
            "Order Metrics",
            {
                "fields": (
                    "total_orders",
                    "first_order_at",
                    "last_order_at",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#2e7d32;font-weight:600;">ACTIVE</span>'
            )
        return format_html(
            '<span style="color:#c62828;font-weight:600;">INACTIVE</span>'
        )


# ======================================================
# OTP ADMIN (AUDIT ONLY)
# ======================================================
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    OTP audit-only admin.
    Security critical.
    """

    list_display = (
        "phone",
        "code",
        "is_used",
        "expires_at",
        "created_at",
    )

    list_filter = ("is_used",)
    search_fields = ("phone", "code")
    ordering = ("-created_at",)

    readonly_fields = (
        "phone",
        "code",
        "is_used",
        "used_at",
        "expires_at",
        "created_at",
    )

    def has_add_permission(self, request):
        # OTPs must be system-generated only
        return False

    def has_change_permission(self, request, obj=None):
        # Strictly read-only (even superusers)
        return False

    def has_delete_permission(self, request, obj=None):
        # Optional cleanup allowed ONLY for superusers
        return bool(request.user and request.user.is_superuser)


# ======================================================
# SMS SETTING ADMIN (SINGLETON)
# ======================================================
@admin.register(SMSSetting)
class SMSSettingAdmin(admin.ModelAdmin):
    """
    Singleton toggle for OTP debug behavior.
    """

    list_display = ("id", "allow_plaintext_otp")
    list_display_links = ("id",)
    list_editable = ("allow_plaintext_otp",)

    def has_add_permission(self, request):
        # Only one row allowed
        return not SMSSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ======================================================
# EMPLOYEE ADMIN
# ======================================================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Staff / operator management.
    ERP-safe.
    """

    list_display = (
        "code",
        "name",
        "role",
        "designation",
        "phone",
        "email",
        "is_active",
        "created_at",
    )

    list_filter = ("role", "designation", "is_active")
    search_fields = ("name", "phone", "code", "user__username")
    ordering = ("-created_at",)

    readonly_fields = (
        "uuid",
        "code",
        "created_at",
        "updated_at",
        "user",
    )

    fieldsets = (
        (
            "Employee",
            {
                "fields": (
                    "name",
                    "code",
                    "role",
                    "designation",
                    "user",
                    "phone",
                    "email",
                    "is_active",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "uuid",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
