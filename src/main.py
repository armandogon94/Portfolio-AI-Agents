import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config.settings import settings
from src.exceptions import AppError
from src.dependencies import get_qdrant_repo
from src.middleware.auth import ApiKeyMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.utils.logger import setup_logging
from src.models.schemas import (
    CrewRequest,
    CrewResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
)

setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter (DEC-03)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting AI Agent System | "
        f"LLM={settings.llm_provider.value} | "
        f"Embeddings={settings.embedding_mode.value} | "
        f"Env={settings.environment.value}"
    )
    # Initialize Qdrant singleton (DEC-04)
    try:
        from src.repositories.qdrant_repo import QdrantRepository

        app.state.qdrant_repo = QdrantRepository()
        logger.info("Qdrant repository initialized")
    except Exception as e:
        logger.warning(f"Qdrant not available at startup: {e}")
        app.state.qdrant_repo = None
    yield
    logger.info("Shutting down AI Agent System")


app = FastAPI(
    title="AI Agent System",
    description="Multi-agent system with CrewAI, RAG, and industry-specific analysis",
    version="2.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception Handlers (DEC-05) ---


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalError",
            "detail": "An unexpected error occurred",
            "status_code": 500,
        },
    )


# --- Routes ---


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        llm_provider=settings.llm_provider.value,
        embedding_mode=settings.embedding_mode.value,
        environment=settings.environment.value,
    )


@app.post("/crew/run", response_model=CrewResponse)
@limiter.limit("5/minute")
async def run_crew(request: Request, body: CrewRequest):
    """Execute the multi-agent crew on a topic."""
    from src.crew import run_crew

    logger.info(f"Running crew: topic='{body.topic}', domain={body.domain}")
    result = run_crew(topic=body.topic, domain=body.domain)
    return CrewResponse(topic=body.topic, domain=body.domain, result=result)


@app.post("/documents/ingest", response_model=IngestResponse)
@limiter.limit("30/minute")
async def ingest_document(
    request: Request,
    body: IngestRequest,
    repo=Depends(get_qdrant_repo),
):
    """Add a document to the RAG knowledge base."""
    repo.add(doc_id=body.doc_id, content=body.content, metadata=body.metadata)
    return IngestResponse(doc_id=body.doc_id)


@app.post("/documents/search", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_documents(
    request: Request,
    body: SearchRequest,
    repo=Depends(get_qdrant_repo),
):
    """Search the RAG knowledge base."""
    docs = repo.search(query=body.query, limit=body.limit)
    results = [
        {"doc_id": d.id, "content": d.content[:500], "score": d.score, "metadata": d.metadata}
        for d in docs
    ]
    return SearchResponse(query=body.query, results=results, count=len(results))
