from django.db import models
from django.utils import timezone
import datetime


class StoreStatus(models.Model):
    """
    Single-row model to control store availability.
    This is the SINGLE source of truth for open / close logic.
    """

    is_open = models.BooleanField(
        default=True,
        help_text="Manual override. Turn OFF to force close store."
    )

    open_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily opening time (e.g. 06:00)"
    )

    close_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily closing time (e.g. 11:30)"
    )

    note = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional message shown to customers"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store Status"
        verbose_name_plural = "Store Status"

    def __str__(self):
        return "OPEN" if self.is_currently_open else "CLOSED"

    # ======================================================
    # CORE LOGIC (NO HARDCODE)
    # ======================================================
    @property
    def is_currently_open(self) -> bool:
        """
        Final decision used by frontend / API / orders.
        """

        # Manual override
        if not self.is_open:
            return False

        # If timing not configured, allow open
        if not self.open_time or not self.close_time:
            return True

        now = timezone.localtime().time()

        # Normal same-day window (e.g. 06:00 → 11:30)
        if self.open_time < self.close_time:
            return self.open_time <= now <= self.close_time

        # Overnight window (e.g. 18:00 → 02:00)
        return now >= self.open_time or now <= self.close_time

    @property
    def status_label(self) -> str:
        return "OPEN" if self.is_currently_open else "CLOSED"
