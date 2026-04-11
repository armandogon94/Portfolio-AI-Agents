import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.mark.unit
class TestErrorResponseSchema:
    def test_error_response_has_required_fields(self):
        """ErrorResponse schema has error, detail, and status_code fields."""
        from src.models.schemas import ErrorResponse

        resp = ErrorResponse(error="NotFoundError", detail="not found", status_code=404)
        assert resp.error == "NotFoundError"
        assert resp.detail == "not found"
        assert resp.status_code == 404


@pytest.mark.unit
class TestExceptionHierarchy:
    def test_app_error_has_status_code_and_message(self):
        """AppError stores status_code and message."""
        from src.exceptions import AppError

        err = AppError("something broke", status_code=500)
        assert str(err) == "something broke"
        assert err.status_code == 500

    def test_not_found_error_defaults_to_404(self):
        """NotFoundError defaults to 404."""
        from src.exceptions import NotFoundError

        err = NotFoundError("missing item")
        assert err.status_code == 404

    def test_service_unavailable_defaults_to_503(self):
        """ServiceUnavailableError defaults to 503."""
        from src.exceptions import ServiceUnavailableError

        err = ServiceUnavailableError("Qdrant is down")
        assert err.status_code == 503

    def test_crew_execution_error_defaults_to_500(self):
        """CrewExecutionError defaults to 500."""
        from src.exceptions import CrewExecutionError

        err = CrewExecutionError("crew failed")
        assert err.status_code == 500

    def test_validation_error_defaults_to_422(self):
        """ValidationError defaults to 422."""
        from src.exceptions import ValidationError

        err = ValidationError("bad input")
        assert err.status_code == 422


@pytest.mark.unit
class TestExceptionHandlers:
    """Exception handlers return structured ErrorResponse JSON."""

    @pytest.fixture
    def client(self):
        from src.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_not_found_returns_404_json(self, client):
        """A NotFoundError raised in a handler returns 404 with ErrorResponse body."""
        from src.exceptions import NotFoundError

        with patch("src.crew.run_crew") as mock_run:
            mock_run.side_effect = NotFoundError("topic not found")
            resp = client.post("/crew/run", json={"topic": "test"})

        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "NotFoundError"
        assert body["detail"] == "topic not found"
        assert body["status_code"] == 404

    def test_service_unavailable_returns_503_json(self, client):
        """A ServiceUnavailableError returns 503 with ErrorResponse body."""
        from src.exceptions import ServiceUnavailableError

        with patch("src.crew.run_crew") as mock_run:
            mock_run.side_effect = ServiceUnavailableError("Qdrant unreachable")
            resp = client.post("/crew/run", json={"topic": "test"})

        assert resp.status_code == 503
        body = resp.json()
        assert body["error"] == "ServiceUnavailableError"
        assert body["status_code"] == 503

    def test_crew_execution_error_returns_500_json(self, client):
        """A CrewExecutionError returns 500 with structured error body."""
        from src.exceptions import CrewExecutionError

        with patch("src.crew.run_crew") as mock_run:
            mock_run.side_effect = CrewExecutionError("agent loop failed")
            resp = client.post("/crew/run", json={"topic": "test"})

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "CrewExecutionError"
        assert body["detail"] == "agent loop failed"

    def test_unhandled_exception_returns_500_json(self, client):
        """An unexpected exception still returns structured ErrorResponse."""
        with patch("src.crew.run_crew") as mock_run:
            mock_run.side_effect = RuntimeError("unexpected")
            resp = client.post("/crew/run", json={"topic": "test"})

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "InternalError"
        assert "status_code" in body
