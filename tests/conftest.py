import os
import pytest
from unittest.mock import Mock

# Force local/test settings before importing anything
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("EMBEDDING_MODE", "local")
os.environ.setdefault("ENVIRONMENT", "development")


@pytest.fixture
def mock_llm():
    """Mock CrewAI LLM for unit tests."""
    llm = Mock()
    llm.call.return_value = "Mocked LLM response"
    return llm


@pytest.fixture
def mock_embedder():
    """Mock embedder returning fixed-dimension vectors."""
    embedder = Mock()
    embedder.dimension = 384
    embedder.embed_query.return_value = [0.1] * 384
    embedder.embed_documents.return_value = [[0.1] * 384]
    embedder.embed.return_value = [[0.1] * 384]
    return embedder


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {"doc_id": "doc-1", "content": "Artificial intelligence is transforming healthcare."},
        {"doc_id": "doc-2", "content": "Machine learning models require large datasets."},
        {"doc_id": "doc-3", "content": "Natural language processing enables chatbots."},
    ]
