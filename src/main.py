import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
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
    yield
    logger.info("Shutting down AI Agent System")


app = FastAPI(
    title="AI Agent System",
    description="Multi-agent system with CrewAI, RAG, and industry-specific analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    try:
        from src.crew import run_crew

        logger.info(f"Running crew: topic='{request.topic}', domain={request.domain}")
        result = run_crew(topic=request.topic, domain=request.domain)
        return CrewResponse(topic=request.topic, domain=request.domain, result=result)
    except Exception as e:
        logger.error(f"Crew execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """Add a document to the RAG knowledge base."""
    try:
        from src.repositories.qdrant_repo import QdrantRepository

        repo = QdrantRepository()
        repo.add(doc_id=request.doc_id, content=request.content, metadata=request.metadata)
        return IngestResponse(doc_id=request.doc_id)
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search the RAG knowledge base."""
    try:
        from src.repositories.qdrant_repo import QdrantRepository

        repo = QdrantRepository()
        docs = repo.search(query=request.query, limit=request.limit)
        results = [
            {"doc_id": d.id, "content": d.content[:500], "score": d.score, "metadata": d.metadata}
            for d in docs
        ]
        return SearchResponse(query=request.query, results=results, count=len(results))
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
