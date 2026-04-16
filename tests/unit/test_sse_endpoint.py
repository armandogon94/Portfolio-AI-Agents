"""Unit tests for the GET /crew/run/{task_id}/events SSE endpoint (slice-19).

Covers:
- 404 for unknown task_id
- ordered agent_state events with a terminal run_complete
- auto-close after terminal event
- auth gating (when API_KEY is configured)
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestSseEndpoint:
    @pytest.fixture
    def client(self):
        # Reset slowapi rate limiter so a preceding test file doesn't exhaust quota.
        # (Pattern from test_webhook.py after the 46b2feb fixture fix.)
        from src.main import app, limiter

        limiter._storage.reset()

        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = None  # bypass auth by default
            yield TestClient(app, raise_server_exceptions=False)

    def _publish(self, task_id: str, state: str, detail: str = "") -> None:
        from src.models.schemas import AgentStateEvent
        from src.services.state_bus import get_state_bus

        bus = get_state_bus()
        bus.publish(
            task_id,
            AgentStateEvent(
                task_id=task_id,
                agent_role="researcher",
                state=state,
                detail=detail,
                ts="2026-04-16T10:00:00+00:00",
            ),
        )

    def test_events_unknown_task_id_returns_404(self, client):
        """Streaming a task that was never created returns 404."""
        resp = client.get("/crew/run/does-not-exist/events")
        assert resp.status_code == 404

    def test_events_streams_agent_state_and_run_complete(self, client):
        """Events are delivered as SSE frames, ending with a run_complete event."""
        from src.main import task_store

        task_id = task_store.create(topic="test", domain=None)

        # Pre-publish events so the subscriber receives them via replay.
        self._publish(task_id, "queued")
        self._publish(task_id, "active", detail="tool: web_search")
        self._publish(task_id, "completed", detail="crew finished")

        with client.stream("GET", f"/crew/run/{task_id}/events") as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            body = "".join(resp.iter_text())

        # Each publish produces an agent_state frame.
        assert body.count("event: agent_state") == 3
        # Terminal event closes the stream with a run_complete frame.
        assert "event: run_complete" in body
        # Ordering: queued before active before completed before run_complete.
        assert body.index("queued") < body.index("active") < body.index("completed")
        assert body.index("completed") < body.index("run_complete")

    def test_events_auto_closes_after_terminal(self, client):
        """Once a terminal event is delivered, the stream ends (does not block)."""
        from src.main import task_store

        task_id = task_store.create(topic="test", domain=None)
        self._publish(task_id, "failed", detail="boom")

        # If auto-close is broken, this would hang; test harness would timeout.
        with client.stream("GET", f"/crew/run/{task_id}/events") as resp:
            body = "".join(resp.iter_text())

        assert resp.status_code == 200
        assert "event: run_complete" in body
        assert '"status":"failed"' in body

    def test_events_requires_api_key_when_configured(self):
        """With API_KEY set, the SSE route rejects requests missing the X-API-Key header."""
        from src.main import app, limiter, task_store

        limiter._storage.reset()

        task_id = task_store.create(topic="test", domain=None)

        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = "secret-key"
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get(f"/crew/run/{task_id}/events")
            assert resp.status_code == 401

            # With the correct header it should at least start streaming.
            self._publish(task_id, "completed")
            resp_ok = client.get(
                f"/crew/run/{task_id}/events",
                headers={"X-API-Key": "secret-key"},
            )
            assert resp_ok.status_code == 200
