"""PDF export tests (slice-27, DEC-23)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestPdfExport:
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

    def test_pdf_bytes_have_valid_magic_header(self):
        from src.services.pdf_export import render_run_pdf

        pdf_bytes = render_run_pdf(
            task_id="t-123",
            topic="Test topic",
            domain="general",
            result="Body text here.",
            events=[],
        )
        # PDF files start with '%PDF-'.
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 500

    def test_pdf_endpoint_returns_application_pdf(self, client):
        from src.main import sqlite_store, task_store

        task_id = task_store.create(topic="for-pdf", domain=None)
        task_store.update(task_id, status="completed", result="done")
        sqlite_store.save(
            task_id=task_id,
            topic="for-pdf",
            domain=None,
            result="done",
            duration_seconds=1.0,
        )

        resp = client.get(f"/crew/history/{task_id}/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")
        assert resp.content[:5] == b"%PDF-"

    def test_pdf_endpoint_requires_api_key_when_configured(self):
        from src.main import app, limiter, sqlite_store, task_store

        limiter._storage.reset()
        task_id = task_store.create(topic="for-pdf-auth", domain=None)
        task_store.update(task_id, status="completed", result="done")
        sqlite_store.save(
            task_id=task_id,
            topic="for-pdf-auth",
            domain=None,
            result="done",
            duration_seconds=1.0,
        )

        with (
            patch("src.middleware.auth.settings") as auth_settings,
            patch("src.main._execute_crew") as mock_execute,
        ):
            auth_settings.api_key = "secret-key"
            mock_execute.return_value = None
            c = TestClient(app, raise_server_exceptions=False)
            resp_noauth = c.get(f"/crew/history/{task_id}/pdf")
            assert resp_noauth.status_code == 401

            resp_ok = c.get(
                f"/crew/history/{task_id}/pdf",
                headers={"X-API-Key": "secret-key"},
            )
            assert resp_ok.status_code == 200
            assert resp_ok.content[:5] == b"%PDF-"
