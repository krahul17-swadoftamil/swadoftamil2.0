from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import now


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
