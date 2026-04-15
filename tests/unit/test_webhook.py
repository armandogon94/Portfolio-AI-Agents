"""Unit tests for webhook callback feature (slice-18)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestWebhookDelivery:
    @pytest.mark.asyncio
    async def test_webhook_posts_payload(self):
        """_deliver_webhook POSTs the correct payload to the URL."""
        mock_response = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.main.httpx.AsyncClient", return_value=mock_client):
            from src.main import _deliver_webhook

            await _deliver_webhook(
                "https://example.com/webhook",
                {"task_id": "abc", "status": "completed", "result": "done"},
            )

        mock_client.post.assert_called_once_with(
            "https://example.com/webhook",
            json={"task_id": "abc", "status": "completed", "result": "done"},
        )

    @pytest.mark.asyncio
    async def test_webhook_failure_does_not_raise(self):
        """Webhook delivery failure logs a warning but does not raise."""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        with patch("src.main.httpx.AsyncClient", return_value=mock_client):
            from src.main import _deliver_webhook

            # Should not raise
            await _deliver_webhook("https://example.com/webhook", {"task_id": "x"})

    @pytest.mark.asyncio
    async def test_webhook_timeout_does_not_raise(self):
        """Webhook timeout does not raise or affect task status."""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch("src.main.httpx.AsyncClient", return_value=mock_client):
            from src.main import _deliver_webhook

            await _deliver_webhook("https://example.com/webhook", {"task_id": "x"})


@pytest.mark.unit
class TestWebhookValidation:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        with patch("src.middleware.auth.settings") as auth_mock:
            auth_mock.api_key = None
            from src.main import app

            return TestClient(app)

    def test_crew_run_without_webhook_still_works(self, client):
        """POST /crew/run without webhook_url returns 202 as before."""
        resp = client.post("/crew/run", json={"topic": "test"})
        assert resp.status_code == 202

    def test_crew_run_with_valid_https_webhook(self, client):
        """POST /crew/run with a valid https webhook_url is accepted."""
        resp = client.post(
            "/crew/run",
            json={"topic": "test", "webhook_url": "https://hooks.example.com/callback"},
        )
        assert resp.status_code == 202

    def test_crew_run_with_private_ip_webhook_rejected(self, client):
        """POST /crew/run with private IP webhook_url is rejected (SSRF)."""
        resp = client.post(
            "/crew/run",
            json={"topic": "test", "webhook_url": "http://192.168.1.1/hook"},
        )
        assert resp.status_code == 422

    def test_crew_run_with_file_scheme_webhook_rejected(self, client):
        """POST /crew/run with file:// webhook_url is rejected."""
        resp = client.post(
            "/crew/run",
            json={"topic": "test", "webhook_url": "file:///etc/passwd"},
        )
        assert resp.status_code == 422


@pytest.mark.unit
class TestWebhookStoredInTaskStore:
    def test_task_store_create_stores_webhook_url(self):
        """TaskStore.create() stores webhook_url in the task dict."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(
            topic="test", domain=None, webhook_url="https://example.com/hook"
        )
        task = store.get(task_id)
        assert task["webhook_url"] == "https://example.com/hook"

    def test_task_store_create_stores_none_webhook(self):
        """TaskStore.create() stores None webhook_url when not provided."""
        from src.services.task_store import TaskStore

        store = TaskStore()
        task_id = store.create(topic="test", domain=None)
        task = store.get(task_id)
        assert task["webhook_url"] is None
