import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestAsyncCrew:
    """Async crew execution endpoint tests. See DECISIONS.md DEC-02."""

    @pytest.fixture
    def client(self):
        from src.main import app

        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = None  # bypass auth
            client = TestClient(app, raise_server_exceptions=False)
            yield client

    def test_crew_run_returns_202_with_task_id(self, client):
        """POST /crew/run returns 202 Accepted with task_id."""
        resp = client.post("/crew/run", json={"topic": "test"})
        assert resp.status_code == 202
        body = resp.json()
        assert "task_id" in body
        assert body["status"] == "pending"

    def test_crew_status_returns_task_state(self, client):
        """GET /crew/status/{id} returns the current task state."""
        # Create a task first
        resp = client.post("/crew/run", json={"topic": "test"})
        task_id = resp.json()["task_id"]

        # Check status
        resp = client.get(f"/crew/status/{task_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == task_id
        assert body["status"] in ("pending", "running", "completed", "failed")

    def test_crew_status_not_found_returns_404(self, client):
        """GET /crew/status/{id} with unknown ID returns 404."""
        resp = client.get("/crew/status/nonexistent-id")
        assert resp.status_code == 404

    def test_crew_status_completed_has_result(self, client):
        """A completed task has a non-null result field."""
        with patch("src.main.task_store") as mock_store:
            mock_store.get.return_value = {
                "task_id": "abc",
                "topic": "test",
                "domain": None,
                "status": "completed",
                "result": "The analysis is complete.",
                "created_at": 1000000,
            }
            resp = client.get("/crew/status/abc")
            assert resp.status_code == 200
            assert resp.json()["result"] == "The analysis is complete."

    def test_crew_status_failed_has_error(self, client):
        """A failed task includes the error message in result."""
        with patch("src.main.task_store") as mock_store:
            mock_store.get.return_value = {
                "task_id": "abc",
                "topic": "test",
                "domain": None,
                "status": "failed",
                "result": "Task execution failed. Check logs for details.",
                "created_at": 1000000,
            }
            resp = client.get("/crew/status/abc")
            assert resp.status_code == 200
            assert resp.json()["status"] == "failed"

    def test_execute_crew_failure_does_not_leak_exception(self):
        """_execute_crew must not store raw str(e) — must use a sanitized message."""
        from src.main import _execute_crew, task_store

        task_id = task_store.create(topic="test", domain=None)

        with patch("src.crew.run_crew", side_effect=Exception("http://internal:11434/api key=sk-abc123")):
            _execute_crew(task_id, "test", None)

        task = task_store.get(task_id)
        assert task["status"] == "failed"
        # Must NOT contain the raw exception with internal URLs or keys
        assert "sk-abc123" not in task["result"]
        assert "internal" not in task["result"]
        assert "Check logs" in task["result"]
