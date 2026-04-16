"""VoiceCallTool — Twilio-trial outbound calling (slice-26, DEC-21).

Gated behind ``VOICE_ENABLED`` (DEC-22). Only dials numbers on the
``TWILIO_VERIFIED_TO_NUMBERS`` whitelist to reduce TCPA exposure.
Never logs auth tokens or full Twilio signatures.
"""

from __future__ import annotations

import logging
from typing import Any

from twilio.rest import Client

from src.config.settings import settings
from src.exceptions import ValidationError, VoiceDisabledError
from src.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("voice_call")
class VoiceCallTool:
    """Place outbound phone calls via Twilio.

    Not a CrewAI BaseTool — the receptionist workflow calls this directly
    from the caller agent's task handler. Registered in the tool registry
    so the FastAPI layer can introspect it.
    """

    name = "voice_call"
    description = (
        "Place an outbound phone call via Twilio. Only dials verified "
        "numbers. Disabled by default (VOICE_ENABLED=false)."
    )

    def place_call(self, to: str, task_id: str) -> dict[str, Any]:
        """Initiate an outbound call. Returns ``{'sid': call_sid}`` on success.

        Raises:
            VoiceDisabledError: when ``VOICE_ENABLED`` is false.
            ValidationError: when ``to`` is not on the verified whitelist
                or Twilio credentials are missing.
        """
        if not settings.voice_enabled:
            raise VoiceDisabledError()

        whitelist = settings.twilio_verified_to_numbers or []
        if to not in whitelist:
            raise ValidationError(
                f"Refusing to dial {to} — number is not in TWILIO_VERIFIED_TO_NUMBERS "
                f"(TCPA guardrail, DEC-22)."
            )
        if not (settings.twilio_account_sid and settings.twilio_auth_token):
            raise ValidationError("Twilio credentials are not configured.")
        if not settings.twilio_from_number:
            raise ValidationError("TWILIO_FROM_NUMBER is not configured.")

        webhook_url = f"{settings.twilio_webhook_base.rstrip('/')}/voice/twiml/{task_id}"
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        call = client.calls.create(
            to=to,
            from_=settings.twilio_from_number,
            url=webhook_url,
        )
        # Log the call SID — safe. Never log the auth token or the webhook
        # URL body (in case secrets end up in the webhook-base query string).
        logger.info(f"Placed call sid={call.sid} task_id={task_id}")
        return {"sid": call.sid}


