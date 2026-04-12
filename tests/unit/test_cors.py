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
