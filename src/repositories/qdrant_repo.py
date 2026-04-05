import hashlib
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config.settings import settings
from src.llm.embeddings import EmbeddingFactory
from src.repositories.base import Document, DocumentRepository

logger = logging.getLogger(__name__)


def _stable_id(doc_id: str) -> int:
    """Convert string ID to a stable positive integer for Qdrant."""
    return int(hashlib.sha256(doc_id.encode()).hexdigest()[:15], 16)


class QdrantRepository(DocumentRepository):
    """Qdrant-backed document repository."""

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name or settings.qdrant_collection
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.embedder = EmbeddingFactory.create()
        self.ensure_collection()

    def ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        embedding = self.embedder.embed_query(content)
        payload = {"content": content, "doc_id": doc_id, **(metadata or {})}
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=_stable_id(doc_id),
                    vector=embedding,
                    payload=payload,
                )
            ],
        )
        logger.debug(f"Added document: {doc_id}")

    def search(self, query: str, limit: int = 5) -> list[Document]:
        query_vector = self.embedder.embed_query(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        return [
            Document(
                id=hit.payload.get("doc_id", str(hit.id)),
                content=hit.payload.get("content", ""),
                metadata={k: v for k, v in hit.payload.items() if k not in ("content", "doc_id")},
                score=hit.score,
            )
            for hit in results
        ]

    def delete(self, doc_id: str) -> bool:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[_stable_id(doc_id)],
        )
        logger.debug(f"Deleted document: {doc_id}")
        return True
