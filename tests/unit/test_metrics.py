import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestMetricsEndpoint:
    """Metrics endpoint tests. See DECISIONS.md DEC-07."""

    @pytest.fixture
    def client(self):
        from src.main import app

        with patch("src.middleware.auth.settings") as auth_settings:
            auth_settings.api_key = "test-key"
            client = TestClient(app, raise_server_exceptions=False)
            yield client

    AUTH = {"X-API-Key": "test-key"}

    def test_metrics_endpoint_returns_json(self, client):
        """GET /metrics returns JSON with expected fields."""
        resp = client.get("/metrics", headers=self.AUTH)
        assert resp.status_code == 200
        body = resp.json()
        assert "total_requests" in body
        assert "error_count" in body
        assert "uptime_seconds" in body
        assert "endpoints" in body

    def test_metrics_counts_requests(self, client):
        """After N requests, total_requests >= N."""
        for _ in range(3):
            client.get("/health")

        resp = client.get("/metrics", headers=self.AUTH)
        body = resp.json()
        # At least the 3 /health requests (plus /metrics itself)
        assert body["total_requests"] >= 3

    def test_metrics_tracks_errors(self, client):
        """Error responses increment error_count."""
        # Hit a non-existent task to trigger 404 (needs auth)
        client.get("/crew/status/nonexistent", headers=self.AUTH)

        resp = client.get("/metrics", headers=self.AUTH)
        body = resp.json()
        assert body["error_count"] >= 1

    def test_metrics_uptime_positive(self, client):
        """uptime_seconds is a positive number."""
        resp = client.get("/metrics", headers=self.AUTH)
        body = resp.json()
        assert body["uptime_seconds"] >= 0

    def test_metrics_endpoints_is_dict(self, client):
        """endpoints field is a dict mapping path to counts."""
        client.get("/health")
        resp = client.get("/metrics", headers=self.AUTH)
        body = resp.json()
        assert isinstance(body["endpoints"], dict)

    def test_metrics_records_even_when_handler_raises(self):
        """MetricsMiddleware records a request even when call_next raises an exception."""
        from src.middleware.metrics import MetricsMiddleware
        from src.services.metrics import MetricsCollector
        import asyncio

        collector = MetricsCollector()
        middleware = MetricsMiddleware(app=None, collector=collector)

        async def boom(_request):
            raise RuntimeError("handler exploded")

        class FakeRequest:
            url = type("URL", (), {"path": "/boom"})()

        async def run():
            try:
                await middleware.dispatch(FakeRequest(), boom)
            except RuntimeError:
                pass  # expected

        asyncio.run(run())
        snapshot = collector.snapshot()
        assert snapshot["total_requests"] >= 1
