import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestQdrantDependency:
    """QdrantRepository is created once at startup and injected via Depends()."""

    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.search.return_value = []
        return repo

    @pytest.fixture
    def client(self, mock_repo):
        from src.main import app
        from src.dependencies import get_qdrant_repo

        app.dependency_overrides[get_qdrant_repo] = lambda: mock_repo
        client = TestClient(app, raise_server_exceptions=False)
        yield client
        app.dependency_overrides.clear()

    def test_qdrant_repo_available_via_depends(self, client, mock_repo):
        """Document search endpoint receives repo via DI — calls repo.search."""
        resp = client.post("/documents/search", json={"query": "test", "limit": 3})
        assert resp.status_code == 200
        mock_repo.search.assert_called_once()

    def test_qdrant_repo_ingest_via_depends(self, client, mock_repo):
        """Document ingest endpoint receives repo via DI — calls repo.add."""
        resp = client.post(
            "/documents/ingest",
            json={"doc_id": "d1", "content": "hello world"},
        )
        assert resp.status_code == 200
        mock_repo.add.assert_called_once()
