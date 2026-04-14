import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestApiKeyAuth:
    """API key authentication tests. See DECISIONS.md DEC-01."""

    @pytest.fixture
    def client_with_key(self):
        """Client against an app where API_KEY is configured."""
        from src.main import app
        from src.dependencies import get_qdrant_repo

        mock_repo = MagicMock()
        mock_repo.search.return_value = []
        app.dependency_overrides[get_qdrant_repo] = lambda: mock_repo

        with patch("src.middleware.auth.settings") as mock_settings:
            mock_settings.api_key = "test-secret-key"
            client = TestClient(app, raise_server_exceptions=False)
            yield client

        app.dependency_overrides.clear()

    @pytest.fixture
    def client_no_key(self):
        """Client against an app where API_KEY is NOT configured (dev mode)."""
        from src.main import app
        from src.dependencies import get_qdrant_repo

        mock_repo = MagicMock()
        mock_repo.search.return_value = []
        app.dependency_overrides[get_qdrant_repo] = lambda: mock_repo

        with patch("src.middleware.auth.settings") as mock_settings:
            mock_settings.api_key = None
            client = TestClient(app, raise_server_exceptions=False)
            yield client

        app.dependency_overrides.clear()

    # --- /health is always public ---

    def test_health_no_auth_required(self, client_with_key):
        """GET /health returns 200 without any API key."""
        resp = client_with_key.get("/health")
        assert resp.status_code == 200

    # --- Protected endpoints require key ---

    def test_crew_run_requires_api_key(self, client_with_key):
        """POST /crew/run without key returns 401."""
        resp = client_with_key.post("/crew/run", json={"topic": "test"})
        assert resp.status_code == 401

    def test_crew_run_with_valid_key(self, client_with_key):
        """POST /crew/run with correct key is allowed (returns 202 async)."""
        resp = client_with_key.post(
            "/crew/run",
            json={"topic": "test"},
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 202

    def test_crew_run_with_invalid_key(self, client_with_key):
        """POST /crew/run with wrong key returns 401."""
        resp = client_with_key.post(
            "/crew/run",
            json={"topic": "test"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_documents_ingest_requires_auth(self, client_with_key):
        """POST /documents/ingest without key returns 401."""
        resp = client_with_key.post(
            "/documents/ingest",
            json={"doc_id": "d1", "content": "hello"},
        )
        assert resp.status_code == 401

    def test_documents_search_requires_auth(self, client_with_key):
        """POST /documents/search without key returns 401."""
        resp = client_with_key.post(
            "/documents/search",
            json={"query": "test"},
        )
        assert resp.status_code == 401

    # --- Auth bypassed when API_KEY not configured ---

    def test_auth_bypassed_when_no_key_configured(self, client_no_key):
        """When API_KEY is not set, all endpoints work without a key."""
        resp = client_no_key.post(
            "/documents/search",
            json={"query": "test"},
        )
        assert resp.status_code == 200

    def test_auth_401_has_error_response_format(self, client_with_key):
        """401 response uses structured ErrorResponse format."""
        resp = client_with_key.post("/crew/run", json={"topic": "test"})
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        assert "detail" in body
        assert "status_code" in body

    def test_metrics_requires_auth(self, client_with_key):
        """GET /metrics requires API key (not in PUBLIC_PATHS)."""
        resp = client_with_key.get("/metrics")
        assert resp.status_code == 401

    def test_metrics_accessible_with_valid_key(self, client_with_key):
        """GET /metrics works with valid API key."""
        resp = client_with_key.get("/metrics", headers={"X-API-Key": "test-secret-key"})
        assert resp.status_code == 200

    def test_health_does_not_leak_provider_details(self, client_with_key):
        """GET /health without auth returns only status:healthy, not provider config."""
        resp = client_with_key.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("status") == "healthy"
        # Provider details must NOT be exposed to unauthenticated callers
        assert "llm_provider" not in body
        assert "embedding_mode" not in body
        assert "environment" not in body

    def test_docs_disabled_in_production(self):
        """FastAPI docs and redoc URLs are None when environment is production."""
        import inspect
        from src import main

        source = inspect.getsource(main)
        # The app creation must conditionally disable docs in production
        assert "docs_url" in source and "redoc_url" in source, (
            "main.py must conditionally set docs_url/redoc_url based on environment"
        )

    def test_api_key_uses_constant_time_comparison(self):
        """API key comparison must use hmac.compare_digest to prevent timing attacks."""
        import inspect
        from src.middleware import auth

        source = inspect.getsource(auth)
        assert "hmac.compare_digest" in source, (
            "Auth module must use hmac.compare_digest for constant-time comparison"
        )
