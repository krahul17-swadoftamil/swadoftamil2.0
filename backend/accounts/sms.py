from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
except Exception:
    Client = None


def send_sms(phone: str, message: str) -> bool:
    """Send SMS via Twilio if configured.

    Returns True on success, False otherwise.
    """
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", None)

    # In development or when DEBUG is True, never call the gateway.
    if getattr(settings, "DEBUG", False) or os.environ.get("ENV") == "development":
        logger.info("DEV MODE: Skipping SMS send to %s (message: %s)", phone, message)
        return False

    if not (sid and token and from_number and Client):
        logger.debug("Twilio not configured or client not installed; skipping SMS send")
        return False

    try:
        client = Client(sid, token)
        client.messages.create(to=phone, from_=from_number, body=message)
        logger.info("Sent OTP SMS to %s", phone)
        return True
    except Exception as e:
        logger.exception("Failed to send SMS to %s: %s", phone, e)
        return False
