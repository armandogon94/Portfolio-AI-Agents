"""VoiceCallTool unit tests (slice-26, DEC-21, DEC-22).

Fully mocks the Twilio client — no network calls. Covers:
  - default off (VOICE_ENABLED=false) raises VoiceDisabledError
  - enabled + verified number places a call with expected args
  - enabled + non-whitelisted number rejects with ValidationError
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestVoiceCallTool:
    def test_disabled_by_default_raises(self):
        from src.exceptions import VoiceDisabledError
        from src.tools.voice import VoiceCallTool

        with patch("src.tools.voice.settings") as s:
            s.voice_enabled = False
            s.twilio_account_sid = "AC_x"
            s.twilio_auth_token = "tok"
            s.twilio_from_number = "+15550000000"
            s.twilio_verified_to_numbers = ["+15551234567"]
            s.twilio_webhook_base = "https://example.ngrok.io"

            tool = VoiceCallTool()
            with pytest.raises(VoiceDisabledError):
                tool.place_call(to="+15551234567", task_id="run-1")

    def test_enabled_verified_to_creates_call(self):
        from src.tools.voice import VoiceCallTool

        fake_call = MagicMock(sid="CA_XXXX")
        fake_client = MagicMock()
        fake_client.calls.create.return_value = fake_call

        with (
            patch("src.tools.voice.settings") as s,
            patch("src.tools.voice.Client", return_value=fake_client) as MockClient,
        ):
            s.voice_enabled = True
            s.twilio_account_sid = "AC_x"
            s.twilio_auth_token = "tok"
            s.twilio_from_number = "+15550000000"
            s.twilio_verified_to_numbers = ["+15551234567"]
            s.twilio_webhook_base = "https://example.ngrok.io"

            tool = VoiceCallTool()
            result = tool.place_call(to="+15551234567", task_id="run-abc")

            MockClient.assert_called_once_with("AC_x", "tok")
            create_kwargs = fake_client.calls.create.call_args.kwargs
            assert create_kwargs["to"] == "+15551234567"
            assert create_kwargs["from_"] == "+15550000000"
            assert (
                create_kwargs["url"]
                == "https://example.ngrok.io/voice/twiml/run-abc"
            )
            assert result["sid"] == "CA_XXXX"

    def test_non_whitelisted_number_rejected(self):
        from src.exceptions import ValidationError
        from src.tools.voice import VoiceCallTool

        with patch("src.tools.voice.settings") as s:
            s.voice_enabled = True
            s.twilio_account_sid = "AC_x"
            s.twilio_auth_token = "tok"
            s.twilio_from_number = "+15550000000"
            s.twilio_verified_to_numbers = ["+15551234567"]
            s.twilio_webhook_base = "https://example.ngrok.io"

            tool = VoiceCallTool()
            with pytest.raises(ValidationError, match=r"VERIFIED_TO_NUMBERS"):
                tool.place_call(to="+15559999999", task_id="run-z")
