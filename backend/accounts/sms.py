import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
except Exception:
    Client = None


# ======================================================
# SEND SMS (TWILIO)
# ======================================================
def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS via Twilio.

    Rules:
    - NEVER send SMS in DEBUG / development
    - Fail silently in production (no crashes)
    - Return True only when message is actually sent
    """

    # ---------------- DEV MODE ----------------
    if settings.DEBUG or os.environ.get("ENV") == "development":
        logger.info(
            "[SMS:DEV] Skipping SMS → %s | %s",
            phone,
            message,
        )
        return False

    # ---------------- CONFIG ----------------
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", None)

    if not (sid and token and from_number):
        logger.warning("[SMS] Twilio credentials missing")
        return False

    if not Client:
        logger.warning("[SMS] Twilio client not installed")
        return False

    # ---------------- SEND ----------------
    try:
        client = Client(sid, token)
        client.messages.create(
            to=phone,
            from_=from_number,
            body=message,
        )
        logger.info("[SMS] Sent to %s", phone)
        return True

    except Exception as exc:
        logger.exception("[SMS] Failed to send to %s | %s", phone, exc)
        return False
