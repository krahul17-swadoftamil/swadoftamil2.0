import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


# ======================================================
# CUSTOMER (END USER / BUYER)
# ======================================================
class Customer(models.Model):
    """
    Customer = end user who places food orders.

    DESIGN PRINCIPLES:
    ✔ Phone-first identity (OTP-based)
    ✔ No passwords, no auth.User dependency
    ✔ Lightweight but analytics-ready
    ✔ Immutable identity (phone)
    """

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Human-friendly reference code (CUST-XXXX)
    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    # Identity
    phone = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        help_text="Primary identifier (OTP based login)",
    )

    name = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional. Asked on first successful order."
    )

    email = models.EmailField(
        blank=True,
        help_text="Optional. For receipts / future communication."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Soft disable customer if needed"
    )

    # ================= ORDER METRICS =================
    first_order_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of first successful order"
    )

    last_order_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of most recent order"
    )

    total_orders = models.PositiveIntegerField(
        default=0,
        help_text="Total completed orders"
    )

    # ================= META =================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name or self.phone}"

    # ================= BUSINESS HELPERS =================
    @property
    def is_first_time_customer(self):
        return self.total_orders == 0

    def mark_order_placed(self):
        """
        Call this after a successful paid order.
        """
        now = timezone.now()

        if not self.first_order_at:
            self.first_order_at = now

        self.last_order_at = now
        self.total_orders = models.F("total_orders") + 1

        self.save(update_fields=[
            "first_order_at",
            "last_order_at",
            "total_orders",
        ])

    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not self.code:
            for _ in range(3):
                try:
                    generate_and_set_code(self, prefix="CUST", field="code", digits=4)
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)


# ======================================================
# OTP (TEMPORARY AUTH RECORD)
# ======================================================
class OTP(models.Model):
    """
    OTP = short-lived authentication record.

    RULES:
    ✔ Phone scoped
    ✔ One-time use
    ✔ Time-bound
    ✔ No business logic
    """

    phone = models.CharField(
        max_length=15,
        db_index=True
    )

    code = models.CharField(
        max_length=6,
        help_text="6-digit numeric OTP"
    )

    is_used = models.BooleanField(
        default=False
    )

    expires_at = models.DateTimeField(
        help_text="OTP expiry timestamp"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"OTP({self.phone})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


# ======================================================
# SMS SETTING (ADMIN TOGGLE)
# ======================================================
class SMSSetting(models.Model):
    """
    Simple singleton-style model to allow admins to toggle whether
    plaintext OTPs may be returned in API responses for testing.
    """

    allow_plaintext_otp = models.BooleanField(default=False)

    def __str__(self):
        return f"SMSSetting(allow_plaintext_otp={self.allow_plaintext_otp})"


# ======================================================
# EMPLOYEE (STAFF / OPERATOR)
# ======================================================
class Employee(models.Model):
    """
    Employee profile for staff members.
    Fields are intentionally compatible with the migration history.
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("kitchen", "Kitchen"),
        ("delivery", "Delivery"),
        ("other", "Other"),
    ]

    DESIGNATION_CHOICES = [
        ("chef", "Chef"),
        ("dosa_chef", "Dosa Chef"),
        ("cleaner", "Cleaner"),
        ("accountant", "Accountant"),
        ("helper", "Helper"),
        ("rider", "Rider"),
        ("cashier", "Cashier"),
    ]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    designation = models.CharField(max_length=32, choices=DESIGNATION_CHOICES)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="other")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="employee_profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code or self.phone})"

    def save(self, *args, **kwargs):
        from core.utils import generate_and_set_code

        if not self.code:
            for _ in range(3):
                try:
                    generate_and_set_code(self, prefix="EMP", field="code", digits=4)
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)
