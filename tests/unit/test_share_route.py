"""GET /share/{token} tests (slice-27)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestShareRoute:
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

    def test_valid_token_returns_200_html(self, client):
        from src.main import sqlite_store, task_store
        from src.services.share_token import mint

        task_id = task_store.create(topic="shareable", domain=None)
        task_store.update(task_id, status="completed", result="The result body.")
        sqlite_store.save(
            task_id=task_id,
            topic="shareable",
            domain=None,
            result="The result body.",
            duration_seconds=1.0,
        )

        with patch("src.main.settings") as s:
            s.share_secret = "s3cret"
            token = mint(task_id, secret="s3cret", ttl_seconds=3600)
            resp = client.get(f"/share/{token}")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        body = resp.text
        assert "shareable" in body
        assert "The result body." in body

    def test_share_body_excludes_sensitive_fields(self, client):
        """Whitelist render — no webhook URLs, no API keys in the HTML."""
        from src.main import sqlite_store, task_store
        from src.services.share_token import mint

        task_id = task_store.create(
            topic="check redaction",
            domain=None,
            webhook_url="https://secret.example.com/hook?k=abc",
        )
        task_store.update(task_id, status="completed", result="done")
        sqlite_store.save(
            task_id=task_id,
            topic="check redaction",
            domain=None,
            result="done",
            duration_seconds=1.0,
        )

        with patch("src.main.settings") as s:
            s.share_secret = "s3cret"
            token = mint(task_id, secret="s3cret", ttl_seconds=3600)
            resp = client.get(f"/share/{token}")

        assert resp.status_code == 200
        body = resp.text
        assert "secret.example.com" not in body
        assert "webhook" not in body.lower()

    def test_invalid_token_returns_403(self, client):
        with patch("src.main.settings") as s:
            s.share_secret = "s3cret"
            resp = client.get("/share/not-a-valid-token")
        assert resp.status_code == 403

    def test_expired_token_returns_410(self, client):
        from src.main import task_store
        from src.services.share_token import mint

        task_id = task_store.create(topic="aged", domain=None)
        with patch("src.main.settings") as s:
            s.share_secret = "s3cret"
            token = mint(task_id, secret="s3cret", ttl_seconds=-1)
            resp = client.get(f"/share/{token}")
        assert resp.status_code == 410

    def test_unknown_task_id_returns_404(self, client):
        from src.services.share_token import mint

        with patch("src.main.settings") as s:
            s.share_secret = "s3cret"
            token = mint("nonexistent-task", secret="s3cret", ttl_seconds=3600)
            resp = client.get(f"/share/{token}")
        assert resp.status_code == 404
