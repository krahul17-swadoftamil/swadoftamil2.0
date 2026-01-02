from django.contrib import admin
from .models import Customer, OTP, SMSSetting
from .models import Employee


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "phone",
        "name",
        "email",
        "is_active",
        "created_at",
        "total_orders",
    )

    list_filter = ("is_active",)
    search_fields = ("phone", "name", "email")
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at", "updated_at", "code", "first_order_at", "last_order_at", "total_orders")

    fieldsets = (
        (
            "Customer",
            {"fields": ("phone", "name", "code", "email", "is_active")},
        ),
        (
            "Orders",
            {"fields": ("total_orders", "first_order_at", "last_order_at")},
        ),
        (
            "System",
            {"fields": ("uuid", "created_at", "updated_at")},
        ),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "is_used", "created_at")
    list_filter = ("is_used",)
    search_fields = ("phone", "code")
    ordering = ("-created_at",)
    readonly_fields = ("phone", "code", "is_used", "created_at")

    def has_add_permission(self, request):
        # Allow superusers to add OTP entries (rare), block regular staff
        return bool(request.user and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        # Allow superusers to change OTP records; block regular staff
        return bool(request.user and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(SMSSetting)
class SMSSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "allow_plaintext_otp")
    list_display_links = ("id",)
    list_editable = ("allow_plaintext_otp",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "role", "designation", "phone", "email", "is_active", "created_at")
    list_filter = ("role", "designation", "is_active")
    search_fields = ("name", "phone", "code", "user__username")
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at", "updated_at", "code", "user")

    fieldsets = (
        ("Employee", {"fields": ("name", "code", "role", "designation", "user", "phone", "email", "is_active")} ),
        ("System", {"fields": ("uuid", "created_at", "updated_at")} ),
    )


