from django.db import models
from django.utils import timezone


class StoreStatus(models.Model):
    """
    MASTER SWITCH — Emergency/Manual Override Control

    Purpose: Emergency close, festival close, power cut, manual override.
    This is NOT the timing system (that's StoreShift).

    Examples:
    - Power outage: Turn OFF to close immediately
    - Festival: Turn OFF for holiday closure
    - Emergency: Turn OFF for any urgent situation
    - Normal operation: Keep ON (timing handled by shifts)
    """

    is_enabled = models.BooleanField(
        default=True,
        help_text="MASTER SWITCH: Turn OFF to force close store (emergency/festival/power cut)"
    )

    accept_orders = models.BooleanField(
        default=True,
        help_text="ACCEPT ORDERS: Turn OFF to stop accepting new orders (overload control)"
    )

    kitchen_active = models.BooleanField(
        default=True,
        help_text="KITCHEN ACTIVE: Turn OFF to stop cooking (prep-only mode)"
    )

    note = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional message shown to customers (e.g., 'Closed for festival')"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store Status"
        verbose_name_plural = "Store Status"

    def __str__(self):
        return "ENABLED" if self.is_enabled else "DISABLED"

    # ======================================================
    # MASTER SWITCH LOGIC
    # ======================================================
    @property
    def is_master_switch_on(self) -> bool:
        """
        Master switch status.
        True = Store can operate (if shifts are active)
        False = Store is forcibly closed (emergency/festival/power cut)
        """
        return self.is_enabled

    @property
    def status_label(self) -> str:
        return "ENABLED" if self.is_enabled else "DISABLED"


# ======================================================
# STORE SHIFT (MULTI-SHIFT TIMING)
# ======================================================

class StoreShift(models.Model):
    """
    Defines operating time windows (shifts) for the store.
    
    Examples:
        Morning: 09:30 - 14:00
        Evening: 18:00 - 22:00
    
    Used by:
    - Order acceptance (only accept during active shifts)
    - Kitchen operations
    - Delivery scheduling
    """

    name = models.CharField(
        max_length=20,
        help_text="e.g. 'Morning', 'Evening', 'Late Night'"
    )

    start_time = models.TimeField(
        help_text="Shift start time (e.g. 09:30)"
    )

    end_time = models.TimeField(
        help_text="Shift end time (e.g. 14:00)"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate to close this shift"
    )

    cutoff_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Minutes before end_time when orders stop being accepted (e.g. 15 = last order at 1:45 PM for 2:00 PM close)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]
        verbose_name = "Store Shift"
        verbose_name_plural = "Store Shifts"
        unique_together = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Prevent 0-length shifts
        if self.start_time == self.end_time:
            raise ValidationError("Shift start and end time cannot be the same.")

        # Prevent overlapping shifts (only check active shifts)
        overlapping = StoreShift.objects.filter(is_active=True).exclude(pk=self.pk)
        
        for shift in overlapping:
            # Check for overlap: two time ranges overlap if start1 < end2 and end1 > start2
            if self.start_time < shift.end_time and self.end_time > shift.start_time:
                raise ValidationError(
                    f"Shift overlaps with {shift.name} ({shift.start_time}-{shift.end_time})"
                )

    # ======================================================
    # LOGIC
    # ======================================================
    @property
    def is_currently_active(self) -> bool:
        """Check if this shift is active right now"""
        if not self.is_active:
            return False

        now = timezone.localtime().time()

        # Normal same-day window (e.g. 09:30 → 14:00)
        if self.start_time < self.end_time:
            return self.start_time <= now <= self.end_time

        # Overnight window (e.g. 22:00 → 06:00)
        return now >= self.start_time or now <= self.end_time

    @property
    def can_accept_orders_now(self) -> bool:
        """Check if this shift is currently accepting orders (before cutoff)"""
        if not self.is_active:
            return False

        from datetime import datetime, timedelta
        now = timezone.localtime()

        today = now.date()
        start_dt = timezone.make_aware(datetime.combine(today, self.start_time))
        end_dt = timezone.make_aware(datetime.combine(today, self.end_time))

        if self.start_time > self.end_time:
            # Overnight shift
            end_dt += timedelta(days=1)
            
            # If we're currently in the "next day" portion of the shift,
            # the shift actually started yesterday
            if now.time() <= self.end_time:
                start_dt -= timedelta(days=1)

        cutoff_dt = end_dt - timedelta(minutes=self.cutoff_minutes)

        return start_dt <= now <= cutoff_dt

    def _get_cutoff_time(self):
        """Calculate the cutoff time (end_time - cutoff_minutes)"""
        from datetime import datetime, timedelta
        # Convert times to datetime for calculation
        today = timezone.localtime().date()
        end_datetime = datetime.combine(today, self.end_time)
        cutoff_datetime = end_datetime - timedelta(minutes=self.cutoff_minutes)
        return cutoff_datetime.time()

    @classmethod
    def get_active_shifts(cls):
        """Get all active shifts (business rules may apply)"""
        return cls.objects.filter(is_active=True).order_by("start_time")

    @classmethod
    def current_shift(cls):
        """Get the shift currently in progress, or None"""
        now = timezone.localtime().time()
        for shift in cls.get_active_shifts():
            if shift.start_time < shift.end_time:
                if shift.start_time <= now <= shift.end_time:
                    return shift
            else:  # Overnight shift
                if now >= shift.start_time or now <= shift.end_time:
                    return shift
        return None

    @classmethod
    def is_open_now(cls) -> bool:
        """Check if ANY shift is currently active"""
        return cls.current_shift() is not None

    @classmethod
    def can_accept_orders_now_cls(cls) -> bool:
        """Check if ANY shift is currently accepting orders (before cutoff)"""
        return any(shift.can_accept_orders_now for shift in cls.get_active_shifts())

    @classmethod
    def next_opening_datetime(cls):
        """
        Get the next datetime when the store will open.
        
        Used for UX: Show customers "Opens at 6:00 PM"
        
        Logic:
        - If store is closed: Find next shift today after now
        - If store is open: Use first shift of next day
        - Return datetime or None if no active shifts
        """
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.localtime()
        today = now.date()
        current_time = now.time()
        
        active_shifts = cls.get_active_shifts()
        if not active_shifts:
            return None
        
        # If store is closed, find next shift today after now
        if not cls.is_open_now():
            for shift in active_shifts:
                if shift.start_time > current_time:
                    next_open = timezone.make_aware(
                        datetime.combine(today, shift.start_time)
                    )
                    return next_open
        
        # Store is open or no more shifts today, use first shift of next day
        tomorrow = today + timedelta(days=1)
        first_shift_tomorrow = min(active_shifts, key=lambda s: s.start_time)
        
        next_open = timezone.make_aware(
            datetime.combine(tomorrow, first_shift_tomorrow.start_time)
        )
        return next_open


# ======================================================
# STORE EXCEPTION (CALENDAR OVERRIDES)
# ======================================================

class StoreException(models.Model):
    """
    Calendar exceptions for special dates.
    
    Overrides normal operating hours for:
    - Festivals and holidays
    - Maintenance days
    - Special events
    - Emergency closures
    """
    
    date = models.DateField(
        unique=True,
        help_text="Date of the exception"
    )
    
    is_closed = models.BooleanField(
        default=True,
        help_text="True = Store closed all day, False = Store open all day"
    )
    
    note = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for exception (e.g., 'Diwali Festival', 'Maintenance')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["date"]
        verbose_name = "Store Exception"
        verbose_name_plural = "Store Calendar"
    
    def __str__(self):
        status = "CLOSED" if self.is_closed else "OPEN"
        return f"{self.date}: {status} - {self.note or 'No note'}"
    
    @classmethod
    def get_exception_for_today(cls):
        """Get exception for current date, or None"""
        from django.utils import timezone
        today = timezone.localdate()
        return cls.objects.filter(date=today).first()
    
    @classmethod
    def today_override(cls):
        """Get today's calendar override, or None if no exception"""
        exception = cls.get_exception_for_today()
        if not exception:
            return None
        return {
            "is_closed": exception.is_closed,
            "note": exception.note,
        }


class BreakfastWindow(models.Model):
    """
    BREAKFAST WINDOW STATUS — Django-Driven Timing System

    Purpose: Control breakfast availability window with premium UX messaging.
    Separate from general StoreShift system for focused breakfast operations.

    Examples:
        Morning: 06:00 - 10:00 (Fresh Tamil breakfast window)
        Status: OPEN, CLOSED, OPENING_SOON
    """

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('OPENING_SOON', 'Opening Soon'),
    ]

    name = models.CharField(
        max_length=50,
        default="Breakfast Window",
        help_text="Display name (e.g., 'Breakfast Window')"
    )

    opens_at = models.TimeField(
        help_text="Breakfast window opens at (e.g., 06:00)"
    )

    closes_at = models.TimeField(
        help_text="Breakfast window closes at (e.g., 10:00)"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this breakfast window"
    )

    status_label = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CLOSED',
        help_text="Current status label for frontend"
    )

    status_message = models.CharField(
        max_length=100,
        blank=True,
        help_text="Single source of truth message (e.g., 'Opens at 9:30 AM')"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Breakfast Window"
        verbose_name_plural = "Breakfast Windows"

    def __str__(self):
        return f"{self.name} ({self.opens_at} - {self.closes_at})"

    @property
    def is_open_now(self) -> bool:
        """Check if breakfast window is currently open"""
        if not self.is_active:
            return False

        from django.utils import timezone
        now = timezone.localtime().time()
        return self.opens_at <= now <= self.closes_at

    @property
    def next_open_datetime(self):
        """Get next opening datetime"""
        from django.utils import timezone
        from datetime import datetime

        now = timezone.localtime()
        today = now.date()
        current_time = now.time()

        # If opens today after current time
        if self.opens_at > current_time:
            next_open = timezone.make_aware(
                datetime.combine(today, self.opens_at)
            )
            return next_open

        # Opens tomorrow
        tomorrow = today.replace(day=today.day + 1)
        next_open = timezone.make_aware(
            datetime.combine(tomorrow, self.opens_at)
        )
        return next_open

    @classmethod
    def get_current_status(cls):
        """Get current breakfast window status for API"""
        try:
            window = cls.objects.filter(is_active=True).first()
            if not window:
                return {
                    "is_open": False,
                    "status_label": "CLOSED",
                    "status_message": "Breakfast window not configured",
                    "opens_at": None,
                    "closes_at": None,
                    "next_open_at": None,
                }

            is_open = window.is_open_now
            next_open = window.next_open_datetime if not is_open else None

            return {
                "is_open": is_open,
                "status_label": window.status_label,
                "status_message": window.status_message or cls._generate_message(window, is_open, next_open),
                "opens_at": window.opens_at.strftime("%H:%M") if window.opens_at else None,
                "closes_at": window.closes_at.strftime("%H:%M") if window.closes_at else None,
                "next_open_at": next_open.isoformat() if next_open else None,
            }

        except Exception as e:
            # Fallback for any errors
            return {
                "is_open": False,
                "status_label": "CLOSED",
                "status_message": "Unable to check breakfast status",
                "opens_at": None,
                "closes_at": None,
                "next_open_at": None,
            }

    @classmethod
    def _generate_message(cls, window, is_open, next_open):
        """Generate status message if not manually set"""
        if is_open:
            return f"Open until {window.closes_at.strftime('%I:%M %p')}"
        elif next_open:
            return f"Opens at {next_open.strftime('%I:%M %p')}"
        else:
            return "Currently closed"
