"""FastAPI dependency providers.

See DECISIONS.md DEC-04 for rationale (Depends() over per-request instantiation).
"""

from fastapi import Request

from src.repositories.qdrant_repo import QdrantRepository


def get_qdrant_repo(request: Request) -> QdrantRepository:
    """Retrieve the QdrantRepository singleton from app.state."""
    return request.app.state.qdrant_repo
