import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestRateLimiting:
    """Rate limiting tests. See DECISIONS.md DEC-03."""

    @pytest.fixture
    def client(self):
        from src.main import app
        from src.dependencies import get_qdrant_repo

        mock_repo = MagicMock()
        mock_repo.search.return_value = []
        app.dependency_overrides[get_qdrant_repo] = lambda: mock_repo
        client = TestClient(app, raise_server_exceptions=False)
        yield client
        app.dependency_overrides.clear()

    def test_rate_limit_crew_run_returns_429(self, client):
        """/crew/run returns 429 after exceeding rate limit."""
        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = None  # bypass auth for this test
            with patch("src.crew.run_crew", return_value="result"):
                for _ in range(5):
                    client.post("/crew/run", json={"topic": "test"})

                resp = client.post("/crew/run", json={"topic": "test"})
                assert resp.status_code == 429

    def test_rate_limit_health_no_limit(self, client):
        """/health endpoint is not rate limited."""
        for _ in range(20):
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_rate_limit_429_has_error_body(self, client):
        """429 response includes an error message."""
        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = None
            with patch("src.crew.run_crew", return_value="result"):
                for _ in range(5):
                    client.post("/crew/run", json={"topic": "test"})

                resp = client.post("/crew/run", json={"topic": "test"})
                assert resp.status_code == 429
                body = resp.json()
                assert "error" in body
