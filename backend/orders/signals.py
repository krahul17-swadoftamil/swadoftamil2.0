from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """Update Customer metrics when an order is created.

    This is intentionally simple: on creation, increment `total_orders` and set
    `first_order_at`/`last_order_at` appropriately. More advanced handling (e.g.
    on cancellations) can be added later.
    """
    try:
        customer = getattr(instance, "customer", None)
        if not customer:
            return

        updated = False
        # Increment total_orders for newly created orders
        if created:
            customer.total_orders = (customer.total_orders or 0) + 1
            updated = True

        # Update first_order_at
        if not customer.first_order_at or (instance.created_at and instance.created_at < customer.first_order_at):
            customer.first_order_at = instance.created_at or timezone.now()
            updated = True

        # Update last_order_at
        if not customer.last_order_at or (instance.created_at and instance.created_at > customer.last_order_at):
            customer.last_order_at = instance.created_at or timezone.now()
            updated = True

        if updated:
            customer.save(update_fields=["first_order_at", "last_order_at", "total_orders"])  # type: ignore
    except Exception:
        # Never allow signal errors to break order save
        return
