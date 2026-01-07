from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import now
from .models import BreakfastWindow


@require_GET
def breakfast_window_status(request):
    """
    BREAKFAST WINDOW STATUS — Django-Driven API

    Returns current breakfast window status for frontend display.
    Single source of truth - no frontend logic for status calculation.

    Response format:
    {
      "is_open": false,
      "status_label": "CLOSED",
      "status_message": "Opens at 9:30 AM",
      "opens_at": "09:30",
      "closes_at": "12:30",
      "next_open_at": "2026-01-08T09:30:00"
    }
    """
    status = BreakfastWindow.get_current_status()
    return JsonResponse(status, status=200)


@require_GET
def health(request):
    """
    Health check endpoint for Swad of Tamil.

    Purpose:
    - Load balancer / reverse proxy health checks
    - Uptime & monitoring systems
    - Deployment verification

    Notes:
    - Must remain fast
    - Must not touch database or external services
    """

    return JsonResponse(
        {
            "status": "ok",
            "service": "swad-of-tamil",
            "timestamp": now().isoformat(),
        },
        status=200,
    )
