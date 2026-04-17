# Spec: AI Agent System — Production Hardening (v2.0)

> **Baseline:** commit `48c1080` (2026-04-07)
> **Status:** In Progress
> **Domain:** agents.305-ai.com

---

## Objective

Harden the existing CrewAI multi-agent system for production readiness. The codebase is functionally complete (4-agent pipeline, FastAPI, Chainlit, Qdrant RAG, dual LLM providers, 3 industry domains) but lacks the operational scaffolding required for a production deployment: authentication, rate limiting, async execution, structured logging, CI/CD, and Docker hardening.

This spec defines **9 vertical slices** that incrementally transform the codebase from "works locally" to "production-hardened portfolio piece." Each slice is independently testable and demoable.

**Success looks like:** A reviewer can clone the repo, run `make dev`, hit the API with an API key, submit a crew task that returns immediately with a task ID, poll for results, and see structured JSON logs — all running in Docker on Apple Silicon.

---

## Current State Summary

### What Works (Baseline)

| Component | Status | Key Files |
|-----------|--------|-----------|
| 4-agent CrewAI pipeline (Research -> Analysis -> Writing -> Validation) | Working | `src/crew.py`, `src/agents/factory.py`, `src/tasks/definitions.py` |
| FastAPI backend (4 endpoints) | Working | `src/main.py` |
| Chainlit chat UI with `/domain` switching | Working | `src/chainlit_app.py` |
| Qdrant vector DB with CRUD | Working | `src/repositories/qdrant_repo.py` |
| RAG pipeline (ingest + semantic search) | Working | `src/tools/rag.py`, `src/tools/search.py` |
| LLM switching (Ollama / Anthropic) | Working | `src/llm/factory.py` |
| Embedding switching (FastEmbed / Ollama / OpenAI) | Working | `src/llm/embeddings.py` |
| 3 industry domains (healthcare, finance, real_estate) | Working | `src/config/domains/*.yaml` |
| Tool registry with decorator registration | Working | `src/tools/registry.py` |
| Docker Compose (dev + prod) | Working | `docker-compose.dev.yml`, `docker-compose.prod.yml` |
| Unit + integration tests | Written | `tests/unit/`, `tests/integration/` |
| Pydantic Settings config | Working | `src/config/settings.py` |

### What's Missing

| Category | Gap | Impact |
|----------|-----|--------|
| **Infrastructure** | No Makefile | Manual commands for every operation |
| | Single-stage Dockerfile | Bloated image, build tools in prod |
| | No health checks for API/Chainlit in compose | No container orchestration awareness |
| | Qdrant uses `:latest` tag | Non-reproducible builds |
| | No dependency lock file | Floating versions across environments |
| | No CI/CD pipeline | No automated testing or builds |
| | No Chainlit in production compose | Chat UI missing from prod |
| **Security** | CORS allows all origins | Cross-origin requests unrestricted |
| | No authentication | Anyone can call any endpoint |
| | No rate limiting | Abuse-prone expensive endpoints |
| **Code Quality** | QdrantRepository per-request instantiation | Wasteful connections, no lifecycle |
| | All errors return generic 500 | No structured error responses |
| | No structured logging | Unstructured text logs, no request tracing |
| | No metrics endpoint | No runtime observability |
| **Features** | Synchronous crew execution | Requests block 30-120+ seconds, can timeout |
| | No async execution pattern | No way to check task progress |

---

## Goals and Non-Goals

### Goals

- Production-hardened API with auth, rate limiting, and structured errors
- Async crew execution with polling (non-blocking)
- Structured JSON logging with request tracing
- Multi-stage Docker build with health checks
- CI/CD pipeline (GitHub Actions)
- Developer experience (Makefile, dependency lock)
- Metrics endpoint for basic observability

### Non-Goals

- Production deployment to agents.305-ai.com (skip `/ship`)
- User accounts, registration, or JWT authentication
- Celery/Redis task queue (no new infrastructure services)
- Full Prometheus/Grafana monitoring stack
- Frontend redesign of Chainlit UI
- Kubernetes manifests or scaling configuration
- WebSocket streaming (SSE or polling is sufficient)

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Agent Framework | CrewAI (+ LiteLLM) | >= 0.30.0 |
| Chat UI | Chainlit | >= 1.0.0 |
| Web Framework | FastAPI | >= 0.104.0 |
| Vector DB | Qdrant | v1.13.2 (pinned) |
| LLM (local) | Ollama | qwen3:8b |
| LLM (cloud) | Anthropic Claude | claude-sonnet-4-6 |
| Embeddings (local) | FastEmbed | BAAI/bge-small-en-v1.5 |
| Rate Limiting | slowapi | >= 0.1.9 |
| Logging | python-json-logger | >= 2.0.0 |
| CI/CD | GitHub Actions | N/A |
| Python | 3.12+ | 3.13 (conda) |

---

## Commands

```bash
# Development
make dev                    # Start full Docker stack (Qdrant + API + Chainlit)
make down                   # Stop all services
make logs                   # Follow service logs
make clean                  # Remove volumes, caches, build artifacts

# Testing
make test                   # Run unit tests (fast, mocked)
make test-int               # Run integration tests (requires Docker services)
make test-all               # Run all tests with coverage

# Code Quality
make lint                   # Run ruff check
make lint-fix               # Run ruff check --fix
make format                 # Run ruff format

# Build
make build                  # Build Docker images
make lock                   # Generate dependency lock files (pip-compile)

# Utilities
make shell                  # Open shell in agents-api container
make health                 # Curl the /health endpoint
```

---

## Project Structure

```
src/
  config/              # Settings + YAML agent/task definitions
    domains/           # Industry-specific overrides (healthcare, finance, real_estate)
  llm/                 # LLM & embedding provider factories
  agents/              # Agent factory (YAML -> CrewAI Agent)
  tasks/               # Task factory (YAML -> CrewAI Task)
  tools/               # Tool registry + custom tools (search, RAG)
  repositories/        # Document storage abstraction (Qdrant)
  models/              # Pydantic request/response schemas
  middleware/          # [NEW] Auth, rate limiting, request ID, metrics
  services/            # [NEW] Task store for async execution, metrics collector
  exceptions.py        # [NEW] Custom exception hierarchy
  utils/               # Logging utilities
  main.py              # FastAPI application
  chainlit_app.py      # Chainlit chat interface
  crew.py              # Crew assembly and execution
tests/
  unit/                # Fast tests with mocked LLMs (no Docker)
  integration/         # Tests requiring Qdrant + Ollama
.github/
  workflows/
    ci.yml             # [NEW] GitHub Actions pipeline
```

---

## Code Style

Python 3.12+, ruff for linting and formatting, line length 100.

```python
# Example: new custom exception (Slice 2)
class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CrewExecutionError(AppError):
    """Raised when crew execution fails."""

    def __init__(self, message: str = "Crew execution failed"):
        super().__init__(message, status_code=500)


# Example: FastAPI dependency injection (Slice 2)
def get_qdrant_repo(request: Request) -> QdrantRepository:
    return request.app.state.qdrant_repo
```

Naming: `snake_case` everywhere. Test files: `test_<module>.py`. Test functions: `test_<action>_<scenario>_<expected>`.

---

## Testing Strategy

| Level | Framework | Location | Marker | Docker Required |
|-------|-----------|----------|--------|-----------------|
| Unit | pytest | `tests/unit/` | `@pytest.mark.unit` | No |
| Integration | pytest | `tests/integration/` | `@pytest.mark.integration` | Yes (Qdrant) |

**TDD workflow per slice:**
1. **RED** — Write failing tests first (`make test` fails)
2. **GREEN** — Write minimum code to pass (`make test` passes)
3. **REFACTOR** — Clean up, run `make lint`, verify no regressions

**Coverage target:** 80%+ on `src/` (measured via `pytest --cov=src`).

**Test commands:**
```bash
pytest -m unit                      # Fast unit tests
pytest -m integration               # Integration tests (Docker services required)
pytest --cov=src --cov-report=term  # Coverage report
```

---

## Boundaries

### Always Do
- Run `make test` before committing
- Run `make lint` before committing
- Write tests before implementation (TDD)
- Use Pydantic models for all request/response schemas
- Use `settings` for all configuration (never hardcode)
- Pin Docker image versions in compose files
- Keep `/health` endpoint public (no auth)

### Ask First
- Adding new Python dependencies to `pyproject.toml`
- Changing the CrewAI agent pipeline or task definitions
- Modifying the Qdrant collection schema
- Changing Docker port allocations (check PORTS.md)

### Never Do
- Commit `.env` files with real API keys
- Use `docker compose down -v` without warning (destroys Qdrant data)
- Skip tests for "simple" changes
- Add Celery, Redis, or PostgreSQL (out of scope)
- Force push to main
- Modify other projects' port ranges

---

## Architecture Changes

### Before (Current)

```
Request -> CORS(*) -> Route Handler -> sync crew/qdrant -> Response
                                       (new connection each time)
```

### After (Target)

```
Request -> RequestID middleware
        -> API Key auth (except /health, /metrics)
        -> Rate Limiter (per-endpoint)
        -> CORS (env-based origins)
        -> Route Handler
           -> Depends(qdrant_repo)     # singleton from lifespan
           -> BackgroundTasks          # async crew execution
           -> Custom exceptions        # structured error responses
        -> JSON logging (with request_id)
        -> Response (with X-Request-ID header)
```

### New Endpoints

| Method | Path | Auth | Rate Limit | Slice |
|--------|------|------|-----------|-------|
| GET | `/crew/status/{task_id}` | Yes | 30/min | 6 |
| GET | `/metrics` | Yes | 10/min | 9 |

### Modified Endpoints

| Method | Path | Change | Slice |
|--------|------|--------|-------|
| POST | `/crew/run` | Returns 202 + task_id (async) | 6 |
| POST | `/documents/ingest` | Uses Depends(repo) instead of per-request | 2 |
| POST | `/documents/search` | Uses Depends(repo) instead of per-request | 2 |
| GET | `/health` | Unchanged (stays public, no auth) | — |

---

## Vertical Slices

### Slice 1: Developer Tooling (Makefile + Dependency Lock)

**What it delivers:** `make dev`, `make test`, `make lint`, `make build` all work. Locked dependency files for reproducible builds.

**Files created:**
- `Makefile`
- `requirements.txt` (generated by pip-compile)
- `requirements-dev.txt` (generated by pip-compile)

**Files changed:**
- `pyproject.toml` — add `pip-tools` to dev deps

**Tests:** No pytest tests. Validation is functional: each `make` target runs and exits 0.

**Acceptance criteria:**
1. `make dev` starts the full Docker compose stack
2. `make test` runs `pytest -m unit` and exits 0
3. `make lint` runs `ruff check src/ tests/` and exits 0
4. `make build` builds the Docker image successfully
5. `make clean` removes `__pycache__`, `.pytest_cache`, `.ruff_cache`
6. `requirements.txt` is generated and reflects `pyproject.toml`

**Skills:** `incremental-implementation`

---

### Slice 2: Error Handling + Dependency Injection

**What it delivers:** Custom exception classes with structured error responses. QdrantRepository initialized once in lifespan and injected via `Depends()`.

**Files created:**
- `src/exceptions.py` — `AppError`, `NotFoundError`, `ValidationError`, `ServiceUnavailableError`, `CrewExecutionError`
- `tests/unit/test_exceptions.py`
- `tests/unit/test_dependencies.py`

**Files changed:**
- `src/main.py` — exception handlers, lifespan QdrantRepository init, `get_qdrant_repo` dependency, refactor document endpoints to use `Depends`
- `src/tools/rag.py` — keep lazy init for CrewAI tool path (separate from FastAPI DI)
- `src/models/schemas.py` — add `ErrorResponse` schema

**Tests (TDD — write these first):**
1. `test_not_found_returns_404` — trigger NotFoundError, verify 404 + ErrorResponse body
2. `test_validation_error_returns_422` — invalid domain returns 422
3. `test_service_unavailable_returns_503` — Qdrant down returns 503
4. `test_qdrant_repo_singleton` — document endpoints receive the same repo instance
5. `test_error_response_schema` — ErrorResponse has `error`, `detail`, `status_code`

**Acceptance criteria:**
1. No endpoint returns a bare 500 with `str(e)` as detail
2. Each exception type maps to a specific HTTP status code
3. QdrantRepository is created once at startup, not per request
4. `make test` passes with all new tests

**Skills:** `api-and-interface-design`, `test-driven-development`

---

### Slice 3: Structured Logging

**What it delivers:** JSON-formatted logs in production, human-readable in development. Request ID injected into every log line and response header.

**Files created:**
- `src/middleware/__init__.py`
- `src/middleware/request_id.py` — generates UUID, stores in context, adds `X-Request-ID` response header
- `tests/unit/test_logging.py`

**Files changed:**
- `src/utils/logger.py` — JSON formatter class, select format by environment, context filter for request_id
- `src/main.py` — add RequestIdMiddleware
- `pyproject.toml` — add `python-json-logger` dependency

**Tests (TDD):**
1. `test_json_log_format_in_production` — ENVIRONMENT=production produces valid JSON with timestamp, level, message
2. `test_human_format_in_development` — ENVIRONMENT=development uses existing readable format
3. `test_request_id_in_response_header` — every response has `X-Request-ID` header
4. `test_request_id_middleware_generates_uuid` — middleware creates valid UUID4

**Acceptance criteria:**
1. `ENVIRONMENT=production` produces JSON logs
2. Every HTTP response includes `X-Request-ID`
3. Development mode is unchanged
4. All existing tests still pass

**Skills:** `test-driven-development`

---

### Slice 4: API Key Authentication

**What it delivers:** All endpoints except `/health` require `X-API-Key` header. When `API_KEY` env var is not set, auth is bypassed (development convenience).

**Files created:**
- `src/middleware/auth.py` — `api_key_auth` FastAPI dependency
- `tests/unit/test_auth.py`

**Files changed:**
- `src/config/settings.py` — add `api_key: Optional[str] = None`
- `src/main.py` — apply auth dependency to protected routes
- `.env.example` — add `API_KEY` variable
- `docker-compose.prod.yml` — add `API_KEY: ${API_KEY}`

**Tests (TDD):**
1. `test_health_no_auth_required` — GET `/health` returns 200 without header
2. `test_crew_run_requires_api_key` — POST `/crew/run` without key returns 401
3. `test_crew_run_with_valid_key` — POST `/crew/run` with correct key returns 200
4. `test_crew_run_with_invalid_key` — wrong key returns 401
5. `test_auth_bypassed_when_no_key_configured` — no `API_KEY` env → all endpoints work
6. `test_documents_ingest_requires_auth` — 401 without key
7. `test_documents_search_requires_auth` — 401 without key

**Acceptance criteria:**
1. `/health` always works without auth
2. Protected endpoints return 401 when API_KEY is set and header missing/wrong
3. Auth bypassed when API_KEY not configured
4. Uses ErrorResponse schema from Slice 2

**Skills:** `security-and-hardening`, `test-driven-development`

---

### Slice 5: Rate Limiting + CORS Hardening

**What it delivers:** Per-endpoint rate limits via slowapi. Environment-based CORS origins.

**Files created:**
- `tests/unit/test_rate_limiting.py`
- `tests/unit/test_cors.py`

**Files changed:**
- `src/main.py` — replace CORS `["*"]` with `settings.cors_origins`, add slowapi limiter
- `src/config/settings.py` — add `cors_origins: list[str]`, `rate_limit_crew: str`, `rate_limit_documents: str`
- `pyproject.toml` — add `slowapi` dependency
- `.env.example` — add CORS_ORIGINS, rate limit vars
- `docker-compose.prod.yml` — set `CORS_ORIGINS=https://agents.305-ai.com`

**Rate limits:**
| Endpoint | Limit |
|----------|-------|
| `/crew/run` | 5/minute |
| `/documents/*` | 30/minute |
| `/health` | No limit |
| `/metrics` | 10/minute |

**Tests (TDD):**
1. `test_cors_allows_all_in_dev` — default cors_origins=["*"] works
2. `test_cors_restricts_in_prod` — only configured origin gets CORS headers
3. `test_rate_limit_crew_run` — 6th request within 1 minute returns 429
4. `test_rate_limit_documents_search` — 31st request returns 429
5. `test_rate_limit_health_no_limit` — `/health` is not rate limited

**Acceptance criteria:**
1. CORS origins driven by env var
2. Rate limiting returns 429 with `Retry-After` header
3. `/health` excluded from rate limiting
4. slowapi state is in-memory (no Redis)

**Skills:** `security-and-hardening`, `test-driven-development`

---

### Slice 6: Async Crew Execution

**What it delivers:** POST `/crew/run` returns 202 immediately with `task_id`. GET `/crew/status/{task_id}` returns status and result when done. Background execution via FastAPI BackgroundTasks.

**Files created:**
- `src/services/__init__.py`
- `src/services/task_store.py` — `TaskStore` with create/get/update/cleanup, in-memory dict with TTL
- `tests/unit/test_task_store.py`
- `tests/unit/test_async_crew.py`

**Files changed:**
- `src/models/schemas.py` — add `CrewAsyncResponse`, `TaskStatusResponse`, `TaskStatus` enum
- `src/main.py` — refactor `/crew/run` to BackgroundTasks, add GET `/crew/status/{task_id}`, init TaskStore in lifespan

**API contract:**

```
POST /crew/run  {"topic": "AI in healthcare", "domain": "healthcare"}
  -> 202  {"task_id": "uuid-...", "status": "pending"}

GET /crew/status/{task_id}
  -> 200  {"task_id": "...", "status": "running|completed|failed", "result": "...", "created_at": "...", "completed_at": "..."}
  -> 404  {"error": "NotFoundError", "detail": "Task not found"}
```

**Tests (TDD):**
1. `test_crew_run_returns_202` — POST returns 202 with task_id
2. `test_crew_status_pending` — immediate GET after POST returns pending
3. `test_crew_status_completed` — after crew finishes, status is completed with result
4. `test_crew_status_failed` — crew exception sets status to failed
5. `test_crew_status_not_found` — unknown task_id returns 404
6. `test_task_store_create_and_get` — TaskStore lifecycle
7. `test_task_store_update_status` — status transitions
8. `test_task_store_cleanup_expired` — TTL cleanup removes old tasks

**Acceptance criteria:**
1. `/crew/run` returns 202 (not 200) with `task_id`
2. `/crew/status/{task_id}` returns current status
3. Completed tasks include full crew output in `result`
4. Failed tasks include error message
5. Tasks auto-expire after TTL (default 1 hour)
6. Chainlit still works (calls `run_crew()` directly, not API)

**Skills:** `api-and-interface-design`, `test-driven-development`

---

### Slice 7: Docker Hardening

**What it delivers:** Multi-stage Dockerfile. Non-root user. Pinned Qdrant version. Health checks for all compose services. Chainlit added to production compose.

**Files changed:**
- `Dockerfile` — multi-stage build (builder + runtime), `USER appuser`
- `docker-compose.dev.yml` — pin `qdrant/qdrant:v1.13.2`, add healthchecks for agents-api and chainlit-ui
- `docker-compose.prod.yml` — pin Qdrant, add healthchecks, add chainlit-ui service, add API_KEY

**Tests:** Functional validation:
1. `make build` succeeds
2. Container runs as non-root
3. `docker compose -f docker-compose.dev.yml config` validates
4. `docker compose -f docker-compose.prod.yml config` validates

**Acceptance criteria:**
1. Docker build produces working image
2. Runtime image is smaller than current single-stage
3. Container user is `appuser` (not root)
4. Qdrant version pinned (no `:latest`)
5. All compose services have health checks
6. Chainlit in production compose

**Skills:** `ci-cd-and-automation`

---

### Slice 8: CI/CD Pipeline (GitHub Actions)

**What it delivers:** Automated lint -> test -> build -> push on every push/PR to main.

**Files created:**
- `.github/workflows/ci.yml`

**Pipeline stages:**
1. **Lint** — `ruff check src/ tests/`
2. **Test** — `pytest -m unit` (no Docker services needed)
3. **Build** — `docker build .`
4. **Push** — push to ghcr.io (main branch only, requires GHCR_TOKEN secret)

**Tests:** Pipeline YAML validates. `make lint && make test` exit 0 locally.

**Acceptance criteria:**
1. Push to main triggers CI
2. PR to main triggers CI
3. 4 stages: lint -> test -> build -> push
4. Push only on main (not PRs)
5. pip cache for faster installs
6. Docker layer cache for faster builds

**Skills:** `ci-cd-and-automation`

---

### Slice 9: Monitoring + Metrics Endpoint

**What it delivers:** GET `/metrics` returning JSON with request counts, error counts, response times, active tasks, uptime.

**Files created:**
- `src/middleware/metrics.py` — records request count, duration, status per endpoint
- `src/services/metrics.py` — `MetricsCollector` class (in-memory counters)
- `tests/unit/test_metrics.py`

**Files changed:**
- `src/main.py` — add MetricsMiddleware, add GET `/metrics`
- `src/models/schemas.py` — add `MetricsResponse` schema

**Tests (TDD):**
1. `test_metrics_endpoint_returns_data` — GET `/metrics` returns expected JSON structure
2. `test_metrics_counts_requests` — 3 requests to `/health` -> count=3
3. `test_metrics_tracks_errors` — failed request increments error count
4. `test_metrics_response_time` — average response time is positive
5. `test_metrics_requires_auth` — `/metrics` requires API key

**Acceptance criteria:**
1. `/metrics` returns: `total_requests`, `error_count`, `endpoints`, `uptime_seconds`, `active_tasks`
2. Metrics are in-memory (reset on restart)
3. `/metrics` protected by API key auth
4. Response times tracked per endpoint

**Skills:** `test-driven-development`, `performance-optimization`

---

## Workflow Protocol

For each slice, follow this exact sequence:

### Step 1: `/plan` the slice
Read the slice description. Identify exact files. Write pseudocode for interfaces.

### Step 2: `/test` — RED phase
Write all test files for the slice. Run `make test` — new tests FAIL. This confirms tests assert behavior that doesn't exist yet.

### Step 3: `/build` — GREEN phase
Implement minimum code to pass all tests. Run `make test` — all tests PASS. Run `make lint` — clean.

### Step 4: `/review` the slice
Review diff against acceptance criteria. Run full test suite (`make test-all`) to catch regressions. Check against relevant AGENTS.md checklists.

### Step 5: Commit
```bash
git add <slice files only>
git commit -m "feat(slice-N): <description>"
```

### Between slices
Run `make test` to verify no regressions before starting next slice.

---

## File Inventory

### New Files (20)

| File | Slice | Purpose |
|------|-------|---------|
| `Makefile` | 1 | Standard dev targets |
| `requirements.txt` | 1 | Locked production deps |
| `requirements-dev.txt` | 1 | Locked dev deps |
| `src/exceptions.py` | 2 | Custom exception hierarchy |
| `tests/unit/test_exceptions.py` | 2 | Exception handler tests |
| `tests/unit/test_dependencies.py` | 2 | DI/singleton tests |
| `src/middleware/__init__.py` | 3 | Middleware package |
| `src/middleware/request_id.py` | 3 | Request ID middleware |
| `tests/unit/test_logging.py` | 3 | Logging format tests |
| `src/middleware/auth.py` | 4 | API key auth dependency |
| `tests/unit/test_auth.py` | 4 | Auth tests |
| `tests/unit/test_rate_limiting.py` | 5 | Rate limiting tests |
| `tests/unit/test_cors.py` | 5 | CORS tests |
| `src/services/__init__.py` | 6 | Services package |
| `src/services/task_store.py` | 6 | In-memory async task store |
| `tests/unit/test_task_store.py` | 6 | TaskStore unit tests |
| `tests/unit/test_async_crew.py` | 6 | Async crew endpoint tests |
| `.github/workflows/ci.yml` | 8 | GitHub Actions CI |
| `src/middleware/metrics.py` | 9 | Metrics collection middleware |
| `src/services/metrics.py` | 9 | MetricsCollector class |
| `tests/unit/test_metrics.py` | 9 | Metrics tests |

### Modified Files (10)

| File | Slices | Changes |
|------|--------|---------|
| `pyproject.toml` | 1, 3, 5 | pip-tools, python-json-logger, slowapi |
| `src/main.py` | 2, 3, 4, 5, 6, 9 | Exceptions, DI, middleware, auth, rate limit, async, metrics |
| `src/config/settings.py` | 4, 5 | api_key, cors_origins, rate limits |
| `src/models/schemas.py` | 2, 6, 9 | ErrorResponse, async responses, metrics |
| `src/utils/logger.py` | 3 | JSON formatter, context filter |
| `src/tools/rag.py` | 2 | Document lazy-init note (keep for CrewAI path) |
| `.env.example` | 4, 5 | API_KEY, CORS_ORIGINS, rate limits |
| `docker-compose.dev.yml` | 7 | Pin Qdrant, add healthchecks |
| `docker-compose.prod.yml` | 4, 7 | API_KEY, pin Qdrant, healthchecks, Chainlit |
| `Dockerfile` | 7 | Multi-stage build, non-root user |

---

## Risk Areas

| Risk | Mitigation |
|------|-----------|
| `src/main.py` modified in 6 slices | Each slice touches a different concern (additive). Full test suite after each slice catches drift. |
| BackgroundTasks may not handle very long crew runs | BackgroundTasks are not subject to request timeouts. Task store captures success/failure regardless. |
| slowapi may conflict with auth middleware | slowapi decorates route handlers; auth is a Depends(). Different layers, tested explicitly. |
| Existing integration tests may break after DI changes | DI changes don't affect mock targets. Verified by running `make test` after Slice 2. |

---

## Success Criteria

- [ ] All 9 slices implemented with passing tests
- [ ] `make dev` starts the full stack in Docker on Apple Silicon
- [ ] `make test` passes with 80%+ coverage on `src/`
- [ ] `make lint` exits clean
- [ ] API key protects all endpoints except `/health`
- [ ] POST `/crew/run` returns 202 with task_id
- [ ] GET `/crew/status/{id}` returns task result
- [ ] Structured JSON logs in production mode
- [ ] `/metrics` returns runtime statistics
- [ ] CI pipeline passes on push to main
- [ ] Docker image runs as non-root user
- [ ] All design decisions documented in DECISIONS.md

---

## Open Questions

None. All design decisions have been made and documented in [DECISIONS.md](DECISIONS.md). See that file for rationale and alternatives considered.

---

---

# Phase 4 — Portfolio Demos (v4.0)

> **Baseline:** commit on `main` after slice 18 + rate-limiter isolation fix (2026-04-15)
> **Status:** Spec written 2026-04-16. Implementation not started.
> **Source plan:** `~/.claude/plans/analyze-the-current-state-temporal-quilt.md` (approved in plan mode)

---

## Phase 4 Objective

Turn the now-hardened, feature-rich system (slices 1-18) into a **portfolio-grade sales asset**. Prospects in a live pitch must be able to:

1. Watch a crew of AI agents work in real time on a dedicated dashboard.
2. Pick from preset business workflows that mirror actual business scenarios (sales, support, content, real estate).
3. See agents delegate to each other and work in parallel — not just a sequential pipeline.
4. Hear an agent **place a phone call** (demo-scale, opt-in, Twilio trial).
5. Leave the meeting with a shareable link + PDF of the run.
6. Re-run the exact same demo deterministically on demand.

**Success looks like:** Armando can open `http://localhost:3061`, pick a `support_triage` workflow, watch a hierarchical crew complete on a live kanban dashboard, copy a share URL for the prospect, and — if `VOICE_ENABLED=true` — have an agent call the prospect's verified phone and read them the summary.

---

## Phase 4 Goals and Non-Goals

### Goals

- **Live team view** — an SSE-driven dashboard showing per-agent state (queued/active/waiting/done) as CrewAI runs
- **Pluggable workflows** — agents+tasks+process lives in `src/workflows/<name>.py`, selectable per run
- **Hierarchical + parallel processes** — CrewAI `Process.hierarchical` and `async_execution=True` are supported where they help
- **7 business workflows** shipped — `research_report` (migrated), `lead_qualifier`, `sdr_outreach`, `support_triage`, `meeting_prep`, `content_pipeline`, `real_estate_cma`, `receptionist`
- **Voice agent** — Twilio-trial receptionist that can place outbound demo calls with TwiML webhooks
- **Share + PDF** — HMAC-signed 7-day read-only link, WeasyPrint PDF export
- **Demo harness** — `DEMO_MODE=true` deterministic fake LLM + canned scenarios for zero-risk pitches
- **Next.js 14 dashboard** shipped as a separate docker-compose service on port 3061

### Non-Goals (Phase 4)

- Production deployment to `agents.305-ai.com` — **deferred** (no `/ship` this cycle, per user instruction)
- Multi-tenant support, user accounts, or role-based access
- Replacing Chainlit — Chainlit stays as the operator chat UI; the dashboard is a new surface for stakeholders
- Persistent event bus (Redis, Kafka) — `AgentStateBus` is in-process asyncio pub/sub (see DEC-27)
- Real inbound IVR menus — voice slice only covers outbound + one-shot capture
- Paid voice providers — Twilio trial only; Telnyx is a documented fallback but not wired
- Full design system — Tailwind + shadcn/ui primitives are the ceiling; no Figma handoff

---

## Phase 4 Architecture Changes

### New runtime topology

```
┌──────────────┐     ┌─────────────────────┐      ┌───────────────────┐
│ Chainlit UI  │     │  Next.js Dashboard  │      │  Twilio (cloud)   │
│   :3060      │     │      :3061          │      │  (via ngrok)      │
└──────┬───────┘     └──────────┬──────────┘      └─────────┬─────────┘
       │ HTTP +              HTTP + SSE                     │ TwiML webhook
       │ async callback      EventSource                    │ POST
       ▼                      ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI  (:8060)                                │
│                                                                  │
│   /crew/run        ──► TaskStore ──► BackgroundTasks            │
│                                       └─► build_crew(workflow)  │
│                                            └─► AgentStateBus ───┤ SSE
│   /crew/run/{id}/events  (SSE)  ◄─────────────────────────────── │
│   /workflows       (GET)                                         │
│   /voice/twiml/{task_id}  (POST from Twilio)                    │
│   /share/{token}   (public, HMAC-gated)                          │
│   /crew/history/{id}/pdf  (weasyprint)                           │
└─────────────────────────────────────────────────────────────────┘
       │                              │
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│   Qdrant     │              │   SQLite     │
│   :6333      │              │ data/*.db    │
└──────────────┘              └──────────────┘
```

### New API contract — live events

```
GET /crew/run/{task_id}/events       (text/event-stream)
  retry: 3000
  event: agent_state
  data: {"task_id":"…","agent_role":"researcher","state":"active",
         "detail":"tool: web_search(q=…)","ts":"2026-04-16T…Z"}

  event: agent_state
  data: {"task_id":"…","agent_role":"analyst","state":"waiting_on_agent",
         "detail":"depends on researcher","ts":"…"}

  event: run_complete
  data: {"task_id":"…","status":"completed"}
```

States: `queued | active | waiting_on_tool | waiting_on_agent | completed | failed`.
404 for unknown task_id. Stream closes on `run_complete` or `run_failed`.

### New API contract — workflows

```
GET /workflows
  -> 200 [{"name":"research_report","description":"…","process":"sequential","agents":["researcher","analyst","writer","validator"]}, …]

POST /crew/run
  body: {"topic":"…", "domain":"…", "workflow":"support_triage", "webhook_url":"…"}
  backward-compat: omitting "workflow" defaults to "research_report" (identical to today's behavior)
```

### New API contract — voice

```
POST /crew/run  { "workflow":"receptionist", "topic":"book table for 4 at 7pm",
                  "domain":"general", "voice":{"to":"+15551234567"} }
  -> 202  (requires VOICE_ENABLED=true AND verified Twilio trial number)

POST /voice/twiml/{task_id}   (called by Twilio, not the user)
  form-urlencoded: CallSid, From, To, Digits, SpeechResult, …
  -> 200  text/xml  (TwiML: <Say>…</Say><Gather input="speech">…</Gather>)
```

### New API contract — share + PDF

```
GET /share/{token}
  token = base64url(HMAC-SHA256(SHARE_SECRET, task_id + "|" + exp_unix) | ":" | task_id | ":" | exp_unix)
  -> 200  text/html   (read-only render)
  -> 403  invalid signature
  -> 410  expired

GET /crew/history/{task_id}/pdf     (auth required)
  -> 200  application/pdf
```

---

## Phase 4 Tech Stack Additions

| Component | Version | Why |
|-----------|---------|-----|
| Next.js | 14 (App Router) | Dashboard framework (DEC-26) |
| TypeScript | 5.x | Type-safe frontend |
| Tailwind CSS | 3.4 | Styling |
| shadcn/ui | latest | Component primitives (DEC-26a) |
| lucide-react | latest | Icons |
| Framer Motion | 11 | Card transitions on state change |
| MSW | 2.x | Dashboard unit-test mocking |
| Vitest | 1.x | Dashboard unit tests |
| Playwright | latest | Dashboard E2E |
| twilio | 9.x | Voice SDK (slice 26) |
| weasyprint | 62.x | PDF export (slice 27) |
| pypdf | already present | PDF parsing (unchanged from slice 15) |

---

## Phase 4 Commands Additions

```bash
# Dashboard (in dashboard/ directory)
cd dashboard
npm install
npm run dev              # http://localhost:3000 (mapped to :3061 in docker)
npm run build
npm test                 # Vitest
npm run test:e2e         # Playwright against running stack

# Voice demo (requires VOICE_ENABLED=true + Twilio env vars + ngrok)
ngrok http 8060                                   # in one terminal
export TWILIO_WEBHOOK_BASE=https://abc.ngrok.io   # paste the ngrok URL
uv run pytest -m voice                            # opt-in Twilio mock tests
# Live call test: POST /crew/run with workflow=receptionist + verified number

# Demo harness
DEMO_MODE=true uv run python scripts/demo.py --scenario lead-qualifier-acme
DEMO_MODE=true uv run python scripts/demo.py --list
```

---

## Phase 4 Project Structure Additions

```
src/
  services/
    state_bus.py       # [NEW] in-process asyncio pub/sub (DEC-27)
    share_token.py     # [NEW] HMAC-signed short URL (DEC-24)
    pdf_export.py      # [NEW] weasyprint renderer
  workflows/           # [NEW package] pluggable crew templates (DEC-18)
    __init__.py        # registry, get_workflow(), list_workflows()
    base.py            # Workflow dataclass
    research_report.py # migrated from crew.py
    lead_qualifier.py
    sdr_outreach.py
    support_triage.py
    meeting_prep.py
    content_pipeline.py
    real_estate_cma.py
    receptionist.py
  tools/
    voice.py           # [NEW] VoiceCallTool wrapping twilio.rest.Client
  demo/                # [NEW package] deterministic pitch mode (DEC-25)
    __init__.py
    fake_llm.py
    scenarios.yaml
scripts/
  demo.py              # [NEW] CLI entry for deterministic scenarios
docs/
  demos/               # [NEW] pitch scripts per workflow pack
    sales.md
    support.md
    verticals.md
    voice.md
    dashboard.md
dashboard/             # [NEW] Next.js 14 app (DEC-26)
  app/
    layout.tsx
    page.tsx                 # launcher
    runs/
      page.tsx               # history
      [id]/page.tsx          # live team view
    share/
      [token]/page.tsx       # public read-only render
  components/
    AgentCard.tsx
    StateChip.tsx
    KanbanColumn.tsx
    WorkflowSelector.tsx
    ToolLog.tsx
    TimelineStrip.tsx
  lib/
    api.ts
    sse.ts
    types.ts
  __tests__/           # Vitest + @testing-library/react (co-located per component)
  e2e/                 # Playwright
  Dockerfile           # multi-stage node:20-alpine
  package.json
  tsconfig.json
  next.config.js
  tailwind.config.ts
  vitest.config.ts
  playwright.config.ts
  .env.example
```

---

## Phase 4 Vertical Slices

Each slice is: **goal → non-goals → files → test plan (RED tests) → acceptance criteria → risks → skills.** Each slice ends with a single commit (`feat(slice-N): …`).

---

### Slice 19 — Agent State Bus + SSE endpoint

**Goal:** Emit typed per-agent state events from CrewAI runs onto an in-process bus, and expose them as an SSE stream on `GET /crew/run/{task_id}/events`.

**Non-goals:** Redis/Kafka; a new persistence layer (slice 27 adds the `agent_events` table); ordering guarantees across multiple subscribers (we only subscribe one dashboard per run in v4.0).

**Files created:**
- `src/services/state_bus.py` — `AgentStateBus` with `publish(task_id, event)` and `subscribe(task_id) -> AsyncIterator[AgentStateEvent]`, asyncio.Queue-per-subscriber, TTL cleanup.
- `tests/unit/test_agent_state_bus.py`
- `tests/unit/test_sse_endpoint.py`

**Files changed:**
- `src/crew.py` — extend `step_callback` to emit `AgentStateEvent` to the bus (keyed by `task_id`).
- `src/models/schemas.py` — add `AgentStateEvent` Pydantic model (`task_id`, `agent_role`, `state`, `detail`, `ts`), `AgentRunState` enum.
- `src/main.py` — new `GET /crew/run/{task_id}/events` returning `StreamingResponse` with `text/event-stream`, 404 on unknown task, auto-close on terminal event.
- `src/dependencies.py` — expose the singleton bus.

**Test plan (RED tests first):**
1. `test_bus_publish_delivers_to_single_subscriber`
2. `test_bus_multiple_subscribers_same_task_id_all_receive`
3. `test_bus_different_task_ids_isolated`
4. `test_bus_queue_full_drops_oldest_with_warning` (bounded queue per subscriber)
5. `test_bus_cleanup_when_no_subscribers_for_ttl`
6. `test_sse_unknown_task_id_returns_404`
7. `test_sse_emits_ordered_events_for_live_run`
8. `test_sse_closes_stream_on_run_complete_event`
9. `test_sse_respects_api_key_when_configured`

**Acceptance criteria:**
- `curl -N http://localhost:8060/crew/run/{id}/events` prints `data: {...}` lines while a run is in progress.
- Unknown task_id returns 404 within 100ms.
- All 9 tests green; `uv run pytest -m unit` total suite still green.

**Risks & mitigations:**
- **CrewAI step_callback runs in a background thread** (see `project_feature_expansion.md`). Mitigation: use `asyncio.run_coroutine_threadsafe(bus.publish(…), loop)` exactly as the Chainlit streaming does today.
- **Slow consumer backs up producer.** Mitigation: bounded queue (max 1000 events/subscriber), drop-oldest-with-warning strategy, logged at WARNING.
- **Memory leak if subscribers never disconnect.** Mitigation: heartbeat (SSE comment line every 15s); server closes stream 30s after terminal event.

**Skills:** `test-driven-development`, `api-and-interface-design`, `incremental-implementation`.

---

### Slice 20 — Next.js Dashboard (Team View)

This slice is broken into **four** sub-slices (20a, 20b, 20c, 20d) to keep each commit demoable. 20d is merged into slice 27.

#### Slice 20a — Scaffold + CI

**Goal:** Stand up a `dashboard/` Next.js 14 app, wire it into `docker-compose.dev.yml` as a 4th service, green-light Vitest + Playwright.

**Non-goals:** Any run-view UI (that's 20c); any shadcn components beyond the demo baseline.

**Files created (scaffolded via `npx create-next-app@latest dashboard --ts --tailwind --app --no-src-dir --eslint`):**
- Everything under `dashboard/` listed in *Phase 4 Project Structure Additions*
- `dashboard/Dockerfile` (multi-stage: `deps` → `builder` → `runner`, `node:20-alpine`)
- `dashboard/__tests__/smoke.test.tsx`
- `dashboard/e2e/home.spec.ts`

**Files changed:**
- `docker-compose.dev.yml` — add `dashboard` service: `node:20-alpine`, `working_dir: /app`, volume-mount `./dashboard:/app`, `command: sh -c "npm ci && npm run dev -- --hostname 0.0.0.0"`, port `3061:3000`, `depends_on: [agents-api]`, env `NEXT_PUBLIC_API_URL=http://localhost:8060`.
- `docker-compose.prod.yml` — add `dashboard` service using the multi-stage Dockerfile, port 3061:3000, health check on `/`.
- `PORTS.md` — add row `3061` for Dashboard dev (verify no collision with other portfolio projects first).
- `README.md` — add dashboard start instructions.

**Test plan:**
1. Vitest: `smoke.test.tsx` renders `<Home />` and asserts title "AI Agent Team Dashboard".
2. Playwright: `home.spec.ts` hits `http://localhost:3061` and checks the title.
3. Docker: `docker compose -f docker-compose.dev.yml config` validates; `docker compose up` brings all 4 services healthy.

**Acceptance criteria:**
- `docker compose up` boots 4 services (qdrant, agents-api, chainlit-ui, dashboard).
- `npm test` and `npm run test:e2e` both green.
- `/` renders "AI Agent Team Dashboard" title.

**Risks & mitigations:**
- **Port 3061 collision** with another portfolio project. Mitigation: grep `PORTS.md` first; pick next free port if needed.
- **npm install slow on first dev boot.** Mitigation: `npm ci` + a `node_modules` named volume to persist between restarts.

**Skills:** `frontend-ui-engineering`, `ci-cd-and-automation`, `source-driven-development` (verify create-next-app flags against current docs).

---

#### Slice 20b — Run launcher + history

**Goal:** `/` lets the user pick a workflow + domain + topic and launch a run, landing them on `/runs/[id]`. `/runs` shows paginated history from `GET /crew/history`.

**Non-goals:** Live event wiring (that's 20c); authentication (uses same API key the rest of the stack uses, passed via `NEXT_PUBLIC_API_KEY`).

**Files created:**
- `dashboard/app/page.tsx` — launcher form (shadcn `Select` + `Input` + `Button`).
- `dashboard/app/runs/page.tsx` — history table.
- `dashboard/components/WorkflowSelector.tsx`
- `dashboard/lib/api.ts` — typed `apiClient.runCrew()`, `listWorkflows()`, `listHistory()`.
- `dashboard/lib/types.ts` — TypeScript mirrors of Python schemas.
- `dashboard/__tests__/launcher.test.tsx`
- `dashboard/__tests__/history.test.tsx`

**Files changed (backend):**
- `src/main.py` — add `GET /workflows` (public, no rate limit, returns registry output); widen CORS allow-list to include `http://localhost:3061` when `ENVIRONMENT=development`.
- `src/config/settings.py` — add `DASHBOARD_ORIGIN: str = "http://localhost:3061"`.

**Test plan (RED):**
1. Vitest `launcher.test.tsx` — renders form, MSW-mocks `GET /workflows`, fills form, submits, asserts navigation to `/runs/:id`.
2. Vitest `history.test.tsx` — MSW-mocks `GET /crew/history` with 3 rows and an empty state.
3. Vitest form validation — submit with empty topic shows error.
4. Python `tests/unit/test_workflows_endpoint.py` — `GET /workflows` returns JSON list shape.

**Acceptance criteria:**
- User can fill the form, click Launch, land on `/runs/{id}`.
- History table populates from the API; empty state renders when no runs exist.
- CORS works from port 3061.

**Risks & mitigations:**
- **CORS misconfiguration in dev.** Mitigation: explicit `DASHBOARD_ORIGIN` in settings + regression test that sends `Origin: http://localhost:3061` and asserts `Access-Control-Allow-Origin`.
- **Next.js router hydration mismatch.** Mitigation: launcher form is a client component (`"use client"`); tests use `userEvent` not direct DOM.

**Skills:** `frontend-ui-engineering`, `api-and-interface-design`, `test-driven-development`.

---

#### Slice 20c — Live team view (SSE)

**Goal:** `/runs/[id]` shows a 4-column kanban (Queued / Active / Waiting / Done) with one card per agent. Cards animate between columns as SSE events arrive.

**Non-goals:** Share/PDF rendering (slice 27); deep tool-output inspection (we show a collapsed log, not raw model I/O).

**Files created:**
- `dashboard/app/runs/[id]/page.tsx` — client component; opens `EventSource`, dispatches to reducer keyed by `agent_role`.
- `dashboard/components/AgentCard.tsx`, `StateChip.tsx`, `KanbanColumn.tsx`, `ToolLog.tsx`, `TimelineStrip.tsx`
- `dashboard/lib/sse.ts` — typed EventSource wrapper with reconnection.
- `dashboard/__tests__/run-view.test.tsx`
- `dashboard/e2e/live-run.spec.ts`

**Test plan (RED):**
1. Vitest `run-view.test.tsx` — mock EventSource, feed a scripted sequence of `agent_state` events, snapshot the DOM after each, assert cards move between columns.
2. Vitest — a `waiting_on_agent` event lights the "Waiting" column with the correct blocked-by label.
3. Vitest — on `run_complete`, the elapsed-time counter stops and a "Copy Share Link" button appears (slice 27 will wire it).
4. Playwright `live-run.spec.ts` — launches a real run in `DEMO_MODE=true` (deterministic), opens the run page, asserts a full `queued → active → done` sequence for the research-report workflow.

**Acceptance criteria:**
- Opening `http://localhost:3061/runs/{id}` during a live crew run shows cards animating across columns in real time.
- SSE reconnects automatically after a transient network blip (within 5s).
- Playwright E2E passes in CI.

**Risks & mitigations:**
- **SSE buffering through proxies** (especially under docker-compose). Mitigation: set `X-Accel-Buffering: no`, disable uvicorn gzip for this route.
- **Framer Motion janks on cheap laptops.** Mitigation: prefers-reduced-motion media query, cap animation duration at 200ms.
- **React 18 StrictMode mounts EventSource twice.** Mitigation: use `useEffect` cleanup properly and test explicitly for no duplicate subscriptions.

**Skills:** `frontend-ui-engineering`, `browser-testing-with-devtools`, `test-driven-development`.

---

#### Slice 20d — *merged into slice 27*

---

### Slice 21 — Workflow Registry

**Goal:** Extract the hard-coded 4-agent pipeline from `src/crew.py` into a pluggable `src/workflows/` package. `POST /crew/run` gains an optional `workflow` field (defaults to `research_report` for backward compat).

**Non-goals:** Ship new workflows (that's 23-25); hierarchical/parallel support (that's 22).

**Files created:**
- `src/workflows/__init__.py` — `register_workflow()`, `get_workflow(name)`, `list_workflows()`.
- `src/workflows/base.py` — `Workflow` dataclass: `name`, `description`, `agent_roles`, `task_specs`, `process`, `parallel_tasks`, `inputs_schema`.
- `src/workflows/research_report.py` — migrated pipeline (identical behavior).
- `tests/unit/test_workflow_registry.py`
- `tests/unit/test_research_report_workflow.py`

**Files changed:**
- `src/crew.py` — `build_crew(workflow_name, inputs)` delegates to the registry.
- `src/models/schemas.py` — `CrewRunRequest.workflow: str = "research_report"`, `WorkflowInfo` response model.
- `src/main.py` — `GET /workflows` (used by slice 20b already), thread `workflow` through `/crew/run`.

**Test plan (RED):**
1. `test_register_and_retrieve`
2. `test_get_unknown_raises`
3. `test_list_workflows_returns_all_registered`
4. `test_duplicate_registration_raises`
5. `test_research_report_migration_produces_identical_crew_shape`
6. `test_crew_run_default_workflow_is_research_report`
7. `test_crew_run_explicit_workflow_honored`
8. `test_crew_run_unknown_workflow_returns_422`

**Acceptance criteria:**
- `POST /crew/run` without `workflow` field behaves identically to today (byte-compatible for research_report).
- `GET /workflows` returns ≥ 1 entry.
- All 18 existing slices' tests still pass — no regressions.

**Risks & mitigations:**
- **Breaking backward compatibility.** Mitigation: golden-output tests against the current research_report pipeline; run them before and after the migration.
- **Circular imports** between `crew.py` and `workflows/*`. Mitigation: workflows only import from `src.agents`, `src.tasks`, `src.tools`; `crew.py` is the only consumer of `workflows`.

**Skills:** `deprecation-and-migration`, `api-and-interface-design`, `test-driven-development`.

---

### Slice 22 — Hierarchical + Parallel Processes

**Goal:** Opt-in support for CrewAI `Process.hierarchical` and task-level `async_execution=True`, so workflows can express manager/specialist delegation and concurrent task execution. Emits `waiting_on_agent` events via the state bus.

**Non-goals:** Supporting arbitrary DAGs (we allow `parallel_tasks: list[list[TaskSpec]]` only — each inner list runs concurrently, inner lists run sequentially); auto-detecting when to go hierarchical.

**Files changed:**
- `src/workflows/base.py` — add `process: Literal["sequential","hierarchical"]`, `manager_agent: str | None`, `parallel_tasks: list[list[str]] | None`.
- `src/crew.py` — when `process="hierarchical"`, enable `allow_delegation=True` on participating agents (overriding the project-wide default from DEC-13) and pass the manager agent. When `parallel_tasks` is set, mark those tasks with `async_execution=True`.
- `src/services/state_bus.py` — emit `waiting_on_agent` when a task's dependency (prior task's agent) is still in `active`/`waiting_on_tool`.

**Files created:**
- `tests/unit/test_hierarchical_process.py`
- `tests/unit/test_parallel_tasks.py`

**Test plan (RED):**
1. `test_hierarchical_crew_builds_with_manager`
2. `test_hierarchical_respects_workflow_opt_in_only` — sequential workflows still have `allow_delegation=False` (DEC-13 remains default).
3. `test_parallel_tasks_build_sets_async_execution_true`
4. `test_state_bus_emits_waiting_on_agent_for_blocked_subtask` (with mocked CrewAI runtime)
5. `test_hierarchical_unknown_manager_raises_configuration_error`
6. `test_parallel_tasks_fan_in_completes_in_expected_order`

**Acceptance criteria:**
- A synthetic test workflow with two parallel tasks shows both agents `active` simultaneously in the state bus.
- A synthetic hierarchical workflow shows manager → delegate → return events.
- Existing `research_report` (sequential) is unchanged.

**Risks & mitigations:**
- **CrewAI sequential + delegation crashes** (root cause of DEC-13). Mitigation: delegation is only enabled when `process="hierarchical"`; unit test asserts the sequential path keeps `allow_delegation=False`.
- **Parallel tasks race on shared mutable state** (tools, embedders). Mitigation: `QdrantRepository` is already thread-safe (slice-2 singleton); no other shared mutables; add a regression test that runs two parallel tasks with the search tool.
- **`async_execution=True` behavior changes between CrewAI versions.** Mitigation: invoke `source-driven-development` skill to verify against the current CrewAI docs at build time.

**Skills:** `source-driven-development` (CrewAI hierarchical + async), `test-driven-development`, `debugging-and-error-recovery`.

---

### Slice 23 — Business Workflow Pack 1 (Sales)

**Goal:** Two demo-ready sales workflows: `lead_qualifier` and `sdr_outreach`.

**Non-goals:** CRM integration (HubSpot/Salesforce); automated email sending (we only produce drafts).

**Workflow specs:**

- **`lead_qualifier`** — Sequential, 3 agents:
  1. `researcher` — web_search + document_search to gather company signals
  2. `scorer` — applies ICP rubric (employee count, funding stage, tech stack, pain-point match); returns 0-100 score with per-criterion breakdown
  3. `report_writer` — structured JSON report + executive summary
  - Input: `topic="Acme Corp"`, `domain="general"` (or user's vertical)
  - Output: `{company, score, reasoning, recommended_next_action, evidence_links}`

- **`sdr_outreach`** — Parallel drafting, 4 agents, `process=sequential` with `parallel_tasks=[["copywriter_a","copywriter_b","copywriter_c"]]`:
  1. `persona_researcher` (first, solo) — produces persona sketch
  2. `copywriter_a`, `copywriter_b`, `copywriter_c` (parallel) — each writes one draft with a different tone (formal/casual/provocative)
  3. `tone_checker` (last, solo) — picks the best variant with justification
  - Output: `{chosen_variant, all_variants, justification, recommended_subject_line}`

**Files created:**
- `src/workflows/lead_qualifier.py`
- `src/workflows/sdr_outreach.py`
- `src/config/agents.yaml` — extend with `scorer`, `report_writer`, `persona_researcher`, `copywriter`, `tone_checker` agent roles.
- `tests/unit/test_lead_qualifier_workflow.py`
- `tests/unit/test_sdr_outreach_workflow.py`
- `docs/demos/sales.md` — 5-minute pitch script using the Acme Corp demo scenario.

**Test plan (RED):**
1. `test_lead_qualifier_output_has_score_in_range`
2. `test_lead_qualifier_output_matches_schema` (Pydantic validation)
3. `test_sdr_outreach_produces_three_distinct_variants` (variants differ by non-trivial diff)
4. `test_sdr_outreach_tone_checker_picks_one_variant`
5. `test_sales_workflows_listed_in_registry`

(Tests use mocked LLM via `DEMO_MODE=true` or pytest fixtures returning deterministic outputs.)

**Acceptance criteria:**
- `POST /crew/run workflow=lead_qualifier topic="Acme Corp"` returns a scored-report task that completes with a schema-valid JSON result.
- `POST /crew/run workflow=sdr_outreach topic="CTO at ACME"` returns 3 variants + pick.
- Dashboard live view shows parallel cards for the three copywriters.
- `docs/demos/sales.md` contains exact click-by-click steps.

**Risks & mitigations:**
- **Local Ollama (qwen3:8b) may produce low-quality scores.** Mitigation: demo script uses `DEMO_MODE=true` when running for stakeholders; fake LLM returns curated sample outputs.
- **Scoring rubric drift.** Mitigation: rubric lives in `src/workflows/lead_qualifier.py` as a module constant; unit test asserts schema + range.

**Skills:** `incremental-implementation`, `test-driven-development`, `source-driven-development` (CrewAI patterns).

---

### Slice 24 — Business Workflow Pack 2 (Support & Ops)

**Goal:** Two workflows that show off hierarchical + parallel respectively: `support_triage` (hierarchical) and `meeting_prep` (parallel).

**Non-goals:** Integrating real ticketing systems (Zendesk, Intercom); calendar API integration for meeting prep (we consume free-text attendee list).

**Workflow specs:**

- **`support_triage`** — Hierarchical, manager + 3 specialists:
  - Manager: `triage_manager` delegates to:
    - `kb_searcher` — queries RAG
    - `sentiment_analyst` — classifies urgency/emotion
    - `response_writer` — drafts the reply
  - Output: `{category, urgency, suggested_response, kb_sources}`
  - Demoable as a hierarchical crew where the dashboard shows the manager delegating.

- **`meeting_prep`** — Sequential + parallel, 4 agents:
  1. `attendee_researcher` and `topic_researcher` run in **parallel** on the same input
  2. `agenda_writer` runs after both complete
  3. `talking_points_writer` runs last
  - Output: `{attendees:[{name, bio}], topic_summary, agenda, talking_points}`

**Files created:**
- `src/workflows/support_triage.py`
- `src/workflows/meeting_prep.py`
- `src/config/agents.yaml` — extend with `triage_manager`, `kb_searcher`, `sentiment_analyst`, `response_writer`, `attendee_researcher`, `topic_researcher`, `agenda_writer`, `talking_points_writer`.
- `tests/unit/test_support_triage_workflow.py`
- `tests/unit/test_meeting_prep_workflow.py`
- `docs/demos/support.md`

**Test plan (RED):**
1. `test_support_triage_uses_hierarchical_process`
2. `test_support_triage_output_schema_matches` (category, urgency, reply, sources)
3. `test_meeting_prep_parallel_tasks_configured`
4. `test_meeting_prep_agenda_depends_on_both_researchers` (state-bus trace)
5. `test_support_triage_registered`, `test_meeting_prep_registered`

**Acceptance criteria:**
- Dashboard shows manager card + 3 specialist cards for `support_triage`.
- Dashboard shows 2 parallel researcher cards for `meeting_prep`, then agenda_writer, then talking_points_writer.
- Both demoable from `docs/demos/support.md`.

**Risks & mitigations:**
- **Manager agent LLM overhead doubles the run.** Mitigation: note in docs/demos/support.md that hierarchical is demoed with `DEMO_MODE=true` for speed; also documented in DEC-19.
- **Parallel attendees/topics race on Qdrant search.** Mitigation: covered by slice 22 regression test.

**Skills:** `incremental-implementation`, `test-driven-development`, `source-driven-development`.

---

### Slice 25 — Business Workflow Pack 3 (Content & Real Estate)

**Goal:** Two vertical-specific workflows: `content_pipeline` (sequential, showcases an editorial pipeline) and `real_estate_cma` (parallel, uses the existing `real_estate` domain seed data).

**Non-goals:** Publishing content to a CMS (just produces markdown); live MLS data (uses seeded/manually-ingested comparables).

**Workflow specs:**

- **`content_pipeline`** — Sequential: `researcher → outliner → writer → editor → seo_optimizer`
  - Output: `{title, meta_description, outline, body_markdown, seo_suggestions, readability_score}`

- **`real_estate_cma`** — Sequential + parallel: `parallel_tasks=[["comps_gatherer","market_analyst"]]` → `appraiser` → `report_writer`
  - Input: `topic="123 Main St, Any City, TX"` (consumes RAG seed for that domain)
  - Output: `{subject_property, comparables, market_trend, estimated_value_range, confidence, report_pdf_ready}`

**Files created:**
- `src/workflows/content_pipeline.py`
- `src/workflows/real_estate_cma.py`
- `src/config/agents.yaml` — extend with `outliner`, `editor`, `seo_optimizer`, `comps_gatherer`, `market_analyst`, `appraiser`.
- `tests/unit/test_content_pipeline_workflow.py`
- `tests/unit/test_real_estate_cma_workflow.py`
- `docs/demos/verticals.md`

**Test plan (RED):**
1. `test_content_pipeline_output_schema`
2. `test_content_pipeline_markdown_contains_outline_headers`
3. `test_cma_parallel_gather_and_market`
4. `test_cma_estimated_value_range_has_low_and_high`
5. Both workflows registered.

**Acceptance criteria:**
- Both workflows runnable from the dashboard; dashboard visualizes parallel + sequential phases correctly.
- `docs/demos/verticals.md` has a scripted pitch for each.

**Risks & mitigations:**
- **RAG seed for real_estate may be too thin for a convincing demo.** Mitigation: extend `src/config/seeds/real_estate.yaml` (if needed) during this slice — but that's one-line additions, not a full re-seed.

**Skills:** `incremental-implementation`, `test-driven-development`.

---

### Slice 26 — Voice-Capable Receptionist (Twilio trial)

**Goal:** Ship a `receptionist` workflow that places an outbound phone call, conducts a short turn-based conversation via TwiML webhooks, and returns a structured post-call summary. Live calls gated behind `VOICE_ENABLED=true` and TCPA guardrails.

**Non-goals:** Inbound IVR menus; call recording + transcription storage; paid Twilio tier; any non-English locale; production-grade number verification (trial-only: pre-verified numbers).

**Workflow spec — `receptionist`** (sequential, 3 agents):
1. `intake_agent` — parses the user's request ("book a table for 4 at 7pm at Luigi's") into structured call parameters.
2. `caller_agent` — invokes `VoiceCallTool`, which kicks off `twilio.rest.Client.calls.create(to, from, url=TWILIO_WEBHOOK_BASE/voice/twiml/{task_id})`. Each time Twilio hits our webhook, the agent's next utterance is generated and returned as TwiML (`<Say>` + `<Gather input="speech">`). The conversation state is stored per `task_id` in the TaskStore.
3. `summary_agent` — writes the post-call report from the transcript.

**Files created:**
- `src/tools/voice.py` — `VoiceCallTool` registered in the tool registry; when `VOICE_ENABLED=false`, the tool is available but raises `VoiceDisabledError` if called.
- `src/workflows/receptionist.py`
- `src/services/voice_session.py` — per-task conversation state machine (turns, last-question, captured speech).
- `tests/unit/test_voice_tool.py`
- `tests/unit/test_receptionist_workflow.py`
- `tests/unit/test_twiml_webhook.py`
- `tests/integration/test_twilio_live.py` — marked `@pytest.mark.voice` (opt-in).
- `docs/demos/voice.md` — ngrok + Twilio signup instructions + TCPA checklist.

**Files changed:**
- `src/main.py` — `POST /voice/twiml/{task_id}` (form-urlencoded body from Twilio, returns `text/xml`), skip API key auth on this route but verify Twilio signature via `TWILIO_AUTH_TOKEN` (see security section below).
- `src/config/settings.py` — `VOICE_ENABLED: bool = False`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `TWILIO_WEBHOOK_BASE`, `TWILIO_VERIFIED_TO_NUMBERS: list[str] = []`.
- `src/models/schemas.py` — `CrewRunRequest.voice: VoiceOptions | None` (nested: `to`, `max_turns=6`, `max_duration_s=120`).
- `pyproject.toml` — add `twilio` dep.
- `README.md` — Voice Demo section with TCPA notice.

**Test plan (RED):**
1. `test_voice_tool_disabled_by_default_raises` (unit)
2. `test_voice_tool_enabled_calls_twilio_with_expected_args` (mocked Twilio client)
3. `test_twiml_webhook_returns_valid_xml`
4. `test_twiml_webhook_rejects_unsigned_request` (Twilio signature verification)
5. `test_twiml_webhook_rejects_unknown_task_id`
6. `test_twiml_webhook_ends_call_after_max_turns`
7. `test_voice_request_to_number_not_in_verified_list_rejected_422`
8. `test_receptionist_workflow_produces_summary_when_call_completes_mocked`
9. **Integration (opt-in):** `test_twilio_live_call_roundtrip` — real call, asserts transcript captured.

**Acceptance criteria:**
- All 8 unit tests green with mocked Twilio; no network calls in unit tests.
- `VOICE_ENABLED=false` → any attempt to dial raises 422 before calling Twilio.
- Manual (optional, gated): Armando sets env, runs ngrok, runs `POST /crew/run workflow=receptionist voice.to=<his verified number>`, receives a call, agent speaks, he answers, call ends, summary appears.
- `docs/demos/voice.md` has a "15-minute first-call setup" with exact commands.

**Risks & mitigations:**
- **TCPA compliance.** Mitigation: only call numbers in `TWILIO_VERIFIED_TO_NUMBERS` (checked by the `POST /crew/run` validator); big banner in README + `docs/demos/voice.md`; DEC-22 enforces `VOICE_ENABLED=false` default.
- **Unsigned webhook spoofing.** Mitigation: verify `X-Twilio-Signature` HMAC on every `POST /voice/twiml/{task_id}` using `TWILIO_AUTH_TOKEN`; unit test 4 above locks this in.
- **Twilio trial credit exhaustion mid-demo.** Mitigation: `MAX_DURATION_S=120` hard cap; Telnyx documented as fallback in DEC-21 (not wired in v4.0).
- **Local Ollama latency > Twilio's 5-second webhook timeout.** Mitigation: `caller_agent` precomputes the next-utterance *before* Twilio asks (we respond with the already-generated line); fallback TwiML says "one moment" and redirects to itself.
- **RAM constraint (qwen3:8b).** Mitigation: `receptionist` workflow has only 3 lightweight agents; responses are short (≤ 50 words per turn).

**Skills:** `security-and-hardening` (webhook signature, TCPA guard), `source-driven-development` (Twilio Python SDK docs), `test-driven-development`, `api-and-interface-design`.

---

### Slice 27 — Shareable read-only run page + PDF export

**Goal:** Any completed run can be turned into a public read-only URL (HMAC-signed, 7-day TTL) and a downloadable PDF. Also covers what was scoped as slice 20d.

**Non-goals:** Per-user share revocation (rotation of `SHARE_SECRET` is the only revocation); PDF internationalization; watermarking.

**Files created:**
- `src/services/share_token.py` — `mint(task_id, ttl_seconds=7*24*3600) -> str`, `verify(token) -> task_id | raise Expired/Invalid`.
- `src/services/pdf_export.py` — Jinja-rendered HTML → WeasyPrint PDF.
- `src/templates/run_report.html` — PDF template.
- `tests/unit/test_share_token.py`
- `tests/unit/test_share_route.py`
- `tests/unit/test_pdf_export.py`
- Frontend: `dashboard/app/share/[token]/page.tsx` (reuses 20c components in read-only mode).

**Files changed:**
- `src/main.py` — `GET /share/{token}` (public, no auth; returns HTML render of the run), `GET /crew/history/{task_id}/pdf` (auth required, returns `application/pdf`).
- `src/config/settings.py` — `SHARE_SECRET: str | None` (required when env=production; auto-generated in dev with warning).
- `src/services/sqlite_store.py` — add `agent_events` table (`task_id`, `agent_role`, `state`, `detail`, `ts`); `save_event()` + `replay(task_id)` methods; wire into state bus so events persist.
- `pyproject.toml` — add `weasyprint` dep.

**Test plan (RED):**
1. `test_token_mint_and_verify_roundtrip`
2. `test_token_tampered_fails_verification`
3. `test_token_expired_raises`
4. `test_share_route_valid_token_returns_200_html`
5. `test_share_route_invalid_token_returns_403`
6. `test_share_route_expired_token_returns_410`
7. `test_share_route_unknown_task_id_returns_404`
8. `test_pdf_export_returns_valid_pdf_bytes` (PDF magic header)
9. `test_pdf_export_requires_api_key`
10. `test_agent_events_table_replay_is_in_chronological_order`

**Acceptance criteria:**
- After any run completes, Armando can copy a share URL and open it in a private/incognito window — full run renders, no auth prompt.
- Rotating `SHARE_SECRET` invalidates all outstanding tokens (manual step).
- PDF downloads cleanly from the dashboard (`/runs/{id}` → Export PDF button).
- Replay: `/share/{token}` reconstructs the timeline from `agent_events` even after a server restart.

**Risks & mitigations:**
- **Signed-URL secret leaked in logs.** Mitigation: tokens never logged; error paths log `task_id` only.
- **WeasyPrint native deps on Apple Silicon.** Mitigation: WeasyPrint 62 supports arm64 via Homebrew `pango`, `cairo`, `gdk-pixbuf`; documented in README.
- **Unbounded storage of `agent_events`.** Mitigation: rows keyed by `task_id`, TTL cleanup same as SQLite results table (90 days; configurable).
- **Read-only page leaks sensitive details.** Mitigation: `/share/{token}` renders a whitelist of fields only (status, agent timeline, final result) — not raw tool I/O, not user-API keys, not webhook URLs. Test 4 asserts the whitelist.

**Skills:** `security-and-hardening` (HMAC, secret rotation, CSP), `api-and-interface-design`, `test-driven-development`.

---

### Slice 28 — Demo Harness (deterministic pitch mode)

**Goal:** A `DEMO_MODE=true` switch that substitutes the live LLM with a deterministic fixture-backed fake, plus a `scripts/demo.py` CLI and a Chainlit "Run demo" action. Pitches now play the same way every single time.

**Non-goals:** Recording/replaying real LLM calls (no HTTP fixture cassettes); UI themeing for demos.

**Files created:**
- `src/demo/__init__.py`
- `src/demo/fake_llm.py` — LiteLLM-compatible fake (patches `LLMFactory.create()` when `DEMO_MODE=true`). Looks up responses by `(workflow, topic, agent_role, task_index)`; raises a clear error on cache miss (so missing fixtures are noisy, not silent).
- `src/demo/scenarios.yaml` — one entry per canned scenario: `lead-qualifier-acme`, `support-triage-refund`, `sdr-outreach-cto`, `meeting-prep-monday`, `content-pipeline-blog`, `cma-123-main`, `receptionist-book-table`.
- `src/demo/fixtures/<scenario>/<agent_role>.md` — one fixture per agent per scenario.
- `scripts/demo.py` — CLI: `--scenario`, `--list`, `--dry-run`.
- `tests/unit/test_demo_scenarios.py`
- `tests/unit/test_demo_button.py`
- `tests/unit/test_fake_llm.py`

**Files changed:**
- `src/config/settings.py` — `DEMO_MODE: bool = False`.
- `src/llm/factory.py` — `if settings.demo_mode: return FakeLLM(...)`.
- `src/chainlit_app.py` — "Run demo" `cl.Action` that lists scenarios from `scenarios.yaml` and POSTs to the API with `DEMO_MODE=true` semantics.
- `dashboard/app/page.tsx` — "Run Demo" button next to Launch when `NEXT_PUBLIC_DEMO_ENABLED=true`.

**Test plan (RED):**
1. `test_demo_mode_off_uses_live_llm`
2. `test_demo_mode_on_uses_fake_llm`
3. `test_fake_llm_returns_fixture_for_known_key`
4. `test_fake_llm_raises_on_missing_fixture`
5. `test_demo_script_runs_scenario_deterministically` — runs the scenario twice, asserts byte-identical outputs
6. `test_demo_list_outputs_all_scenarios`
7. `test_chainlit_run_demo_action_triggers_scenario`

**Acceptance criteria:**
- `python scripts/demo.py --scenario lead-qualifier-acme` produces identical stdout+exit code twice in a row.
- `/` dashboard's "Run Demo" button (when enabled) runs one of the canned scenarios end-to-end with the live team view lighting up.
- `scripts/demo.py --list` prints all 7 scenarios + descriptions.
- Missing fixture raises a clear error naming the missing key (so Armando can't accidentally ship a scenario that falls back to live LLM).

**Risks & mitigations:**
- **Fixtures drift from real LLM output.** Mitigation: demos intentionally use fixtures, not live LLM output; the point is reproducibility, not authenticity. README and `docs/demos/*.md` say so explicitly.
- **Fake LLM masks real bugs.** Mitigation: `DEMO_MODE` is off by default; CI runs tests with `DEMO_MODE=false` for everything except the dedicated demo-mode tests above.

**Skills:** `test-driven-development`, `incremental-implementation`.

---

## Phase 4 Workflow Protocol

For each Phase 4 slice, follow the v2 protocol **verbatim** (Step 1 `/plan` the slice → Step 2 `/test` RED → Step 3 `/build` GREEN → Step 4 `/review` → Step 5 Commit). Additions for Phase 4:

- **Dashboard slices (20a/b/c):** `/test` RED means Vitest + Playwright green on negative cases; `/build` GREEN is typed components + passing snapshots.
- **Voice slice (26):** never toggle `VOICE_ENABLED=true` in CI. Live call verification is a manual step Armando does once.
- **Demo slice (28):** every new business workflow (23-25) adds one fixture set to `src/demo/fixtures/` as part of that slice so the demo harness stays in sync.

---

## Phase 4 Risk Register

| Risk | Likelihood | Mitigation | Owner |
|------|-----------|------------|-------|
| CrewAI step_callback thread → asyncio bus race | Medium | Covered by slice 19 tests 1-5 | Slice 19 |
| Next.js hydration mismatch breaks SSE | Low | Slice 20c uses client components; StrictMode test | Slice 20c |
| Delegation re-enabled breaks sequential workflows | Medium | Slice 22 test asserts sequential keeps delegation off | Slice 22 |
| TCPA violation during voice demo | Medium-High | Verified-number whitelist + README banner + DEC-22 | Slice 26 |
| Twilio webhook spoofing | Medium | X-Twilio-Signature HMAC check (test 4 in slice 26) | Slice 26 |
| Share link leaks sensitive run data | Medium | Whitelisted render (test 4 in slice 27); rotating secret | Slice 27 |
| Fake LLM hides production bugs | Low | `DEMO_MODE=false` default; CI runs real tests | Slice 28 |
| WeasyPrint native deps on Apple Silicon | Low | Documented brew deps in README | Slice 27 |
| Port 3061 collision | Low | Check PORTS.md before slice 20a | Slice 20a |
| SSE buffering through reverse proxy | Low (no proxy in dev) | `X-Accel-Buffering: no` header; no gzip | Slice 19 |

---

## Phase 4 Success Criteria

- [ ] Slices 19-28 implemented, tested, committed on `main` (one commit per slice).
- [ ] All v2-era tests (152) still green. All new v4 tests green.
- [ ] `docker compose -f docker-compose.dev.yml up` boots 4 services healthy.
- [ ] `http://localhost:3061` launcher runs every one of the 7 new workflows end-to-end in `DEMO_MODE=true`.
- [ ] Live team view (`/runs/{id}`) shows real-time state for both sequential and parallel workflows.
- [ ] Share link + PDF export round-trip tested for at least one completed run.
- [ ] Voice slice unit tests green; opt-in live call round-trip verified manually at least once.
- [ ] `docs/demos/*.md` exists for dashboard, sales, support, verticals, voice — each with a scripted 5-min pitch.
- [ ] DEC-16…DEC-28 (+26a/26b) written to DECISIONS.md.
- [ ] README v4 updates committed (capability table, demo links, voice section).

---

## Phase 4 Open Questions

None. All 13 new design decisions are captured in DEC-16…DEC-28 in [DECISIONS.md](DECISIONS.md). Two choices that required user input (voice-slice scope, dashboard stack) were resolved during the plan-mode brainstorm on 2026-04-16 and are recorded at the top of the source plan file.

---

## Next Step

After this spec is reviewed, the next command is:

```
/plan SPEC.md Phase 4 — slices 19-28. Break each slice into TDD sub-tasks (RED test → GREEN implementation → refactor → commit). Reference DEC-16..DEC-28 in DECISIONS.md. Write PLAN.md with task order, dependencies, and per-task acceptance + verify steps. Respect the approved plan at ~/.claude/plans/analyze-the-current-state-temporal-quilt.md as the source of truth. Docker + TDD + vertical slices only; no /ship. End with the /build prompt for slice 19.
```

(The earlier v2 `/plan` prompt above remains for historical reference.)

---

# v4.1 — Graph Team View

> **Baseline:** commit `4d250e2` on `main` (Phase-4 hardening landed 2026-04-16)
> **Status:** Spec written 2026-04-16. Implementation not started.
> **Source review:** Phase-4 five-axis review UI/UX brainstorm.

---

## v4.1 Objective

Replace the static **kanban** on `/runs/[id]` with a live **node-and-edge graph** that makes the multi-agent system feel like a living thing during pitches. Same agents + same SSE backbone as Phase 4 — only the front-door UX changes.

**Success looks like:** a prospect watching `http://localhost:3061/runs/…` sees a graph identical in structure to what they'd sketch on a whiteboard — each agent a node, each dependency an edge — with a pulsing halo on the active node, a shimmering edge toward the next node, a small "packet" dot sliding along that edge when a task completes, and a transcript pane on the right streaming the agent's text output in real time. When the run finishes, a scrubber at the bottom of the share page lets them replay the full sequence frame-by-frame.

**Why not ship Phase 4 as-is:** the kanban reads as "wireframe" to reviewers. The graph view communicates *structure and flow* in 2 seconds — which is what the pitch is actually selling.

---

## v4.1 Goals and Non-Goals

### Goals

- **Node-and-edge graph** replaces the kanban for live runs (kanban stays available behind a view toggle for operators who want compact monitoring).
- **Workflow-aware layout** — sequential = left-to-right pipeline, parallel = fork/join, hierarchical = tree with manager on top. Derived from the registry; no hand-authored positions.
- **Live state** — active-node halo, edge shimmer, packet-dot animation, waiting-node dimming, failed-node error state.
- **Transcript pane** — right-side live stream of per-agent output with auto-scroll, collapsible sections.
- **Scrubber on share page** — time-series replay through `agent_events` so stakeholders can re-watch a run after the fact.
- **Dual-pane layout** by default on desktop (graph left, transcript right); stacked on mobile.

### Non-Goals (v4.1)

- Workflow editor (drag-to-edit agents + edges) — tracked as v4.2 if there's demand.
- Backend schema changes — all animation is derived client-side from the existing SSE + registry surfaces.
- Any new voice/Twilio work. Deferred Important items from the Phase-4 review (I2-I6) also stay deferred.
- Multi-run comparison view.
- Collaborative cursors / multi-user dashboards.
- Backward-compat shim for the kanban — it's demoted to a "Board" toggle, not removed.

---

## v4.1 Architecture Changes

### New runtime topology

```
┌─────────────────────────────────────────────────────────────────┐
│  Next.js Dashboard (:3061)                                       │
│                                                                   │
│  /runs/[id]                     /share/[token]                   │
│  ┌──────────────────────┐       ┌──────────────────────┐         │
│  │ Graph    │ Transcript │       │ Graph    │ Transcript│         │
│  │  pane    │   pane     │       │  pane    │  pane     │         │
│  │          │            │       │          │           │         │
│  │ React    │ Per-agent  │       │ React    │ Per-agent │         │
│  │ Flow     │ stream     │       │ Flow     │ stream    │         │
│  │          │            │       │          │           │         │
│  └──────────┴────────────┘       │ ── Scrubber ──       │         │
│                                  └──────────────────────┘         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
              │                                  │
              │ SSE (live)                       │ HTML replay
              ▼                                  ▼
        FastAPI :8060                     FastAPI :8060
        /crew/run/{id}/events             /share/{token}
                                          (replays agent_events table)
```

### Graph topology derivation (client-side)

A new `lib/graph.ts` converts the `WorkflowInfo` returned by `GET /workflows` into React Flow's `nodes[]` + `edges[]`:

```
Workflow metadata                          Graph output
─────────────────                          ──────────────
name: "support_triage"                     nodes:
process: "hierarchical"                      - triage_manager  (kind: manager)
manager_agent: "triage_manager"              - kb_searcher     (kind: specialist)
agent_roles: [triage_manager,                - sentiment_analyst
               kb_searcher,                   - response_writer
               sentiment_analyst,           edges:
               response_writer]               - manager → kb_searcher  (kind: delegation)
task_names: [triage_route, kb_search,        - manager → sentiment_analyst
             sentiment_analyze,               - manager → response_writer
             response_draft]
parallel_tasks: null

name: "meeting_prep"                       nodes:
process: "sequential"                        - attendee_researcher
parallel_tasks:                              - topic_researcher
  - [attendee_research,                      - agenda_writer
     topic_research]                         - talking_points_writer
agent_roles: [attendee_researcher,         edges:
              topic_researcher,              - attendee_researcher → agenda_writer (fan-in)
              agenda_writer,                 - topic_researcher    → agenda_writer (fan-in)
              talking_points_writer]         - agenda_writer       → talking_points_writer
```

The layout engine is **dagre** (`@dagrejs/dagre`) — rank-based directed acyclic graph layout. It's the same engine React Flow's official examples use; zero custom math.

### Layout rules (derived from `process` + `parallel_tasks`)

| Process | Layout |
|---|---|
| `sequential` with no `parallel_tasks` | Single rank per task; left-to-right pipeline. |
| `sequential` with `parallel_tasks` | Tasks in the same parallel group share a rank; downstream tasks wait at the next rank (visual fan-in). |
| `hierarchical` | Manager at rank 0, specialists at rank 1, fan-out edges. Task-wise edges follow order. |

### Node-state contract

| State | Visual | Source |
|---|---|---|
| `queued` | Dim, slate border, no glow | No event yet, or pre-run |
| `active` | Indigo halo, pulsing ring (2s loop) | Latest event for this role has `state=active` or `waiting_on_tool` |
| `waiting_on_tool` | Amber halo, spinner icon | Latest event state |
| `waiting_on_agent` | Amber border, faded (60% opacity) | Latest event state (blocked on upstream) |
| `completed` | Indigo solid, check glyph | Latest event state |
| `failed` | Rose border, ✕ glyph, subtle shake animation | Latest event state |

The node is the standard `AgentCard` reused from Phase 4, wrapped as a custom React Flow node. Its **halo** is a CSS pseudo-element with `box-shadow` + `@keyframes` pulse.

### Edge-animation contract

Edges respond to *state transitions* on their source node (client-side derivation — no backend change):

| Edge state | Trigger | Visual |
|---|---|---|
| `idle` | Neither endpoint has fired yet | 1px slate stroke, 40% opacity |
| `armed` | Source node is active; target is queued | 1.5px slate stroke, 80% opacity |
| `firing` | Source completed AND target became active within the last 3s | Animated dashed stroke (stroke-dashoffset shimmer), indigo hue, 2px |
| `packet` | Source completed and target is about to activate | A small circle (SVG `<circle>` animated via `framer-motion`'s `path` prop) travels from source handle to target handle over 600ms |
| `completed` | Both endpoints are in a terminal state | 1.5px indigo stroke, 100% opacity, no animation |

A React hook `useGraphState(events)` consumes the same event array as `useAgentEvents` and derives `{nodeStates, edgeStates}` as a memoized reducer. Same hook serves the live run and the share-page replay — the only difference is `events` is bounded by the scrubber index on the share page.

### Transcript pane

Right-hand 380px column on desktop, full-width bottom drawer on mobile.

- One expandable section per agent (role icon + name + state chip).
- Each section streams that agent's `detail` fields as lines with timestamps.
- Current speaker (latest event's `agent_role`) is highlighted with a subtle left-border.
- Auto-scrolls to the latest entry unless the user has scrolled up manually (IntersectionObserver on the "latest" marker).
- Tool calls render inline as chips: `[web_search] AI in healthcare 2026`.
- Collapsible "Crew" lifecycle section at the top for crew-level events.
- Copy-all button for each agent so a prospect can grab an agent's output.

### Scrubber (share page only)

On `/share/[token]`, the fetched HTML from the backend stays (slice-27 still works). Above the graph, a compact scrubber:

```
────●─────────────────────── 47 / 119 events · 14:23
```

- Drag to replay the graph/transcript through any prefix of events.
- Play/pause button re-plays at real-time speed (derived from `ts` deltas, 2× cap).
- "Jump to failure" shortcut if any event has `state=failed`.
- Keyboard: `←` / `→` step one event, `space` play/pause.
- Renders from the `agent_events` already persisted by slice-27.

### Component topology

```
dashboard/
  app/runs/[id]/page.tsx            unchanged route
    └─ <RunView taskId/>            reusable shell
        ├─ <ViewToggle/>            toggle: graph (default) | board
        ├─ <GraphPane/>              ← NEW — React Flow
        │   ├─ <AgentNode/>          custom node component (reuses AgentCard)
        │   ├─ <EdgeAnimated/>       custom edge component
        │   ├─ <MiniMap/>            React Flow built-in
        │   └─ <Controls/>           pan, zoom, fit-view
        ├─ <TranscriptPane/>         ← NEW
        │   ├─ <CrewLifecycleFeed/>
        │   └─ <AgentTranscriptSection/> (one per agent)
        └─ <KanbanPane/>             existing kanban, opt-in via ViewToggle
  app/share/[token]/page.tsx         gains <Scrubber/> above the shell
  lib/graph.ts                       ← NEW — workflow → nodes/edges + dagre layout
  lib/useGraphState.ts               ← NEW — event[] → {nodeStates, edgeStates}
```

---

## v4.1 Tech Stack Additions

| Component | Version | Why |
|-----------|---------|-----|
| `@xyflow/react` | 12.x | Node-graph renderer (DEC-29) |
| `@dagrejs/dagre` | 1.x | Automatic rank-based layout |
| `framer-motion` | already installed | Packet-dot motion along edge |
| `use-debounce` | 10.x | Scrubber drag debouncing (optional) |

**Dependencies removed:** none. Kanban components stay as a toggle; deletion deferred to v4.2.

---

## v4.1 Commands Additions

```bash
# Dashboard
cd dashboard
npm install                       # pulls @xyflow/react, dagre
npm run dev                       # http://localhost:3000 (docker: 3061)
npm test                          # Vitest — includes graph reducer tests
npm run test:e2e                  # Playwright — live run renders graph

# Storybook (if we add it — open question)
# npm run storybook              # port 6006 — visual regression for nodes/edges
```

---

## v4.1 Project Structure Additions

```
dashboard/
  app/
    runs/[id]/page.tsx             (modified) — adds <ViewToggle/>
    share/[token]/page.tsx         (modified) — adds <Scrubber/>
  components/
    GraphPane.tsx                  (NEW) — React Flow canvas
    AgentNode.tsx                  (NEW) — custom node
    EdgeAnimated.tsx               (NEW) — custom edge (shimmer + packet)
    TranscriptPane.tsx             (NEW)
    AgentTranscriptSection.tsx     (NEW) — per-agent feed
    Scrubber.tsx                   (NEW) — share-page replay
    ViewToggle.tsx                 (NEW) — graph vs board
  lib/
    graph.ts                       (NEW) — WorkflowInfo → nodes[]/edges[]
    useGraphState.ts               (NEW) — reducer hook
    dagreLayout.ts                 (NEW) — pure layout fn (easy to test)
  __tests__/
    graph-topology.test.ts         (NEW) — 7 cases covering all process types
    use-graph-state.test.ts        (NEW) — reducer under scripted events
    transcript-pane.test.tsx       (NEW) — autoscroll, collapse, copy
    scrubber.test.tsx              (NEW) — drag, play/pause, keyboard
  e2e/
    graph-run.spec.ts              (NEW) — run from launcher → graph animates
    scrubber.spec.ts               (NEW) — share page scrubber round-trip
```

No backend files change in v4.1 — the SSE + registry surfaces already provide everything the client needs.

---

## v4.1 Vertical Slices

Each slice: goal → non-goals → files → test plan (RED) → acceptance criteria → risks → skills. Each ends with a single `feat(slice-29x): …` commit.

### Slice 29a — Workflow graph topology (static render)

**Goal:** Given a `WorkflowInfo`, render a correct graph (nodes + edges + dagre layout) on the run page. No animation yet; states are all `idle`. Toggle kanban/graph view.

**Non-goals:** Live SSE updates (slice 29b); transcript pane (29c); share-page scrubber (29d).

**Files created:**
- `dashboard/lib/graph.ts` — `buildGraph(workflow: WorkflowInfo): {nodes, edges}`. Pure fn.
- `dashboard/lib/dagreLayout.ts` — `layoutNodes(nodes, edges, direction='LR')`. Pure fn.
- `dashboard/components/GraphPane.tsx` — React Flow canvas + fit-view + minimap + controls.
- `dashboard/components/AgentNode.tsx` — custom node reusing AgentCard visual but stripped down for the graph context.
- `dashboard/components/EdgeAnimated.tsx` — custom edge (idle only in this slice).
- `dashboard/components/ViewToggle.tsx` — graph (default) ↔ board.
- `dashboard/__tests__/graph-topology.test.ts` — 7 cases:
  1. Sequential workflow → N nodes, N-1 edges, ranks increment left-to-right.
  2. Parallel workflow → fan-out + fan-in edges at the right ranks.
  3. Hierarchical workflow → manager at rank 0, specialists at rank 1, delegation edges.
  4. Sequential + parallel mixed (meeting_prep) → correct topology.
  5. Unknown process string → throws with a helpful message.
  6. Empty `task_names` → empty graph (no crash).
  7. Dagre `layoutNodes` produces distinct x/y for every node (no overlap).

**Test plan (RED):**
1. Vitest `graph-topology.test.ts` (7 cases above).
2. Playwright `graph-run.spec.ts` — launches a `DEMO_MODE=true` research_report run, opens `/runs/[id]`, asserts the graph canvas has 4 node elements with the expected aria-labels.

**Acceptance:**
- Running any of the 7 registered workflows renders a graph with the correct topology.
- View toggle preserves scroll position + task_id.
- `npm test` green; `npm run test:e2e` green.

**Risks & mitigations:**
- **React Flow's React 19 compat:** verify `@xyflow/react@12` works with React 19.2 before any other code (install + Hello World). Mitigation: if incompatible, pin to React 18 or switch to `reactflow@11`.
- **Dagre SSR hydration:** dagre is CPU-only; safe in a client component. Mitigation: mark `GraphPane` `"use client"`.

**Skills:** `frontend-ui-engineering`, `source-driven-development` (verify @xyflow/react 12 + dagre API), `test-driven-development`.

---

### Slice 29b — Live animation (active halos, edge shimmer, packet dot)

**Goal:** Hook SSE into the graph. Active nodes pulse; the edge from source→target shimmers during the 3s around the transition; a packet dot travels the edge once per transition.

**Non-goals:** Transcript pane (29c); scrubber (29d).

**Files created/modified:**
- `dashboard/lib/useGraphState.ts` — reducer hook `(events) → {nodeStates, edgeStates, lastTransition}`.
- `dashboard/components/AgentNode.tsx` — halo variants per state; CSS keyframe pulse.
- `dashboard/components/EdgeAnimated.tsx` — shimmer (stroke-dashoffset) + packet dot (framer-motion along SVG path).
- `dashboard/__tests__/use-graph-state.test.ts` — 6 cases:
  1. Sequence of events → last-wins state per node.
  2. `waiting_on_tool` maps to `waiting_on_tool` state (not `waiting_on_agent`).
  3. `lastTransition` set when a new node becomes active.
  4. Transition clears after 3s (time-dependent; use fake timers).
  5. No events → all nodes `idle`.
  6. Failed event → node state `failed`, no packet emitted to downstream.

**Test plan (RED):**
- Vitest `use-graph-state.test.ts` (6 cases).
- Playwright `graph-run.spec.ts` extended: launches a run, asserts the `active` node gets an `aria-current="true"` during execution, and at least one edge gets the `data-edge-state="firing"` attribute.

**Acceptance:**
- Running a real (or demo-mode) crew visibly animates: halo on active agent, shimmer on outgoing edge, packet dot traveling before the next node lights up.
- Reduced-motion media query disables the shimmer + packet (just the state chip changes).
- No layout thrash (all animation via `transform` / `opacity` / `stroke-*`).

**Risks & mitigations:**
- **Packet-dot performance:** framer-motion along SVG path can be expensive. Mitigation: bail out of animation when >20 concurrent packets (unrealistic for our scale but documented).
- **CSS pulse keyframes steal GPU on laptops:** use `will-change: filter` judiciously; test on battery-saver.

**Skills:** `frontend-ui-engineering`, `test-driven-development`, `browser-testing-with-devtools` (verify no CLS).

---

### Slice 29c — Transcript pane (live stream)

**Goal:** Right-hand pane showing per-agent output as it arrives. Auto-scroll, collapsible per-agent sections, tool-call chips.

**Non-goals:** Search / full-text filtering of the transcript (future).

**Files:**
- `dashboard/components/TranscriptPane.tsx`
- `dashboard/components/AgentTranscriptSection.tsx`
- `dashboard/__tests__/transcript-pane.test.tsx` — 5 cases:
  1. Renders one section per unique `agent_role`.
  2. Sections stay collapsed by default except the currently-active one.
  3. Auto-scrolls to latest entry.
  4. User scroll-up stops auto-scroll until they return to bottom.
  5. Copy-all writes the concatenated transcript to `navigator.clipboard`.

**Acceptance:**
- Live run: every SSE event appears in the transcript within 200ms.
- Completed run: final transcript has all events in insertion order.
- Copy-all button copies only the target agent's section.
- Dual-pane layout: graph ~60% + transcript ~40% on desktop; stacked on mobile.

**Risks & mitigations:**
- **Large transcripts** (hundreds of events) rerender every section. Mitigation: virtualize per-section lists if >100 entries.
- **Clipboard API** permissions in iframes. Mitigation: fall back to a selectable textarea.

**Skills:** `frontend-ui-engineering`, `test-driven-development`.

---

### Slice 29d — Share-page scrubber (replay)

**Goal:** On `/share/[token]`, a scrubber above the shell lets the viewer replay `agent_events` chronologically. Graph and transcript re-render to the scrubber's current index.

**Non-goals:** Live-update the shared page if the owner runs a new task (out of scope; a shared link is a snapshot).

**Files:**
- `dashboard/components/Scrubber.tsx`
- `dashboard/app/share/[token]/page.tsx` modified to pass `events` from the existing HTML payload (or augment the backend to also return JSON via a `?format=json` flag — decide in `/plan`).
- `dashboard/__tests__/scrubber.test.tsx` — 4 cases:
  1. Initial render: scrubber at max (latest event), graph shows final state.
  2. Drag to index 0: all nodes `idle`, transcript empty.
  3. Play: advances frame at `(ts[i+1] - ts[i]) / 2` intervals (2× speed cap).
  4. `Space` key toggles play/pause; `←` / `→` step one event.

**Acceptance:**
- Scrubber feels like video playback — smooth, no stuttering.
- "Jump to failure" appears only when any event has `state=failed`.
- Keyboard controls work without hijacking page scroll.

**Risks & mitigations:**
- **Backend change needed?** If we must JSON-return events for the share page, that's a backend API addition. Will decide in `/plan`; likely we augment `GET /share/{token}?format=json` returning `{workflow, events}` so the client can render richly. The existing HTML path stays for non-JS consumers.

**Skills:** `frontend-ui-engineering`, `api-and-interface-design` (if JSON endpoint added), `test-driven-development`.

---

### Slice 29e — Polish (shared-element transition, minimap fit, a11y)

**Goal:** Make the whole thing feel cohesive.

- Shared-element transition from launcher workflow card → graph view (framer-motion `layoutId`).
- Minimap styling + sensible viewport defaults.
- Full keyboard nav (tab through nodes, arrow-keys move selection).
- `prefers-reduced-motion` parity — disable all animation, keep state chips + transcripts.
- Dark-mode parity on graph colors.
- Lighthouse a11y ≥ 95 on the run page.

**Files:**
- Small tweaks across `GraphPane`, `AgentNode`, `EdgeAnimated`, `TranscriptPane`.
- `dashboard/__tests__/graph-pane.a11y.test.tsx` — axe-core integration, no violations at the `wcag2a` level.
- `dashboard/e2e/graph-a11y.spec.ts` — keyboard-only journey from launcher → run → transcript.

**Acceptance:**
- Lighthouse a11y ≥ 95.
- Keyboard-only user can launch a run, select a node, read its transcript, copy text.
- All animations honor `prefers-reduced-motion`.

**Skills:** `frontend-ui-engineering`, `browser-testing-with-devtools`.

---

## v4.1 Testing Strategy

| Level | Tool | Location | Coverage target |
|---|---|---|---|
| Unit (pure) | Vitest | `dashboard/__tests__/*.test.ts{x}` | 100% on `lib/graph.ts` + `lib/useGraphState.ts` (pure reducers) |
| Component | Vitest + Testing Library | `dashboard/__tests__/*.test.tsx` | every new component has at least one render + one interaction test |
| E2E | Playwright | `dashboard/e2e/` | one spec per slice (graph-run, scrubber, graph-a11y) |
| Backend | pytest | `tests/unit/` | ≥246 passing — no new backend tests unless scrubber slice 29d adds a JSON endpoint; in that case test the new endpoint |

**TDD discipline:** every slice starts with a failing Vitest or Playwright test.

---

## v4.1 Boundaries

### Always do
- Derive graph topology from the registry — never hand-position nodes.
- Run animation on `transform` / `opacity` / `stroke-*` only.
- Keep kanban available behind the view toggle (zero-disruption migration).
- Respect `prefers-reduced-motion` for every animation.
- Test each new component with at least one Vitest render test.

### Ask first
- Adding a new backend endpoint (e.g., JSON scrubber payload for slice 29d).
- Adding anything that changes the `AgentStateEvent` shape (would invalidate slice-27 persistence).
- Introducing a third dashboard dependency ≥ 30KB gzipped.

### Never do
- Hard-code workflow positions or names in the UI (registry is the source of truth).
- Ship an animation that drops below 30fps on a 2019 MacBook Air.
- Remove or rename existing dashboard tests — adapt them instead.
- Pre-render the graph server-side (SSR hydration mismatches + Dagre is CPU-only).

---

## v4.1 Risk Register

| Risk | Likelihood | Mitigation | Owner slice |
|---|---|---|---|
| `@xyflow/react@12` incompatible with React 19.2 | Low | Hello-World prototype in slice 29a gate | 29a |
| Packet-dot perf on long edges | Medium | Cap concurrent packets; bail out + static stroke | 29b |
| Transcript autoscroll fights the user | Medium | IntersectionObserver on the "latest" marker, pause-when-scrolled-up | 29c |
| Scrubber needs backend JSON endpoint | Medium | Decide in `/plan`; if yes, add `GET /share/{token}?format=json` | 29d |
| Dashboard bundle size growth | Medium | `@xyflow/react` is ~50 KB gzipped; acceptable. Audit with `npm run build` after 29a. | 29a |
| Kanban drift while graph is primary | Low | Covered by existing Phase-4 Vitest tests that still run | all |

---

## v4.1 Success Criteria

- [ ] All 5 slices (29a-29e) implemented and committed on `main` with TDD.
- [ ] Every Phase-4 Python test (246) still green.
- [ ] Dashboard tests ≥ 25 (current 10 + ~15 new).
- [ ] Playwright `graph-run.spec.ts` green against a `DEMO_MODE=true` run.
- [ ] Lighthouse a11y ≥ 95 on `/runs/[id]`.
- [ ] `docker compose -f docker-compose.dev.yml up` still boots 4 services; dashboard bundle < 500 KB gzipped.
- [ ] Kanban available behind view toggle with no regression in existing Phase-4 tests.
- [ ] `prefers-reduced-motion` honored — verified by manual browser toggle.

---

## v4.1 Open Questions

1. **Storybook or no Storybook?** — helps visual regression on nodes/edges but adds tooling. Default: no; revisit in `/plan` if component test coverage isn't enough.
2. **Share-page scrubber JSON endpoint vs embed in HTML** — decide in `/plan`. Leaning JSON endpoint (`GET /share/{token}?format=json`) for clean separation.
3. **Kanban deletion timing** — keep until when? Proposal: keep through v4.2, delete when Phase-4 ops tests migrate to the graph view.

---

## v4.1 Next Step

After this spec is reviewed, the next command is:

```
/plan SPEC.md v4.1 — slices 29a-29e. Break each slice into TDD sub-tasks (RED Vitest/Playwright test → GREEN implementation → refactor → commit). Reference DEC-29, DEC-30, DEC-31 in DECISIONS.md. Write PLAN.md with task order, dependencies, per-task acceptance + verify steps, and call out the `/share/{token}?format=json` decision for slice 29d explicitly. Docker + TDD + vertical slices only; no /ship. End with the /build prompt for slice 29a.
```
