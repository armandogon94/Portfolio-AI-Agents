"""Regression tests for the Phase-4 Critical review fixes.

Each test pins a specific hardening contract:
  - PDF export is awaited on a worker thread, never in-line on the loop.
  - State bus has a cleanup loop bound to the lifespan.
  - SSE route is rate-limited just like every other state-reader.
  - Twilio webhook validates the signature before touching the form body.
  - TaskStore.cleanup() cascades to VoiceSessionStore so abandoned
    voice sessions don't leak.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestPdfAsyncPath:
    """C1: WeasyPrint must run in a worker thread."""

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

    def test_pdf_route_runs_render_via_asyncio_to_thread(self, client):
        from src.main import sqlite_store, task_store

        task_id = task_store.create(topic="for-pdf-hardened", domain=None)
        task_store.update(task_id, status="completed", result="done")
        sqlite_store.save(
            task_id=task_id, topic="for-pdf-hardened", domain=None,
            result="done", duration_seconds=1.0,
        )

        sentinel = b"%PDF-FAKE"
        with patch("src.main.asyncio.to_thread", new=AsyncMock(return_value=sentinel)) as mock_to_thread:
            resp = client.get(f"/crew/history/{task_id}/pdf")

        assert resp.status_code == 200
        assert resp.content == sentinel
        # to_thread was awaited exactly once with the render function.
        mock_to_thread.assert_awaited_once()
        args, _ = mock_to_thread.call_args
        from src.services.pdf_export import render_run_pdf

        assert args[0] is render_run_pdf


@pytest.mark.unit
class TestStateBusCleanupLoop:
    """C2: the state bus must have a periodic cleanup task bound to lifespan."""

    def test_cleanup_loop_task_exists_on_bus(self):
        """The AgentStateBus exposes a start_cleanup_loop(interval) helper that
        returns an asyncio.Task so the lifespan can cancel it on shutdown."""
        import asyncio

        from src.services.state_bus import AgentStateBus

        bus = AgentStateBus(ttl_seconds=60)

        async def _drive():
            task = bus.start_cleanup_loop(interval_seconds=0.01)
            assert isinstance(task, asyncio.Task)
            # Let the loop run once, then cancel.
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(_drive())

    def test_lifespan_binds_cleanup_loop(self):
        """The FastAPI lifespan must call start_cleanup_loop on the bound bus."""
        from src.services.state_bus import AgentStateBus

        # AgentStateBus is instantiated lazily via get_state_bus(); the
        # lifespan wires it. We check the module-level source for the call
        # so this regression test doesn't depend on async lifespan context.
        from pathlib import Path
        main_src = Path(__file__).resolve().parent.parent.parent / "src" / "main.py"
        body = main_src.read_text()
        assert "start_cleanup_loop" in body, (
            "src/main.py lifespan must call bus.start_cleanup_loop()"
        )
        # Sanity: the helper lives on the bus
        assert hasattr(AgentStateBus, "start_cleanup_loop")


@pytest.mark.unit
class TestSseRateLimited:
    """C3: /crew/run/{id}/events must carry a slowapi rate-limit decorator."""

    def test_events_route_decorated_with_rate_limit(self):
        """Introspect the route and confirm the rate-limit marker is present."""
        from src.main import app

        for route in app.routes:
            if getattr(route, "path", "") == "/crew/run/{task_id}/events":
                endpoint = route.endpoint
                # slowapi stores the per-route limit either via _limits or
                # an attribute on the endpoint that its decorator sets.
                marker = getattr(endpoint, "_rate_limit", None) or getattr(
                    endpoint, "__wrapped__", None
                )
                assert marker is not None, (
                    "Expected /crew/run/{task_id}/events to be decorated with @limiter.limit"
                )
                return
        pytest.fail("SSE route /crew/run/{task_id}/events not registered")


@pytest.mark.unit
class TestTwilioSignatureFirst:
    """C4: the TwiML webhook must validate X-Twilio-Signature before parsing the form."""

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

    def test_form_body_is_not_parsed_when_signature_invalid(self, client):
        """If the signature is bad, request.form() must never be awaited —
        otherwise an attacker forces expensive parsing without authenticating."""
        with (
            patch("src.main.settings") as s,
            patch("src.main.RequestValidator") as MockValidator,
            patch("fastapi.Request.form", new=AsyncMock()) as mock_form,
        ):
            s.voice_enabled = True
            s.twilio_auth_token = "tok"
            MockValidator.return_value.validate.return_value = False

            resp = client.post(
                "/voice/twiml/whatever",
                content=b"CallSid=CA1&From=%2B15550001111&To=%2B15550002222",
                headers={
                    "X-Twilio-Signature": "bogus",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        assert resp.status_code == 403
        mock_form.assert_not_awaited()


@pytest.mark.unit
class TestVoiceSessionTaskStoreCascade:
    """I1: TaskStore.cleanup() must cascade to VoiceSessionStore."""

    def test_taskstore_cleanup_clears_voice_sessions_for_expired_tasks(self):
        """Use a generous TTL + hand-age the task so create()'s lazy
        cleanup doesn't evict it before we attach a voice session."""
        from src.services.task_store import TaskStore
        from src.services.voice_session import VoiceSessionStore

        sessions = VoiceSessionStore()
        store = TaskStore(ttl_seconds=3600, voice_session_store=sessions)

        task_id = store.create(topic="voice-run", domain=None)
        sessions.get_or_create(task_id, max_turns=3)
        assert sessions.get(task_id) is not None

        # Age the task beyond the TTL so cleanup() evicts it.
        store._tasks[task_id]["created_at"] = 0.0

        removed = store.cleanup()
        assert removed >= 1
        assert sessions.get(task_id) is None, (
            "VoiceSession for an evicted task_id must be cleared (memory leak fix)"
        )

    def test_taskstore_cleanup_is_safe_without_voice_store(self):
        """Back-compat: when no voice store is wired, cleanup still works."""
        from src.services.task_store import TaskStore

        store = TaskStore(ttl_seconds=3600)
        task_id = store.create(topic="no-voice", domain=None)
        store._tasks[task_id]["created_at"] = 0.0
        assert store.cleanup() >= 1
