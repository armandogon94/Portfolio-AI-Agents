"""HTTP contract tests for the workflow registry wiring (slice-21)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestWorkflowsEndpoint:
    @pytest.fixture
    def client(self):
        from src.main import app, limiter

        limiter._storage.reset()
        # Patch out the actual crew execution so background tasks finish instantly
        # and don't try to reach Ollama during unit tests.
        with (
            patch("src.middleware.auth.settings") as auth_settings,
            patch("src.main._execute_crew") as mock_execute,
        ):
            auth_settings.api_key = None
            mock_execute.return_value = None
            yield TestClient(app, raise_server_exceptions=False)

    def test_list_workflows_returns_research_report(self, client):
        resp = client.get("/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        names = [w["name"] for w in data]
        assert "research_report" in names

    def test_list_workflows_shape_is_workflowinfo(self, client):
        resp = client.get("/workflows")
        data = resp.json()
        entry = next(w for w in data if w["name"] == "research_report")
        for field in ("name", "description", "process", "agent_roles", "task_names"):
            assert field in entry
        assert entry["process"] == "sequential"
        assert entry["agent_roles"] == ["researcher", "analyst", "writer", "validator"]

    def test_crew_run_default_workflow_still_202s(self, client):
        resp = client.post("/crew/run", json={"topic": "test-default"})
        assert resp.status_code == 202

    def test_crew_run_explicit_workflow_research_report_accepted(self, client):
        resp = client.post(
            "/crew/run",
            json={"topic": "test-explicit", "workflow": "research_report"},
        )
        assert resp.status_code == 202

    def test_crew_run_unknown_workflow_returns_422(self, client):
        resp = client.post(
            "/crew/run",
            json={"topic": "test-unknown", "workflow": "no_such_workflow"},
        )
        assert resp.status_code == 422
