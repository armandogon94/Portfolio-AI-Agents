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

## Next Step

After this spec is reviewed, the next command is:

```
/plan SPEC.md — all 9 slices. Break each slice into TDD sub-tasks (RED test -> GREEN implementation -> refactor). Reference DECISIONS.md for design choices.
```
