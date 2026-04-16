import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import BackgroundTasks, FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import httpx

from src.config.settings import Environment, settings
from src.exceptions import AppError, NotFoundError
from src.services.ingest_service import IngestService, _validate_url
from src.services.metrics import MetricsCollector
from src.services.sqlite_store import SQLiteResultStore
from src.services.state_bus import get_state_bus
from src.services.task_store import TaskStore
from src.dependencies import get_qdrant_repo
from src.middleware.auth import ApiKeyMiddleware
from src.middleware.metrics import MetricsMiddleware
from src.middleware.request_id import RequestIdMiddleware
from src.utils.logger import setup_logging
from src.models.schemas import (
    AgentStateEvent,
    CrewAsyncResponse,
    CrewRequest,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    RunHistoryResponse,
    SearchRequest,
    SearchResponse,
    TaskStatusResponse,
    UrlIngestRequest,
    UrlIngestResponse,
)

setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter (DEC-03)
limiter = Limiter(key_func=get_remote_address)

# Task store for async execution (DEC-02)
task_store = TaskStore()

# Metrics collector (DEC-07)
metrics_collector = MetricsCollector()

# SQLite result store for completed run history (DEC-14)
sqlite_store = SQLiteResultStore(db_path=settings.sqlite_db_path)

# URL/PDF ingest service (DEC-15)
ingest_service = IngestService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Starting AI Agent System | "
        f"LLM={settings.llm_provider.value} | "
        f"Embeddings={settings.embedding_mode.value} | "
        f"Env={settings.environment.value}"
    )

    # Production safety checks (I4, I5)
    if settings.environment == Environment.PRODUCTION:
        if not settings.api_key:
            logger.warning(
                "SECURITY WARNING: API_KEY is not set in production — all endpoints are unauthenticated"
            )
        if settings.cors_origins == ["*"]:
            logger.warning(
                "SECURITY WARNING: CORS_ORIGINS is '*' in production — all origins are allowed"
            )

    # Initialize Qdrant singleton (DEC-04)
    try:
        from src.repositories.qdrant_repo import QdrantRepository

        app.state.qdrant_repo = QdrantRepository()
        logger.info("Qdrant repository initialized")
    except Exception as e:
        logger.warning(f"Qdrant not available at startup: {e}")
        app.state.qdrant_repo = None

    # Bind the running event loop so the state bus can dispatch from other threads (DEC-27)
    get_state_bus().bind_loop(asyncio.get_running_loop())
    yield
    logger.info("Shutting down AI Agent System")


app = FastAPI(
    title="AI Agent System",
    description="Multi-agent system with CrewAI, RAG, and industry-specific analysis",
    version="2.0.0",
    lifespan=lifespan,
    # Disable interactive docs in production — prevents API enumeration (I9)
    docs_url=None if settings.environment == Environment.PRODUCTION else "/docs",
    redoc_url=None if settings.environment == Environment.PRODUCTION else "/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(MetricsMiddleware, collector=metrics_collector)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # allow_credentials=True is safe: when cors_origins=["*"] the library automatically
    # omits the Allow-Credentials header (browsers reject wildcard + credentials).
    # In production cors_origins is a specific domain, so credentials work as intended.
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


@app.get("/metrics")
async def metrics():
    """Return application metrics. See DECISIONS.md DEC-07."""
    data = metrics_collector.snapshot()
    data["active_tasks"] = task_store.active_count()
    return data


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


async def _deliver_webhook(url: str, payload: dict) -> None:
    """POST task result to webhook URL. Logs failures; never raises."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)
        logger.info(f"Webhook delivered to {url}")
    except Exception as e:
        logger.warning(f"Webhook delivery failed for {url}: {e}")


def _ts_now() -> str:
    """RFC 3339 UTC timestamp for state-bus events."""
    return datetime.now(timezone.utc).isoformat()


def _execute_crew(task_id: str, topic: str, domain: str | None) -> None:
    """Background task that runs the crew and updates the task store."""
    import time

    bus = get_state_bus()
    bus.publish(
        task_id,
        AgentStateEvent(
            task_id=task_id, agent_role="crew", state="active",
            detail="crew started", ts=_ts_now(),
        ),
    )
    try:
        from src.crew import run_crew

        task_store.update(task_id, status="running")
        start = time.monotonic()
        result = run_crew(topic=topic, domain=domain, task_id=task_id)
        duration = time.monotonic() - start
        task_store.update(task_id, status="completed", result=result)
        sqlite_store.save(
            task_id=task_id,
            topic=topic,
            domain=domain,
            result=result,
            duration_seconds=round(duration, 2),
        )
        bus.publish(
            task_id,
            AgentStateEvent(
                task_id=task_id, agent_role="crew", state="completed",
                detail="crew finished", ts=_ts_now(),
            ),
        )
        status = "completed"
    except Exception as e:
        logger.error(f"Crew task {task_id} failed: {e}")
        result = "Task execution failed. Check logs for details."
        task_store.update(task_id, status="failed", result=result)
        bus.publish(
            task_id,
            AgentStateEvent(
                task_id=task_id, agent_role="crew", state="failed",
                detail="crew failed", ts=_ts_now(),
            ),
        )
        status = "failed"

    # Deliver webhook if configured (best-effort)
    task = task_store.get(task_id)
    webhook_url = task.get("webhook_url") if task else None
    if webhook_url:
        asyncio.run(
            _deliver_webhook(
                webhook_url,
                {"task_id": task_id, "status": status, "result": result},
            )
        )


@app.post("/crew/run", response_model=CrewAsyncResponse, status_code=202)
@limiter.limit("5/minute")
async def run_crew_async(request: Request, body: CrewRequest, background_tasks: BackgroundTasks):
    """Submit a crew execution job. Returns 202 with task_id for polling."""
    if body.webhook_url:
        _validate_url(body.webhook_url)  # raises ValidationError for private IPs / bad schemes
    logger.info(f"Queuing crew: topic='{body.topic}', domain={body.domain}")
    task_id = task_store.create(topic=body.topic, domain=body.domain, webhook_url=body.webhook_url)
    background_tasks.add_task(_execute_crew, task_id, body.topic, body.domain)
    return CrewAsyncResponse(task_id=task_id)


@app.get("/crew/status/{task_id}", response_model=TaskStatusResponse)
@limiter.limit("30/minute")
async def crew_status(request: Request, task_id: str):
    """Poll the status of a crew execution task."""
    task = task_store.get(task_id)
    if task is None:
        raise NotFoundError(f"Task '{task_id}' not found")
    return TaskStatusResponse(**task)


@app.get("/crew/run/{task_id}/events")
async def crew_run_events(request: Request, task_id: str):
    """Stream live per-agent state events as Server-Sent Events (slice-19, DEC-16).

    Ends with a `run_complete` event once the crew reaches a terminal state.
    Unknown task_id → 404. Auth enforced by ApiKeyMiddleware when API_KEY is set.
    """
    if task_store.get(task_id) is None:
        raise NotFoundError(f"Task '{task_id}' not found")

    bus = get_state_bus()

    async def stream():
        yield "retry: 3000\n\n"
        try:
            async for event in bus.subscribe(task_id):
                yield f"event: agent_state\ndata: {event.model_dump_json()}\n\n"
                if event.state in ("completed", "failed"):
                    yield (
                        "event: run_complete\n"
                        f'data: {{"task_id":"{task_id}","status":"{event.state}"}}\n\n'
                    )
        except asyncio.CancelledError:  # pragma: no cover — client disconnect
            return

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/crew/history", response_model=RunHistoryResponse)
@limiter.limit("30/minute")
async def crew_history(request: Request, limit: int = 20):
    """Return the most recent completed crew runs from persistent storage (DEC-14)."""
    limit = max(1, min(limit, 100))
    runs = sqlite_store.list_recent(limit=limit)
    return RunHistoryResponse(runs=runs, count=len(runs))


@app.post("/documents/ingest", response_model=IngestResponse)
@limiter.limit("30/minute")
async def ingest_document(
    request: Request,
    body: IngestRequest,
    repo=Depends(get_qdrant_repo),
):
    """Add a document to the RAG knowledge base."""
    await asyncio.to_thread(repo.add, doc_id=body.doc_id, content=body.content, metadata=body.metadata)
    return IngestResponse(doc_id=body.doc_id)


@app.post("/documents/search", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_documents(
    request: Request,
    body: SearchRequest,
    repo=Depends(get_qdrant_repo),
):
    """Search the RAG knowledge base."""
    docs = await asyncio.to_thread(repo.search, query=body.query, limit=body.limit)
    results = [
        {"doc_id": d.id, "content": d.content[:500], "score": d.score, "metadata": d.metadata}
        for d in docs
    ]
    return SearchResponse(query=body.query, results=results, count=len(results))


@app.post("/documents/ingest/url", response_model=UrlIngestResponse)
@limiter.limit("10/minute")
async def ingest_url(
    request: Request,
    body: UrlIngestRequest,
    repo=Depends(get_qdrant_repo),
):
    """Fetch a URL or PDF and ingest the extracted text into the RAG knowledge base (DEC-15)."""
    text = await ingest_service.fetch_url(body.url)
    doc_id = body.doc_id or body.url
    metadata = {"source_url": body.url, **body.metadata}
    await asyncio.to_thread(repo.add, doc_id=doc_id, content=text, metadata=metadata)
    return UrlIngestResponse(doc_id=doc_id, char_count=len(text))
