import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.utils import timezone


# ======================================================
# CUSTOMER (END USER / BUYER)
# ======================================================
class Customer(models.Model):
    """
    Phone-first customer.
    OTP based authentication.
    Linked to Django User ONLY for session handling.
    """

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Public readable code (CUST0001 etc)
    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        editable=False,
        null=True,
        blank=True,
    )

    # PRIMARY LOGIN IDENTIFIER
    phone = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        help_text="Primary identifier (OTP login)",
    )

    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)

    # ================= GOOGLE AUTH =================
    google_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Google OAuth user ID",
    )

    google_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email returned by Google OAuth",
    )

    auth_provider = models.CharField(
        max_length=20,
        choices=[
            ("phone", "Phone OTP"),
            ("google", "Google OAuth"),
        ],
        default="phone",
        help_text="Authentication method used",
    )

    # 🔥 CRITICAL — SESSION AUTH LINK
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="customer_profile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Linked Django user for session auth",
    )

    is_active = models.BooleanField(default=True)

    # ================= ORDER METRICS =================
    first_order_at = models.DateTimeField(null=True, blank=True)
    last_order_at = models.DateTimeField(null=True, blank=True)
    total_orders = models.PositiveIntegerField(default=0)

    # ================= CUSTOMER PREFERENCES =================
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Customer preferences stored as JSON (e.g., dietary restrictions, favorite items)",
    )

    # ================= META =================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name or self.phone

    # ---------------- BUSINESS ----------------
    @property
    def is_first_time_customer(self):
        return self.total_orders == 0

    def mark_order_placed(self):
        """
        Atomic order update (safe for concurrent requests)
        """
        now = timezone.now()

        updates = {
            "last_order_at": now,
            "total_orders": F("total_orders") + 1,
        }

        if not self.first_order_at:
            updates["first_order_at"] = now

        Customer.objects.filter(pk=self.pk).update(**updates)

    def link_google_account(self, google_id, google_email, name=None):
        """
        Link Google account to this customer.
        Used for auto-linking when email matches.
        """
        if self.google_id and self.google_id != google_id:
            raise ValueError("Customer already linked to different Google account")

        self.google_id = google_id
        self.google_email = google_email
        self.auth_provider = "google"

        if name and not self.name:
            self.name = name

        self.save(update_fields=["google_id", "google_email", "auth_provider", "name"])

    def get_personalization_data(self):
        """
        Get customer data useful for personalization.
        """
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'preferences': self.preferences or {},
            'total_orders': self.total_orders,
            'first_order_at': self.first_order_at,
            'last_order_at': self.last_order_at,
            'is_first_time_customer': self.total_orders == 0,
        }

    def save(self, *args, **kwargs):
        """
        Auto-generate public customer code once.
        """
        from core.utils import generate_and_set_code

        if not self.code:
            for _ in range(3):
                try:
                    generate_and_set_code(
                        self,
                        prefix="CUST",
                        field="code",
                        digits=4,
                    )
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)


# ======================================================
# OTP (TEMPORARY AUTH RECORD)
# ======================================================
class OTP(models.Model):
    """
    Short-lived OTP record.
    Used ONLY for verification.
    """

    phone = models.CharField(max_length=15, db_index=True)

    code = models.CharField(
        max_length=6,
        help_text="Numeric OTP",
    )

    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField()
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

    def mark_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])


# ======================================================
# SMS SETTING (SINGLETON)
# ======================================================
class SMSSetting(models.Model):
    """
    Admin toggle for OTP debug/testing behavior.
    Only ONE row allowed.
    """

    allow_plaintext_otp = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and SMSSetting.objects.exists():
            raise ValidationError("Only one SMSSetting instance allowed.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"SMSSetting(plaintext={self.allow_plaintext_otp})"


# ======================================================
# EMPLOYEE (STAFF / OPERATOR)
# ======================================================
class Employee(models.Model):
    """
    Staff profile.
    Can optionally link to Django User.
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

    designation = models.CharField(
        max_length=32,
        choices=DESIGNATION_CHOICES,
    )

    role = models.CharField(
        max_length=32,
        choices=ROLE_CHOICES,
        default="other",
    )

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
                    generate_and_set_code(
                        self,
                        prefix="EMP",
                        field="code",
                        digits=4,
                    )
                    break
                except Exception:
                    continue

        super().save(*args, **kwargs)
