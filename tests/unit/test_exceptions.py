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
class TestInputValidation:
    """Input schema max_length constraints prevent resource exhaustion."""

    def test_crew_request_topic_max_length(self):
        """CrewRequest.topic rejects strings over 500 characters."""
        from src.models.schemas import CrewRequest
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            CrewRequest(topic="x" * 501)

    def test_ingest_request_content_max_length(self):
        """IngestRequest.content rejects strings over 100_000 characters."""
        from src.models.schemas import IngestRequest
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            IngestRequest(doc_id="d1", content="x" * 100_001)

    def test_ingest_request_doc_id_max_length(self):
        """IngestRequest.doc_id rejects strings over 255 characters."""
        from src.models.schemas import IngestRequest
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            IngestRequest(doc_id="x" * 256, content="hello")

    def test_crew_request_accepts_valid_topic(self):
        """CrewRequest accepts a topic within limits."""
        from src.models.schemas import CrewRequest

        req = CrewRequest(topic="AI in healthcare")
        assert req.topic == "AI in healthcare"


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
        from src.dependencies import get_qdrant_repo
        from unittest.mock import MagicMock

        mock_repo = MagicMock()
        app.dependency_overrides[get_qdrant_repo] = lambda: mock_repo
        client = TestClient(app, raise_server_exceptions=False)
        yield client, mock_repo
        app.dependency_overrides.clear()

    def test_not_found_returns_404_json(self, client):
        """NotFoundError returns 404 with ErrorResponse body (via /crew/status)."""
        c, _ = client
        resp = c.get("/crew/status/nonexistent-task-id")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "NotFoundError"
        assert body["status_code"] == 404

    def test_service_unavailable_returns_503_json(self, client):
        """ServiceUnavailableError returns 503 with ErrorResponse body."""
        from src.exceptions import ServiceUnavailableError

        c, mock_repo = client
        mock_repo.search.side_effect = ServiceUnavailableError("Qdrant unreachable")
        with patch("src.middleware.auth.settings") as auth_s:
            auth_s.api_key = None
            resp = c.post("/documents/search", json={"query": "test"})

        assert resp.status_code == 503
        body = resp.json()
        assert body["error"] == "ServiceUnavailableError"
        assert body["status_code"] == 503

    def test_crew_execution_error_returns_500_json(self, client):
        """CrewExecutionError returns 500 with structured error body."""
        from src.exceptions import CrewExecutionError

        c, mock_repo = client
        mock_repo.add.side_effect = CrewExecutionError("agent loop failed")
        with patch("src.middleware.auth.settings") as auth_s:
            auth_s.api_key = None
            resp = c.post(
                "/documents/ingest",
                json={"doc_id": "d1", "content": "test"},
            )

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "CrewExecutionError"
        assert body["detail"] == "agent loop failed"

    def test_unhandled_exception_returns_500_json(self, client):
        """An unexpected exception still returns structured ErrorResponse."""
        c, mock_repo = client
        mock_repo.search.side_effect = RuntimeError("unexpected")
        with patch("src.middleware.auth.settings") as auth_s:
            auth_s.api_key = None
            resp = c.post("/documents/search", json={"query": "test"})

        assert resp.status_code == 500
        body = resp.json()
        assert body["error"] == "InternalError"
        assert "status_code" in body
