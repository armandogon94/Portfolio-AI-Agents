import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.exceptions import AppError
from src.dependencies import get_qdrant_repo
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

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def run_crew(request: CrewRequest):
    """Execute the multi-agent crew on a topic."""
    from src.crew import run_crew

    logger.info(f"Running crew: topic='{request.topic}', domain={request.domain}")
    result = run_crew(topic=request.topic, domain=request.domain)
    return CrewResponse(topic=request.topic, domain=request.domain, result=result)


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    repo=Depends(get_qdrant_repo),
):
    """Add a document to the RAG knowledge base."""
    repo.add(doc_id=request.doc_id, content=request.content, metadata=request.metadata)
    return IngestResponse(doc_id=request.doc_id)


@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    repo=Depends(get_qdrant_repo),
):
    """Search the RAG knowledge base."""
    docs = repo.search(query=request.query, limit=request.limit)
    results = [
        {"doc_id": d.id, "content": d.content[:500], "score": d.score, "metadata": d.metadata}
        for d in docs
    ]
    return SearchResponse(query=request.query, results=results, count=len(results))
