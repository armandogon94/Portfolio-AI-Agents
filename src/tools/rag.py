import logging
from crewai.tools import BaseTool
from src.tools.registry import register_tool

logger = logging.getLogger(__name__)

# Lazy-initialized repository (avoids connecting to Qdrant at import time)
_repo = None


def _get_repo():
    global _repo
    if _repo is None:
        from src.repositories.qdrant_repo import QdrantRepository

        _repo = QdrantRepository()
    return _repo


@register_tool("document_search")
class DocumentSearchTool(BaseTool):
    name: str = "Document Search"
    description: str = (
        "Search internal documents using semantic similarity. "
        "Use this to find relevant information from the knowledge base."
    )

    def _run(self, query: str) -> str:
        repo = _get_repo()
        results = repo.search(query, limit=5)

        if not results:
            return "No relevant documents found."

        output = []
        for doc in results:
            score = f"{doc.score:.2f}"
            output.append(f"[Score: {score}] {doc.content[:500]}")
        return "\n\n---\n\n".join(output)


@register_tool("document_ingest")
class DocumentIngestTool(BaseTool):
    name: str = "Document Ingest"
    description: str = "Add a document to the knowledge base for future retrieval."

    def _run(self, content: str, doc_id: str = "") -> str:
        if not doc_id:
            import hashlib

            doc_id = hashlib.md5(content[:200].encode()).hexdigest()[:12]

        repo = _get_repo()
        repo.add(doc_id=doc_id, content=content)
        return f"Document '{doc_id}' added to knowledge base."
