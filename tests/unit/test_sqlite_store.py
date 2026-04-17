"""Unit tests for SQLiteResultStore (slice-13)."""

import tempfile

import pytest


@pytest.mark.unit
class TestSQLiteResultStore:
    @pytest.fixture
    def store(self, tmp_path):
        from src.services.sqlite_store import SQLiteResultStore

        return SQLiteResultStore(db_path=str(tmp_path / "test.db"))

    def test_save_and_get(self, store):
        """save() persists a result; get() retrieves it by task_id."""
        store.save(
            task_id="task-001",
            topic="AI trends",
            domain="healthcare",
            result="Some detailed result here",
            duration_seconds=42.5,
        )
        row = store.get("task-001")
        assert row is not None
        assert row["task_id"] == "task-001"
        assert row["topic"] == "AI trends"
        assert row["domain"] == "healthcare"
        assert row["result"] == "Some detailed result here"
        assert row["duration_seconds"] == 42.5
        assert "created_at" in row

    def test_get_missing_returns_none(self, store):
        """get() returns None for unknown task_id."""
        assert store.get("nonexistent-id") is None

    def test_save_with_null_domain(self, store):
        """save() accepts None domain (general mode)."""
        store.save(task_id="task-002", topic="topic", domain=None, result="r")
        row = store.get("task-002")
        assert row["domain"] is None

    def test_list_recent_empty(self, store):
        """list_recent() returns [] when no rows exist."""
        assert store.list_recent() == []

    def test_list_recent_order(self, store):
        """list_recent() returns rows newest-first."""
        store.save(task_id="t1", topic="first", domain=None, result="r1")
        store.save(task_id="t2", topic="second", domain=None, result="r2")
        store.save(task_id="t3", topic="third", domain=None, result="r3")
        rows = store.list_recent(limit=10)
        assert len(rows) == 3
        # created_at is ISO 8601 — lexicographic sort = chronological sort
        assert rows[0]["task_id"] == "t3"
        assert rows[2]["task_id"] == "t1"

    def test_list_recent_respects_limit(self, store):
        """list_recent() respects the limit parameter."""
        for i in range(5):
            store.save(task_id=f"t{i}", topic=f"topic {i}", domain=None, result="r")
        rows = store.list_recent(limit=3)
        assert len(rows) == 3

    def test_save_replace_on_duplicate_id(self, store):
        """Saving the same task_id twice updates the record."""
        store.save(task_id="dup", topic="original", domain=None, result="first")
        store.save(task_id="dup", topic="updated", domain=None, result="second")
        row = store.get("dup")
        assert row["result"] == "second"
        assert row["topic"] == "updated"

    def test_creates_parent_directory(self, tmp_path):
        """SQLiteResultStore creates missing parent directories."""
        from src.services.sqlite_store import SQLiteResultStore

        deep_path = tmp_path / "nested" / "dirs" / "results.db"
        store = SQLiteResultStore(db_path=str(deep_path))
        store.save(task_id="x", topic="t", domain=None, result="r")
        assert deep_path.exists()

    def test_history_endpoint_returns_runs(self):
        """GET /crew/history returns RunHistoryResponse with runs list."""
        from unittest.mock import patch
        from fastapi.testclient import TestClient

        with tempfile.TemporaryDirectory() as tmpdir:
            from src.services.sqlite_store import SQLiteResultStore

            test_store = SQLiteResultStore(db_path=f"{tmpdir}/test.db")
            test_store.save(
                task_id="hist-1",
                topic="test topic",
                domain=None,
                result="test result",
                duration_seconds=10.0,
            )

            with patch("src.middleware.auth.settings") as auth_mock, \
                 patch("src.main.sqlite_store", test_store):
                auth_mock.api_key = None
                from src.main import app
                client = TestClient(app)
                resp = client.get("/crew/history")

            assert resp.status_code == 200
            body = resp.json()
            assert "runs" in body
            assert "count" in body

    def test_agent_events_save_and_replay(self, store):
        """Slice-27: state bus persists to agent_events; replay returns
        rows in chronological order for the share page."""
        store.save_event(
            task_id="e-1",
            agent_role="researcher",
            state="active",
            detail="started",
            ts="2026-04-16T10:00:00+00:00",
        )
        store.save_event(
            task_id="e-1",
            agent_role="researcher",
            state="completed",
            detail="done",
            ts="2026-04-16T10:00:05+00:00",
        )
        store.save_event(
            task_id="other",
            agent_role="writer",
            state="active",
            detail="",
            ts="2026-04-16T10:00:02+00:00",
        )

        events = store.replay_events("e-1")
        assert [e["state"] for e in events] == ["active", "completed"]
        assert all(e["task_id"] == "e-1" for e in events)
        assert store.replay_events("no-such-task") == []
