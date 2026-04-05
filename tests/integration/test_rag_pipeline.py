import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestRAGPipeline:
    def test_qdrant_repo_add_and_search(self):
        """Test adding and searching documents in Qdrant (mocked client)."""
        with patch("src.repositories.qdrant_repo.QdrantClient") as MockClient:
            with patch("src.repositories.qdrant_repo.EmbeddingFactory") as MockEmbedFactory:
                # Setup mocks
                mock_embedder = MagicMock()
                mock_embedder.dimension = 384
                mock_embedder.embed_query.return_value = [0.1] * 384
                MockEmbedFactory.create.return_value = mock_embedder

                mock_client = MagicMock()
                mock_client.get_collections.return_value.collections = []
                MockClient.return_value = mock_client

                from src.repositories.qdrant_repo import QdrantRepository

                repo = QdrantRepository(collection_name="test_collection")

                # Test add
                repo.add(doc_id="test-1", content="AI is transforming healthcare")
                mock_client.upsert.assert_called_once()

                # Test search
                mock_hit = MagicMock()
                mock_hit.payload = {"doc_id": "test-1", "content": "AI is transforming healthcare"}
                mock_hit.score = 0.95
                mock_hit.id = 12345
                mock_client.search.return_value = [mock_hit]

                results = repo.search("healthcare AI")
                assert len(results) == 1
                assert results[0].id == "test-1"
                assert results[0].score == 0.95

    def test_qdrant_repo_delete(self):
        """Test deleting a document from Qdrant."""
        with patch("src.repositories.qdrant_repo.QdrantClient") as MockClient:
            with patch("src.repositories.qdrant_repo.EmbeddingFactory") as MockEmbedFactory:
                mock_embedder = MagicMock()
                mock_embedder.dimension = 384
                MockEmbedFactory.create.return_value = mock_embedder

                mock_client = MagicMock()
                mock_client.get_collections.return_value.collections = []
                MockClient.return_value = mock_client

                from src.repositories.qdrant_repo import QdrantRepository

                repo = QdrantRepository(collection_name="test_collection")

                result = repo.delete("test-1")
                assert result is True
                mock_client.delete.assert_called_once()
