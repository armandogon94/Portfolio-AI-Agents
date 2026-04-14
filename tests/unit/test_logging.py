import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestLogFormat:
    def test_json_log_format_in_production(self):
        """In production, setup_logging uses JSON formatter."""
        from pythonjsonlogger.json import JsonFormatter
        from unittest.mock import patch, MagicMock

        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.environment.value = "production"

        root = logging.getLogger()
        original_handlers = root.handlers[:]
        root.handlers.clear()

        try:
            with patch("src.utils.logger.settings", mock_settings):
                from src.utils.logger import setup_logging

                setup_logging()

                assert len(root.handlers) > 0
                handler = root.handlers[-1]
                assert isinstance(handler.formatter, JsonFormatter)

                record = logging.LogRecord(
                    name="test", level=logging.INFO, pathname="", lineno=0,
                    msg="test message", args=(), exc_info=None,
                )
                output = handler.formatter.format(record)
                parsed = json.loads(output)
                assert parsed["message"] == "test message"
        finally:
            root.handlers = original_handlers

    def test_human_format_in_development(self):
        """In development, logs use human-readable format (not JSON)."""
        from unittest.mock import patch, MagicMock

        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.environment.value = "development"

        root = logging.getLogger()
        original_handlers = root.handlers[:]
        root.handlers.clear()

        try:
            with patch("src.utils.logger.settings", mock_settings):
                from src.utils.logger import setup_logging

                setup_logging()

                handler = root.handlers[-1]
                record = logging.LogRecord(
                    name="test", level=logging.INFO, pathname="", lineno=0,
                    msg="hello world", args=(), exc_info=None,
                )
                output = handler.formatter.format(record)
                with pytest.raises(json.JSONDecodeError):
                    json.loads(output)
                assert "hello world" in output
        finally:
            root.handlers = original_handlers


@pytest.mark.unit
class TestRequestIdMiddleware:
    @pytest.fixture
    def client(self):
        from src.main import app

        return TestClient(app)

    def test_request_id_in_response_header(self, client):
        """Every response includes X-Request-ID header."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers

    def test_request_id_is_valid_uuid(self, client):
        """X-Request-ID header value is a valid UUID4."""
        resp = client.get("/health")
        request_id = resp.headers.get("x-request-id")
        assert request_id is not None
        parsed = uuid.UUID(request_id, version=4)
        assert str(parsed) == request_id

    def test_request_id_unique_per_request(self, client):
        """Each request gets a distinct request ID."""
        resp1 = client.get("/health")
        resp2 = client.get("/health")
        id1 = resp1.headers.get("x-request-id")
        id2 = resp2.headers.get("x-request-id")
        assert id1 != id2


@pytest.mark.unit
class TestSecurityHeaders:
    """Security response headers are present on every response."""

    @pytest.fixture
    def client(self):
        from src.main import app
        return TestClient(app)

    def test_x_content_type_options_header(self, client):
        """X-Content-Type-Options: nosniff prevents MIME-type sniffing."""
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_header(self, client):
        """X-Frame-Options: DENY prevents clickjacking."""
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection_header(self, client):
        """X-XSS-Protection header enables browser XSS filter."""
        resp = client.get("/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"

    def test_content_security_policy_header(self, client):
        """Content-Security-Policy: default-src 'none' — restricts resource loading for API responses."""
        resp = client.get("/health")
        assert resp.headers.get("content-security-policy") == "default-src 'none'"
