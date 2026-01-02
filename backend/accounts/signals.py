from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from .models import UserCode, Customer
from .models import Employee

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_usercode_and_notify(sender, instance, created, **kwargs):
    """Create a UserCode and email credentials to new users when created.

    - Generates a random password if created via admin/script and emails it.
    - Creates a `UserCode` record if missing.
    """
    # Ensure UserCode exists
    try:
        UserCode.objects.get_or_create(user=instance)
    except Exception:
        pass

    if created:
        # Generate a random password and set on user if unusable
        password = get_random_string(10)
        try:
            instance.set_password(password)
            instance.save()
        except Exception:
            password = None

        # Send email with credentials
        try:
            subject = "Your Swad admin account"
            body = f"Hello {instance.get_full_name() or instance.username},\n\nYour account has been created.\n"
            if password:
                body += f"Username: {instance.username}\nPassword: {password}\n\nPlease change your password after first login.\n"
            body += "\nRegards,\nSwad of Tamil"

            send_mail(
                subject,
                body,
                'no-reply@swad.local',
                ['krahul17@gmail.com', instance.email] if instance.email else ['krahul17@gmail.com'],
                fail_silently=True,
            )
        except Exception:
            pass


@receiver(post_save, sender=Customer)
def ensure_customer_user(sender, instance, created, **kwargs):
    """Optional: create a linked Django User for Customer for login.

    For now, do not auto-create users for customers; user login will be via OTP flow.
    This hook ensures any necessary side-effects for customers.
    """
    # If the customer was just created and has an email, create a minimal
    # Django auth user so we can optionally email credentials.
    try:
        if not created:
            return

        # Only create a user when an email is present
        if not instance.email:
            return

        UserModel = User

        # Derive a username from phone or customer code or name
        base = None
        if getattr(instance, "phone", None):
            base = instance.phone.replace("+", "").replace(" ", "")
        elif getattr(instance, "code", None):
            base = instance.code.lower()
        else:
            base = (instance.name or "customer").replace(" ", "").lower()

        username = base
        suffix = 0
        while UserModel.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"

        # Do not create duplicate by email
        if UserModel.objects.filter(email=instance.email).exists():
            return

        from django.utils.crypto import get_random_string

        password = get_random_string(10)
        user = UserModel.objects.create_user(username=username, email=instance.email, password=password)

        # Send credentials email to customer and admin for record
        try:
            subject = "Your Swad account"
            body = f"Hello {instance.name or instance.phone},\n\nAn account has been created for you on Swad of Tamil.\n\nUsername: {user.username}\nPassword: {password}\n\nYou can login and view your orders.\n\nRegards,\nSwad of Tamil"
            send_mail(subject, body, 'no-reply@swad.local', [instance.email], fail_silently=True)
        except Exception:
            pass

    except Exception:
        # Never fail customer saves due to signal errors
        return


@receiver(post_save, sender=Employee)
def ensure_employee_user(sender, instance, created, **kwargs):
    """Auto-create a Django `User` for an Employee when missing.

    - Creates a username derived from email or name/code
    - Marks `is_staff=True`; `is_superuser=True` only for admin role
    - Stores the created user on `employee.user` (nullable link)
    """
    try:
        if instance.user:
            return

        UserModel = User
        base = None
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

        password = get_random_string(10)
        user = UserModel.objects.create_user(username=username, email=instance.email or "", password=password)
        user.is_staff = True
        if getattr(instance, "role", None) == Employee.ROLE_ADMIN:
            user.is_superuser = True
        user.save()

        # Link back to employee
        instance.user = user
        instance.save(update_fields=["user"])  # type: ignore

        # Send email with credentials to admin and employee (if email present)
        try:
            subject = "Swad staff account created"
            body = f"Hello {instance.name},\n\nAn account has been created for you.\nUsername: {user.username}\nPassword: {password}\n\nPlease change your password on first login.\n"
            send_mail(subject, body, 'no-reply@swad.local', ['krahul17@gmail.com', instance.email] if instance.email else ['krahul17@gmail.com'], fail_silently=True)
        except Exception:
            pass

    except Exception:
        # Never fail employee saves due to signal errors
        return
