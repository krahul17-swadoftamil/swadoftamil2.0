from django.db import transaction, IntegrityError
from django.utils import timezone


def auto_code(prefix: str, model, field: str, width: int) -> str:
    """
    Generate the next unique code for `model` based on `field` values
    that start with `prefix-`.

    Returns a string like f"{prefix}-{n:0{width}}".

    NOTE: This function does a best-effort read of the last code. Callers
    should wrap save() in a retry loop and handle IntegrityError to avoid
    race conditions in high-concurrency environments.
    """
    last = (
        model.objects
        .filter(**{f"{field}__startswith": f"{prefix}-"})
        .order_by(f"-{field}")
        .first()
    )

    if last:
        last_val = getattr(last, field)
        try:
            n = int(last_val.split("-")[-1]) + 1
        except Exception:
            n = 1
    else:
        n = 1

    return f"{prefix}-{str(n).zfill(width)}"


def generate_and_set_code(instance, prefix: str, field: str, width: int):
    """
    Helper wrapper that attempts to generate a code and set it on the
    instance. It does not save the instance.
    """
    if getattr(instance, field):
        return getattr(instance, field)

    Model = instance.__class__

    # Best-effort attempt — actual save should handle IntegrityError retries.
    code = auto_code(prefix, Model, field, width)
    setattr(instance, field, code)
    return code


# ======================================================
# SINGLE SOURCE OF TRUTH — STORE RUNTIME STATUS
# ======================================================

def store_runtime_status():
    """
    SINGLE SOURCE OF TRUTH: Complete store runtime status.
    
    Used by frontend, API, orders, admin — NO OTHER CODE should decide open/closed.
    
    Returns dict with comprehensive status information.
    """
    from .models import StoreStatus, StoreShift, StoreException
    
    # Get store status (should always exist)
    try:
        status = StoreStatus.objects.get()
    except StoreStatus.DoesNotExist:
        # Emergency fallback - assume closed
        return {
            "open": False,
            "reason": "no_store_status_configured",
            "accept_orders": False,
            "kitchen_active": False,
            "current_shift": None,
            "message": "Store status not configured",
            "next_opening": None,
            "order_cutoff": None,
            "calendar_exception": None,
        }
    
    # Check manual override first
    if not status.is_enabled:
        return {
            "open": False,
            "reason": "manual_override",
            "accept_orders": False,
            "kitchen_active": False,
            "current_shift": None,
            "message": status.note or "Store temporarily closed",
            "next_opening": next_opening_time(),
            "order_cutoff": None,
            "calendar_exception": None,
        }
    
    # Check calendar exceptions
    override = StoreException.today_override()
    if override:
        if override["is_closed"]:
            return {
                "open": False,
                "reason": "calendar_exception",
                "accept_orders": False,
                "kitchen_active": False,
                "current_shift": None,
                "message": override["note"] or "Store closed for special occasion",
                "next_opening": next_opening_time(),
                "order_cutoff": None,
                "calendar_exception": {
                    "date": StoreException.get_exception_for_today().date,
                    "is_closed": override["is_closed"],
                    "note": override["note"],
                },
            }
        else:
            # Special open day
            return {
                "open": True,
                "reason": "calendar_exception_open",
                "accept_orders": status.accept_orders,
                "kitchen_active": status.kitchen_active,
                "current_shift": "Special Hours",
                "message": override["note"] or "Store open for special occasion",
                "next_opening": None,
                "order_cutoff": None,  # Special hours - no cutoff
                "calendar_exception": {
                    "date": StoreException.get_exception_for_today().date,
                    "is_closed": override["is_closed"],
                    "note": override["note"],
                },
            }
    
    # Check if any shift is active
    if not StoreShift.is_open_now():
        return {
            "open": False,
            "reason": "no_active_shift",
            "accept_orders": False,
            "kitchen_active": False,
            "current_shift": None,
            "message": status.note or "Store is currently closed",
            "next_opening": next_opening_time(),
            "order_cutoff": None,
            "calendar_exception": None,
        }
    
    # Store is open - get current shift info
    current_shift_obj = StoreShift.current_shift()
    current_shift = current_shift_obj.name if current_shift_obj else None
    
    # Calculate order cutoff
    order_cutoff = None
    if current_shift_obj and status.accept_orders:
        order_cutoff = current_shift_obj._get_cutoff_time()
    
    return {
        "open": True,
        "reason": "normal_operation",
        "accept_orders": status.accept_orders and StoreShift.can_accept_orders_now_cls(),
        "kitchen_active": status.kitchen_active,
        "current_shift": current_shift,
        "message": status.note,
        "next_opening": None,
        "order_cutoff": order_cutoff,
        "calendar_exception": None,
    }


# ======================================================
# STORE STATUS UTILITIES — DEPRECATED (use store_runtime_status)
# ======================================================

def is_store_open() -> bool:
    """
    SINGLE SOURCE OF TRUTH: Is the store open for business?

    This is the ONLY function frontend/API/orders should trust.

    DELEGATES TO: store_runtime_status() for all logic.

    Returns True ONLY if store_runtime_status()["open"] is True.
    """
    return store_runtime_status()["open"]


def get_store_status() -> dict:
    """
    Get complete store status for API/frontend.

    DELEGATES TO: store_runtime_status() for all logic.

    Returns the result from store_runtime_status() with field name mapping for backward compatibility.
    """
    status = store_runtime_status()
    
    return {
        'is_open': status['open'],
        'accept_orders': status['accept_orders'],
        'kitchen_active': status['kitchen_active'],
        'master_switch': status.get('manual_override', False),  # From reason
        'shifts_active': status['current_shift'] is not None,
        'current_shift': status['current_shift'],
        'message': status['message'],
        'next_opening': status['next_opening'],
        'order_cutoff': status['order_cutoff'],
        'calendar_exception': status['calendar_exception'],
    }


def next_opening_time():
    """
    Get the next opening time for UX display.

    Returns the start_time of the next upcoming active shift,
    or None if no shifts are scheduled.

    Used for customer messages like:
    "❌ Closed — opens at 6:00 PM"
    """
    from .models import StoreShift

    now = timezone.localtime().time()
    upcoming = StoreShift.objects.filter(
        is_active=True,
        start_time__gt=now
    ).order_by("start_time").first()

    return upcoming.start_time if upcoming else None


def next_opening_datetime():
    """
    Get the next opening datetime for comprehensive UX & operations.

    Returns the datetime when store will next open, considering:
    - If store is closed: Find next shift today after now
    - If store is open: Use first shift of next day

    Used for:
    - Customer messages: "❌ Closed · Opens at 6:00 PM"
    - Admin operations planning
    - Order scheduling logic

    Returns datetime or None if no active shifts.
    """
    from .models import StoreShift
    return StoreShift.next_opening_datetime()


def can_accept_orders() -> bool:
    """
    Can the store accept new orders?

    DELEGATES TO: store_runtime_status() for all logic.

    Returns store_runtime_status()["accept_orders"].
    """
    return store_runtime_status()["accept_orders"]


def is_kitchen_active() -> bool:
    """
    Is the kitchen actively cooking/preparing?

    DELEGATES TO: store_runtime_status() for all logic.

    Returns store_runtime_status()["kitchen_active"].
    """
    return store_runtime_status()["kitchen_active"]
