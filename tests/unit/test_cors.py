import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestCors:
    """CORS configuration tests. See DECISIONS.md DEC-06."""

    def test_cors_allows_all_in_dev(self):
        """With default CORS_ORIGINS=["*"], any origin gets CORS headers."""
        with patch("src.config.settings.Settings") as _:
            from src.main import app

            client = TestClient(app)
            resp = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert resp.headers.get("access-control-allow-origin") in (
                "*",
                "http://localhost:3000",
            )

    def test_cors_settings_has_cors_origins(self):
        """Settings model has cors_origins field with default ['*']."""
        from src.config.settings import Settings

        s = Settings()
        assert hasattr(s, "cors_origins")
        assert s.cors_origins == ["*"]

    def test_dashboard_origin_default_is_port_3061(self):
        """Slice-20b: Next.js dashboard talks to the API from port 3061."""
        from src.config.settings import Settings

        s = Settings()
        assert s.dashboard_origin == "http://localhost:3061"

    def test_build_cors_origins_appends_dashboard_when_not_wildcard(self):
        """When cors_origins is a specific list, dashboard_origin is added."""
        with patch("src.main.settings") as mock_settings:
            mock_settings.cors_origins = ["https://agents.305-ai.com"]
            mock_settings.dashboard_origin = "http://localhost:3061"
            from src.main import _build_cors_origins

            assert _build_cors_origins() == [
                "https://agents.305-ai.com",
                "http://localhost:3061",
            ]

    def test_build_cors_origins_wildcard_is_preserved(self):
        """Wildcard stays wildcard — the dashboard origin isn't redundantly appended."""
        with patch("src.main.settings") as mock_settings:
            mock_settings.cors_origins = ["*"]
            mock_settings.dashboard_origin = "http://localhost:3061"
            from src.main import _build_cors_origins

            assert _build_cors_origins() == ["*"]
