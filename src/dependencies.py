"""FastAPI dependency providers.

See DECISIONS.md DEC-04 for rationale (Depends() over per-request instantiation).
"""

from fastapi import Request

from src.exceptions import ServiceUnavailableError
from src.repositories.qdrant_repo import QdrantRepository


def get_qdrant_repo(request: Request) -> QdrantRepository:
    """Retrieve the QdrantRepository singleton from app.state."""
    repo = request.app.state.qdrant_repo
    if repo is None:
        raise ServiceUnavailableError("Vector database is not available")
    return repo
