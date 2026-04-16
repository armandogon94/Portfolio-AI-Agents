"""TwiML webhook unit tests (slice-26).

Covers:
  - valid signature + known task returns TwiML (text/xml)
  - missing/invalid signature rejected with 403
  - unknown task_id returns 404
  - call ends after max_turns
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestTwimlWebhook:
    @pytest.fixture
    def client(self):
        from src.main import app, limiter

        limiter._storage.reset()
        with (
            patch("src.middleware.auth.settings") as auth_settings,
            patch("src.main._execute_crew") as mock_execute,
        ):
            auth_settings.api_key = None
            mock_execute.return_value = None
            yield TestClient(app, raise_server_exceptions=False)

    def test_valid_signature_returns_twiml(self, client):
        from src.main import task_store

        task_id = task_store.create(topic="book a table", domain=None)

        with (
            patch("src.main.settings") as s,
            patch("src.main.RequestValidator") as MockValidator,
        ):
            s.voice_enabled = True
            s.twilio_auth_token = "tok"
            s.twilio_webhook_base = "https://example.ngrok.io"
            MockValidator.return_value.validate.return_value = True

            resp = client.post(
                f"/voice/twiml/{task_id}",
                data={"CallSid": "CA_1", "From": "+15550000000", "To": "+15551234567"},
                headers={"X-Twilio-Signature": "sig"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/xml")
        body = resp.text
        assert "<Response" in body
        # The agent must speak something on the first turn.
        assert "<Say" in body

    def test_missing_signature_returns_403(self, client):
        from src.main import task_store

        task_id = task_store.create(topic="t", domain=None)

        with patch("src.main.settings") as s:
            s.voice_enabled = True
            s.twilio_auth_token = "tok"

            resp = client.post(
                f"/voice/twiml/{task_id}",
                data={"CallSid": "CA_1"},
            )
        assert resp.status_code == 403

    def test_invalid_signature_returns_403(self, client):
        from src.main import task_store

        task_id = task_store.create(topic="t", domain=None)

        with (
            patch("src.main.settings") as s,
            patch("src.main.RequestValidator") as MockValidator,
        ):
            s.voice_enabled = True
            s.twilio_auth_token = "tok"
            MockValidator.return_value.validate.return_value = False

            resp = client.post(
                f"/voice/twiml/{task_id}",
                data={"CallSid": "CA_1"},
                headers={"X-Twilio-Signature": "bogus"},
            )
        assert resp.status_code == 403

    def test_unknown_task_id_returns_404(self, client):
        with (
            patch("src.main.settings") as s,
            patch("src.main.RequestValidator") as MockValidator,
        ):
            s.voice_enabled = True
            s.twilio_auth_token = "tok"
            MockValidator.return_value.validate.return_value = True

            resp = client.post(
                "/voice/twiml/does-not-exist",
                data={"CallSid": "CA_1"},
                headers={"X-Twilio-Signature": "sig"},
            )
        assert resp.status_code == 404

    def test_call_hangs_up_after_max_turns(self, client):
        """Once the voice session has reached its max_turns, the webhook
        returns a <Hangup/> instead of another <Gather/>."""
        from src.main import task_store
        from src.services.voice_session import get_voice_session_store

        task_id = task_store.create(topic="t", domain=None)
        sessions = get_voice_session_store()
        session = sessions.get_or_create(task_id, max_turns=1)
        session.record_turn(prompt="Hi", heard="yes")  # already at max

        with (
            patch("src.main.settings") as s,
            patch("src.main.RequestValidator") as MockValidator,
        ):
            s.voice_enabled = True
            s.twilio_auth_token = "tok"
            MockValidator.return_value.validate.return_value = True

            resp = client.post(
                f"/voice/twiml/{task_id}",
                data={"CallSid": "CA_1", "SpeechResult": "ok"},
                headers={"X-Twilio-Signature": "sig"},
            )
        assert resp.status_code == 200
        assert "<Hangup" in resp.text
