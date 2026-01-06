from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from .models import Customer, Employee

User = get_user_model()


# ======================================================
# CUSTOMER SIGNALS (OTP-FIRST — NO DJANGO USER)
# ======================================================

@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    """
    IMPORTANT:
    - Customers are OTP-authenticated ONLY
    - DO NOT auto-create Django User
    - DO NOT send passwords
    - DO NOT touch auth/session

    This signal is intentionally minimal.
    """
    return  # Explicit no-op (future safe)


# ======================================================
# EMPLOYEE → DJANGO USER (ADMIN / STAFF ONLY)
# ======================================================

@receiver(post_save, sender=Employee)
def ensure_employee_user(sender, instance, created, **kwargs):
    """
    Auto-create Django User for Employees ONLY.

    ✔ Safe
    ✔ Idempotent
    ✔ No effect on customers
    """

    # Already linked → do nothing
    if instance.user:
        return

    UserModel = User

    # Username derivation (stable & collision-safe)
    if instance.email:
        base = instance.email.split("@")[0]
    elif instance.code:
        base = instance.code.lower()
    else:
        base = (instance.name or "employee").replace(" ", "").lower()

    username = base
    suffix = 0
    while UserModel.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"

    # Generate password
    password = get_random_string(10)

    # Create user
    user = UserModel.objects.create_user(
        username=username,
        email=instance.email or "",
        password=password,
    )

    user.is_staff = True
    if instance.role == "admin":
        user.is_superuser = True

    user.save()

    # Link employee → user
    instance.user = user
    instance.save(update_fields=["user"])

    # Optional email (safe)
    if instance.email:
        try:
            send_mail(
                subject="Swad staff account created",
                message=(
                    f"Hello {instance.name},\n\n"
                    f"Your staff account has been created.\n\n"
                    f"Username: {user.username}\n"
                    f"Password: {password}\n\n"
                    f"Please change your password after first login.\n\n"
                    f"— Swad of Tamil"
                ),
                from_email="no-reply@swad.local",
                recipient_list=[instance.email],
                fail_silently=True,
            )
        except Exception:
            pass
