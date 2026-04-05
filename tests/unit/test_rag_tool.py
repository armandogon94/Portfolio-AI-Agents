import pytest
from unittest.mock import patch, MagicMock
from src.repositories.base import Document, DocumentRepository


@pytest.mark.unit
class TestDocumentModel:
    def test_document_creation(self):
        doc = Document(id="test-1", content="Hello world", score=0.95)
        assert doc.id == "test-1"
        assert doc.content == "Hello world"
        assert doc.score == 0.95
        assert doc.metadata == {}

    def test_document_with_metadata(self):
        doc = Document(
            id="test-2",
            content="Test content",
            metadata={"source": "web", "date": "2024-01-01"},
        )
        assert doc.metadata["source"] == "web"


@pytest.mark.unit
class TestToolRegistry:
    def test_register_and_get(self):
        from src.tools.registry import ToolRegistry

        # The search and rag tools are registered on import
        import src.tools.search  # noqa: F401

        tool = ToolRegistry.get("web_search")
        assert tool is not None
        assert tool.name == "Web Search"

    def test_get_unknown_tool_raises(self):
        from src.tools.registry import ToolRegistry

        with pytest.raises(KeyError, match="not registered"):
            ToolRegistry.get("nonexistent_tool")

    def test_get_all_tools(self):
        from src.tools.registry import ToolRegistry

        # Ensure tools are imported
        import src.tools.search  # noqa: F401

        all_tools = ToolRegistry.get_all()
        assert "web_search" in all_tools


@pytest.mark.unit
class TestSchemas:
    def test_crew_request(self):
        from src.models.schemas import CrewRequest

        req = CrewRequest(topic="AI in healthcare", domain="healthcare")
        assert req.topic == "AI in healthcare"
        assert req.domain == "healthcare"

    def test_crew_request_no_domain(self):
        from src.models.schemas import CrewRequest

        req = CrewRequest(topic="General research")
        assert req.domain is None

    def test_health_response(self):
        from src.models.schemas import HealthResponse

        resp = HealthResponse(
            llm_provider="ollama",
            embedding_mode="local",
            environment="development",
        )
        assert resp.status == "healthy"
