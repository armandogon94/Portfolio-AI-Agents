from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class DocumentRepository(ABC):
    """Abstract interface for document storage and retrieval."""

    @abstractmethod
    def add(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        """Add a document to the store."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[Document]:
        """Search documents by semantic similarity."""

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""

    @abstractmethod
    def ensure_collection(self) -> None:
        """Ensure the backing collection/table exists."""
