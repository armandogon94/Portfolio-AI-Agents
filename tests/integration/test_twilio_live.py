"""Opt-in live Twilio call smoke test (slice-26).

Skipped by default. Enable with: ``uv run pytest -m voice``.

Requires:
  - VOICE_ENABLED=true
  - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
  - TWILIO_VERIFIED_TO_NUMBERS containing a number you control
  - TWILIO_WEBHOOK_BASE pointing at an ngrok tunnel of your local API

DO NOT commit personal numbers. Read them from the environment.
"""

import os

import pytest


pytestmark = pytest.mark.voice


def test_place_verified_call_and_receive_sid():
    to = os.getenv("TWILIO_LIVE_TEST_TO")
    if not to:
        pytest.skip("Set TWILIO_LIVE_TEST_TO to a verified number to run this.")

    # Force-reload settings so the live env wins over conftest defaults.
    from src.config import settings as settings_module

    settings_module.settings = settings_module.Settings()

    from src.tools.voice import VoiceCallTool

    tool = VoiceCallTool()
    result = tool.place_call(to=to, task_id="live-smoke")
    assert result["sid"].startswith("CA")
