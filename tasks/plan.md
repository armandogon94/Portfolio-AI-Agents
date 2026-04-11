# Implementation Plan: Production Hardening v2.0

> **Spec:** [SPEC.md](../SPEC.md) | **Decisions:** [DECISIONS.md](../DECISIONS.md)
> **Date:** 2026-04-11 | **Slices:** 9 | **Tasks:** 36

## Overview

Transform the functionally-complete CrewAI multi-agent system into a production-hardened portfolio piece. Each of the 9 vertical slices follows the TDD cycle (RED -> GREEN -> REFACTOR) and produces a single atomic commit on main.

## Architecture Decisions

All decisions documented in [DECISIONS.md](../DECISIONS.md). Key choices:
- **DEC-01:** API key auth (not JWT) — portfolio project, no user accounts
- **DEC-02:** BackgroundTasks + in-memory store (not Celery) — zero new deps
- **DEC-04:** Qdrant via Depends() + lifespan (not per-request) — testable singleton
- **DEC-05:** Custom exception hierarchy (not RFC 7807) — simpler, sufficient
- **DEC-09:** Multi-stage Docker, pinned versions, non-root user

## Dependency Graph

```
Slice 1 (Makefile + deps)
    |
Slice 2 (Errors + DI)
    |
Slice 3 (Structured logging)
    |
Slice 4 (API key auth)
    |
Slice 5 (Rate limiting + CORS)
    |
Slice 6 (Async crew execution)
    |
Slice 7 (Docker hardening)
    |
Slice 8 (CI/CD pipeline)
    |
Slice 9 (Metrics endpoint)
```

## Skills Per Slice

| Slice | Primary Skill | Supporting Skills |
|-------|--------------|-------------------|
| 1 | `incremental-implementation` | — |
| 2 | `api-and-interface-design` | `test-driven-development` |
| 3 | `test-driven-development` | — |
| 4 | `security-and-hardening` | `test-driven-development` |
| 5 | `security-and-hardening` | `test-driven-development` |
| 6 | `api-and-interface-design` | `test-driven-development` |
| 7 | `ci-cd-and-automation` | — |
| 8 | `ci-cd-and-automation` | — |
| 9 | `test-driven-development` | `performance-optimization` |

---

## Phase 1: Foundation

### Slice 1: Developer Tooling (Makefile + Dependency Lock)

#### Task 1.1: Create Makefile with standard targets

**Description:** Create a Makefile with dev, test, lint, build, up, down, logs, clean, lock, shell, health targets. Add a `help` target as default that lists all available targets.

**Acceptance criteria:**
- [ ] `make help` lists all targets with descriptions
- [ ] `make test` runs `pytest -m unit`
- [ ] `make lint` runs `ruff check src/ tests/`
- [ ] `make build` runs `docker build -t agents-api .`
- [ ] `make dev` runs `docker compose -f docker-compose.dev.yml up -d`
- [ ] `make down` stops all services
- [ ] `make clean` removes `__pycache__`, `.pytest_cache`, `.ruff_cache`

**Verification:** Each make target runs and exits 0 (or shows expected output).

**Dependencies:** None (first task)

**Files:**
- `Makefile` (new)

**Scope:** S (1 file)

---

#### Task 1.2: Add pip-tools and generate lock files

**Description:** Add `pip-tools` to dev dependencies. Generate `requirements.txt` (production) and `requirements-dev.txt` (dev) via `pip-compile`. Add `make lock` target.

**Acceptance criteria:**
- [ ] `pip-tools` in `[project.optional-dependencies] dev`
- [ ] `requirements.txt` generated and committed
- [ ] `requirements-dev.txt` generated and committed
- [ ] `make lock` regenerates both files
- [ ] `Dockerfile` updated to use `requirements.txt` for deterministic install

**Verification:** `make lock && diff requirements.txt requirements.txt` (idempotent). Docker build uses lock file.

**Dependencies:** Task 1.1

**Files:**
- `pyproject.toml` (modify — add pip-tools)
- `requirements.txt` (new — generated)
- `requirements-dev.txt` (new — generated)
- `Dockerfile` (modify — `COPY requirements.txt .` + `pip install -r requirements.txt`)
- `Makefile` (modify — add `lock` target)

**Scope:** S (3 modified, 2 new)

---

### Checkpoint: Foundation
- [ ] `make help` works
- [ ] `make test` runs existing unit tests and they pass
- [ ] `make lint` exits clean (or shows existing issues only)
- [ ] `make build` produces a Docker image
- [ ] `requirements.txt` is committed
- [ ] Commit: `feat(slice-1): add Makefile and dependency lock files`

---

## Phase 2: Core Infrastructure

### Slice 2: Error Handling + Dependency Injection

#### Task 2.1: RED — Write failing tests for exceptions and DI

**Description:** Write test files that assert behavior not yet implemented: custom error responses, ErrorResponse schema, and QdrantRepository singleton.

**Acceptance criteria:**
- [ ] `tests/unit/test_exceptions.py` has 3+ tests for error response format
- [ ] `tests/unit/test_dependencies.py` has 2+ tests for DI behavior
- [ ] `make test` FAILS (tests assert non-existent behavior)

**Verification:** `make test` shows RED failures on new tests only. Existing tests still pass.

**Dependencies:** Task 1.1

**Files:**
- `tests/unit/test_exceptions.py` (new)
- `tests/unit/test_dependencies.py` (new)

**Scope:** S (2 new files)

**Tests to write:**
```python
# test_exceptions.py
test_app_error_has_status_code_and_message     # AppError stores both fields
test_not_found_returns_404_response            # FastAPI handler returns 404 + ErrorResponse
test_service_unavailable_returns_503           # Qdrant down -> 503
test_crew_execution_error_returns_500          # Crew failure -> 500 with detail
test_error_response_schema_fields              # ErrorResponse has error, detail, status_code

# test_dependencies.py
test_qdrant_repo_available_via_depends         # Route handler receives repo
test_qdrant_repo_is_singleton                  # Same instance across requests
```

---

#### Task 2.2: GREEN — Implement exceptions, error handlers, and DI

**Description:** Create `src/exceptions.py` with the exception hierarchy. Add exception handlers to `src/main.py`. Refactor lifespan to initialize QdrantRepository. Add `get_qdrant_repo` dependency. Update document endpoints to use `Depends()`. Add `ErrorResponse` to schemas.

**Acceptance criteria:**
- [ ] `src/exceptions.py` defines AppError, NotFoundError, ValidationError, ServiceUnavailableError, CrewExecutionError
- [ ] `src/main.py` has exception handlers registered
- [ ] QdrantRepository created once in lifespan, stored on `app.state`
- [ ] `/documents/ingest` and `/documents/search` use `Depends(get_qdrant_repo)`
- [ ] `make test` PASSES (all tests green)

**Verification:** `make test && make lint`

**Dependencies:** Task 2.1

**Files:**
- `src/exceptions.py` (new)
- `src/main.py` (modify — handlers, lifespan, DI)
- `src/models/schemas.py` (modify — add ErrorResponse)
- `src/tools/rag.py` (modify — document that lazy-init stays for CrewAI path)

**Scope:** M (1 new, 3 modified)

---

#### Task 2.3: REFACTOR — Clean up error handling

**Description:** Review and tidy the exception module and handlers. Ensure consistent error response format. Verify no bare `str(e)` remains in any endpoint.

**Acceptance criteria:**
- [ ] `make test` still passes
- [ ] `make lint` is clean
- [ ] No endpoint catches `Exception` and returns `str(e)` directly
- [ ] `/crew/run` uses CrewExecutionError

**Verification:** `make test && make lint`. Grep for `str(e)` in main.py — should be zero.

**Dependencies:** Task 2.2

**Files:**
- `src/main.py` (modify — final cleanup)

**Scope:** XS (1 file, minor edits)

---

### Slice 3: Structured Logging

#### Task 3.1: RED — Write failing tests for JSON logging and request ID

**Description:** Write tests asserting JSON log format in production and request ID in response headers.

**Acceptance criteria:**
- [ ] `tests/unit/test_logging.py` has 4+ tests
- [ ] `make test` FAILS on new tests

**Verification:** `make test` shows RED on new tests.

**Dependencies:** Task 2.3

**Files:**
- `tests/unit/test_logging.py` (new)

**Scope:** S (1 file)

**Tests to write:**
```python
test_json_log_format_in_production         # ENVIRONMENT=production -> valid JSON log lines
test_human_format_in_development           # ENVIRONMENT=development -> existing readable format
test_request_id_in_response_header         # Response has X-Request-ID header (UUID)
test_request_id_middleware_generates_uuid   # Middleware creates valid UUID4
```

---

#### Task 3.2: GREEN — Implement JSON logger and request ID middleware

**Description:** Add JSON formatter to logger. Create `src/middleware/request_id.py`. Add middleware to FastAPI app. Add `python-json-logger` dependency.

**Acceptance criteria:**
- [ ] `src/middleware/request_id.py` generates UUID, adds to response header
- [ ] `src/utils/logger.py` has JSON formatter selected by environment
- [ ] `make test` PASSES

**Verification:** `make test && make lint`

**Dependencies:** Task 3.1

**Files:**
- `src/middleware/__init__.py` (new)
- `src/middleware/request_id.py` (new)
- `src/utils/logger.py` (modify)
- `src/main.py` (modify — add middleware)
- `pyproject.toml` (modify — add python-json-logger)

**Scope:** M (2 new, 3 modified)

---

#### Task 3.3: REFACTOR — Verify logging integration

**Description:** Clean up logger module. Ensure request_id flows through to log output. Run full suite.

**Acceptance criteria:**
- [ ] `make test` passes (all tests, not just new ones)
- [ ] `make lint` clean

**Verification:** `make test && make lint`

**Dependencies:** Task 3.2

**Files:**
- `src/utils/logger.py` (modify — minor cleanup if needed)

**Scope:** XS

---

### Checkpoint: Core Infrastructure
- [ ] All tests pass (`make test`)
- [ ] Custom exceptions return structured ErrorResponse
- [ ] QdrantRepository is a singleton via Depends()
- [ ] Logs are JSON in production, readable in development
- [ ] Every response has X-Request-ID header
- [ ] Commit: `feat(slice-2): custom exceptions and Qdrant DI`
- [ ] Commit: `feat(slice-3): structured JSON logging and request ID`

---

## Phase 3: Security

### Slice 4: API Key Authentication

#### Task 4.1: RED — Write failing auth tests

**Description:** Write tests for API key authentication behavior.

**Acceptance criteria:**
- [ ] `tests/unit/test_auth.py` has 7 tests
- [ ] `make test` FAILS on new tests

**Dependencies:** Task 3.3

**Files:**
- `tests/unit/test_auth.py` (new)

**Scope:** S (1 file)

**Tests to write:**
```python
test_health_no_auth_required              # GET /health -> 200 without header
test_crew_run_requires_api_key            # POST /crew/run without key -> 401
test_crew_run_with_valid_key              # POST /crew/run with correct key -> 200/202
test_crew_run_with_invalid_key            # POST /crew/run with wrong key -> 401
test_auth_bypassed_when_no_key_configured # API_KEY not set -> all endpoints work
test_documents_ingest_requires_auth       # POST /documents/ingest without key -> 401
test_documents_search_requires_auth       # POST /documents/search without key -> 401
```

---

#### Task 4.2: GREEN — Implement API key auth middleware

**Description:** Create `src/middleware/auth.py` with `api_key_auth` dependency. Add `api_key` to Settings. Apply to protected routes (all except `/health`).

**Acceptance criteria:**
- [ ] `src/middleware/auth.py` implements API key validation
- [ ] `api_key: Optional[str] = None` in Settings
- [ ] `/health` stays public
- [ ] All other endpoints require valid key when `API_KEY` is set
- [ ] Auth bypassed when `API_KEY` is not set
- [ ] `make test` PASSES

**Verification:** `make test && make lint`

**Dependencies:** Task 4.1

**Files:**
- `src/middleware/auth.py` (new)
- `src/config/settings.py` (modify — add api_key)
- `src/main.py` (modify — apply auth dependency)
- `.env.example` (modify — add API_KEY)
- `docker-compose.prod.yml` (modify — add API_KEY env)

**Scope:** M (1 new, 4 modified)

---

#### Task 4.3: REFACTOR — Clean up auth and verify

**Description:** Review auth implementation. Ensure 401 responses use ErrorResponse schema. Run full suite.

**Acceptance criteria:**
- [ ] 401 responses match ErrorResponse format
- [ ] `make test` passes all tests
- [ ] `make lint` clean

**Dependencies:** Task 4.2

**Files:**
- `src/middleware/auth.py` (modify — minor if needed)

**Scope:** XS

---

### Slice 5: Rate Limiting + CORS Hardening

#### Task 5.1: RED — Write failing rate limit and CORS tests

**Description:** Write tests for rate limiting behavior and environment-based CORS.

**Acceptance criteria:**
- [ ] `tests/unit/test_rate_limiting.py` has 3+ tests
- [ ] `tests/unit/test_cors.py` has 2+ tests
- [ ] `make test` FAILS on new tests

**Dependencies:** Task 4.3

**Files:**
- `tests/unit/test_rate_limiting.py` (new)
- `tests/unit/test_cors.py` (new)

**Scope:** S (2 files)

**Tests to write:**
```python
# test_rate_limiting.py
test_rate_limit_crew_run_returns_429       # 6th request in 1 minute -> 429
test_rate_limit_documents_search_returns_429 # 31st request -> 429
test_rate_limit_health_no_limit            # /health is not rate limited

# test_cors.py
test_cors_allows_all_in_dev                # cors_origins=["*"] -> Access-Control-Allow-Origin: *
test_cors_restricts_in_prod                # Only configured origin gets CORS headers
```

---

#### Task 5.2: GREEN — Implement rate limiting and env-based CORS

**Description:** Add `slowapi` to deps. Configure per-endpoint rate limits. Replace hardcoded CORS `["*"]` with `settings.cors_origins`.

**Acceptance criteria:**
- [ ] slowapi limiter applied to `/crew/run` (5/min) and `/documents/*` (30/min)
- [ ] CORS origins read from `settings.cors_origins`
- [ ] 429 response includes `Retry-After` header
- [ ] `make test` PASSES

**Verification:** `make test && make lint`

**Dependencies:** Task 5.1

**Files:**
- `src/main.py` (modify — slowapi, CORS from settings)
- `src/config/settings.py` (modify — add cors_origins, rate limit fields)
- `pyproject.toml` (modify — add slowapi)
- `.env.example` (modify — add CORS_ORIGINS)
- `docker-compose.prod.yml` (modify — CORS_ORIGINS env)

**Scope:** M (5 modified)

---

#### Task 5.3: REFACTOR — Verify rate limit and CORS integration

**Description:** Run full suite. Verify rate limit and CORS don't interfere with auth.

**Acceptance criteria:**
- [ ] `make test` passes all tests
- [ ] `make lint` clean
- [ ] Auth + rate limit work together (rate limit applies after auth)

**Dependencies:** Task 5.2

**Files:**
- Minor adjustments if needed

**Scope:** XS

---

### Checkpoint: Security
- [ ] All tests pass (`make test`)
- [ ] API key auth protects all endpoints except `/health`
- [ ] Rate limiting returns 429 on abuse
- [ ] CORS is environment-based
- [ ] Commit: `feat(slice-4): API key authentication`
- [ ] Commit: `feat(slice-5): rate limiting and CORS hardening`

---

## Phase 4: Async Execution

### Slice 6: Async Crew Execution

#### Task 6.1: RED — Write failing tests for TaskStore and async endpoints

**Description:** Write tests for the in-memory TaskStore and the new async crew endpoints.

**Acceptance criteria:**
- [ ] `tests/unit/test_task_store.py` has 4+ tests for TaskStore
- [ ] `tests/unit/test_async_crew.py` has 5+ tests for async endpoints
- [ ] `make test` FAILS on new tests

**Dependencies:** Task 5.3

**Files:**
- `tests/unit/test_task_store.py` (new)
- `tests/unit/test_async_crew.py` (new)

**Scope:** S (2 files)

**Tests to write:**
```python
# test_task_store.py
test_task_store_create_returns_task_id     # create() returns UUID string
test_task_store_get_returns_task           # get() returns task with status
test_task_store_update_changes_status      # update() transitions status + sets result
test_task_store_cleanup_removes_expired    # cleanup() removes tasks past TTL

# test_async_crew.py
test_crew_run_returns_202_with_task_id     # POST /crew/run -> 202 + task_id
test_crew_status_returns_task_state        # GET /crew/status/{id} -> status object
test_crew_status_not_found_returns_404     # Unknown task_id -> 404
test_crew_status_completed_has_result      # Completed task -> result field populated
test_crew_status_failed_has_error          # Failed task -> error message in result
```

---

#### Task 6.2: GREEN — Implement TaskStore and async endpoints

**Description:** Create `src/services/task_store.py` with in-memory task storage. Refactor `/crew/run` to return 202 and run crew in background. Add `/crew/status/{task_id}`.

**Acceptance criteria:**
- [ ] `TaskStore` has create, get, update, cleanup methods
- [ ] POST `/crew/run` returns 202 with `task_id` and `status: "pending"`
- [ ] GET `/crew/status/{task_id}` returns current task status
- [ ] Background task updates store on completion/failure
- [ ] `make test` PASSES

**Verification:** `make test && make lint`

**Dependencies:** Task 6.1

**Files:**
- `src/services/__init__.py` (new)
- `src/services/task_store.py` (new)
- `src/main.py` (modify — async crew, new endpoint, lifespan TaskStore)
- `src/models/schemas.py` (modify — CrewAsyncResponse, TaskStatusResponse, TaskStatus)

**Scope:** M (2 new, 2 modified)

---

#### Task 6.3: REFACTOR — Clean up async execution

**Description:** Verify Chainlit still works with `run_crew()` directly. Ensure TaskStore TTL cleanup. Run full suite.

**Acceptance criteria:**
- [ ] `make test` passes all tests
- [ ] `make lint` clean
- [ ] `src/chainlit_app.py` still imports and calls `run_crew()` directly (unchanged)
- [ ] TaskStore cleanup runs periodically or on access

**Dependencies:** Task 6.2

**Files:**
- `src/services/task_store.py` (modify — cleanup trigger if needed)

**Scope:** XS

---

### Checkpoint: Async Execution
- [ ] All tests pass (`make test`)
- [ ] POST `/crew/run` returns 202 with task_id
- [ ] GET `/crew/status/{task_id}` returns task state
- [ ] Chainlit unaffected
- [ ] Commit: `feat(slice-6): async crew execution with task polling`

---

## Phase 5: Docker + CI/CD

### Slice 7: Docker Hardening

#### Task 7.1: Implement multi-stage Dockerfile

**Description:** Rewrite Dockerfile with builder and runtime stages. Add non-root user. Use `requirements.txt` from Slice 1.

**Acceptance criteria:**
- [ ] Builder stage installs deps
- [ ] Runtime stage copies only installed packages + source
- [ ] `USER appuser` in runtime stage
- [ ] `make build` succeeds
- [ ] Runtime image is smaller than current

**Verification:** `make build`. Compare image sizes. `docker run --rm agents-api whoami` returns `appuser`.

**Dependencies:** Task 6.3

**Files:**
- `Dockerfile` (modify — full rewrite to multi-stage)

**Scope:** S (1 file)

---

#### Task 7.2: Pin versions and add health checks in compose

**Description:** Pin Qdrant to `v1.13.2`. Add health checks for agents-api and chainlit-ui in dev compose. Add chainlit-ui to prod compose.

**Acceptance criteria:**
- [ ] Qdrant image is `qdrant/qdrant:v1.13.2` in both compose files
- [ ] agents-api has healthcheck (curl /health)
- [ ] chainlit-ui has healthcheck
- [ ] Production compose includes chainlit-ui service
- [ ] `docker compose -f docker-compose.dev.yml config` validates
- [ ] `docker compose -f docker-compose.prod.yml config` validates

**Verification:** `docker compose config` validates for both files.

**Dependencies:** Task 7.1

**Files:**
- `docker-compose.dev.yml` (modify)
- `docker-compose.prod.yml` (modify)

**Scope:** S (2 files)

---

#### Task 7.3: Verify Docker stack end-to-end

**Description:** Build images, start dev stack, verify health checks, stop stack.

**Acceptance criteria:**
- [ ] `make build` succeeds
- [ ] `make dev` starts all 3 services
- [ ] `make health` returns healthy response
- [ ] `make down` stops all services
- [ ] `make test` still passes

**Verification:** Full `make build && make dev && make health && make down` sequence.

**Dependencies:** Task 7.2

**Files:** None (verification only)

**Scope:** XS

---

### Slice 8: CI/CD Pipeline

#### Task 8.1: Create GitHub Actions workflow

**Description:** Write `.github/workflows/ci.yml` with lint -> test -> build -> push stages. Push only on main branch.

**Acceptance criteria:**
- [ ] Triggered on push to main and PRs to main
- [ ] Lint stage: ruff check
- [ ] Test stage: pytest -m unit (Python 3.12)
- [ ] Build stage: docker build
- [ ] Push stage: ghcr.io (main only)
- [ ] pip cache for faster installs
- [ ] Docker layer cache

**Verification:** `make lint && make test` pass locally. YAML syntax validates.

**Dependencies:** Task 7.3

**Files:**
- `.github/workflows/ci.yml` (new)

**Scope:** S (1 file)

---

#### Task 8.2: Verify CI readiness

**Description:** Ensure all lint and test commands exit 0. Fix any ruff issues.

**Acceptance criteria:**
- [ ] `make lint` exits 0
- [ ] `make test` exits 0
- [ ] No ruff violations

**Verification:** `make lint && make test`

**Dependencies:** Task 8.1

**Files:** Any files with lint issues (fix only)

**Scope:** XS-S

---

### Checkpoint: Docker + CI/CD
- [ ] Docker image builds and runs as non-root
- [ ] Qdrant pinned, health checks on all services
- [ ] CI pipeline YAML created
- [ ] `make lint && make test` pass
- [ ] Commit: `feat(slice-7): multi-stage Docker with health checks`
- [ ] Commit: `feat(slice-8): GitHub Actions CI/CD pipeline`

---

## Phase 6: Observability

### Slice 9: Monitoring + Metrics Endpoint

#### Task 9.1: RED — Write failing metrics tests

**Description:** Write tests for the /metrics endpoint and metrics collection.

**Acceptance criteria:**
- [ ] `tests/unit/test_metrics.py` has 5 tests
- [ ] `make test` FAILS on new tests

**Dependencies:** Task 8.2

**Files:**
- `tests/unit/test_metrics.py` (new)

**Scope:** S (1 file)

**Tests to write:**
```python
test_metrics_endpoint_returns_json         # GET /metrics -> JSON with expected fields
test_metrics_counts_requests               # After N requests, count == N
test_metrics_tracks_errors                 # Failed request increments error count
test_metrics_response_time_positive        # Average response time > 0
test_metrics_requires_auth                 # /metrics requires API key
```

---

#### Task 9.2: GREEN — Implement MetricsCollector and /metrics endpoint

**Description:** Create `MetricsCollector` class, metrics middleware, and `/metrics` endpoint.

**Acceptance criteria:**
- [ ] `src/services/metrics.py` has MetricsCollector with increment/record methods
- [ ] `src/middleware/metrics.py` records request count, duration, status per endpoint
- [ ] GET `/metrics` returns JSON with total_requests, error_count, endpoints, uptime_seconds, active_tasks
- [ ] `/metrics` protected by API key auth
- [ ] `make test` PASSES

**Verification:** `make test && make lint`

**Dependencies:** Task 9.1

**Files:**
- `src/services/metrics.py` (new)
- `src/middleware/metrics.py` (new)
- `src/main.py` (modify — add middleware, add endpoint)
- `src/models/schemas.py` (modify — add MetricsResponse)

**Scope:** M (2 new, 2 modified)

---

#### Task 9.3: REFACTOR — Final cleanup and integration

**Description:** Run full test suite. Verify metrics don't slow down requests. Clean up any code smells.

**Acceptance criteria:**
- [ ] `make test` passes all tests (expected: 30+ tests)
- [ ] `make lint` clean
- [ ] All 9 slices committed

**Dependencies:** Task 9.2

**Files:** Minor adjustments

**Scope:** XS

---

### Checkpoint: Complete
- [ ] All acceptance criteria from SPEC.md met
- [ ] `make test` passes with 80%+ coverage
- [ ] `make lint` exits clean
- [ ] All 9 slices committed to main
- [ ] Commit: `feat(slice-9): metrics endpoint and request monitoring`

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `src/main.py` modified in 6 slices | Med | Each slice touches different concerns. Full test suite after each. |
| BackgroundTasks for long crew runs | Low | Not subject to request timeout. TaskStore captures success/failure. |
| slowapi + auth middleware conflict | Low | Different layers (decorator vs Depends). Explicitly tested in Slice 5. |
| Existing tests break after DI changes | Med | DI doesn't change mock targets. Verified immediately after Slice 2. |
| pip-compile may fail on Apple Silicon | Low | Run with `--no-emit-index-url`. Fallback: manual requirements.txt. |

---

## Suggested Prompts Per Slice

After plan approval, start with:

```
/build Slice 1 — Developer Tooling. Create Makefile with standard targets (dev, test, lint, build, up, down, logs, clean, lock, shell, health). Add pip-tools, generate lock files. Reference DECISIONS.md DEC-10, DEC-11.
```

After each slice, the next prompt is:

| Completed | Next Prompt |
|-----------|-------------|
| Slice 1 | `/build Slice 2 — Error Handling + DI. TDD: write failing tests first, then implement custom exceptions (AppError hierarchy) and Qdrant Depends() injection. Reference DEC-04, DEC-05.` |
| Slice 2 | `/build Slice 3 — Structured Logging. TDD: write failing tests for JSON log format and request ID middleware. Reference DEC-07.` |
| Slice 3 | `/build Slice 4 — API Key Auth. TDD: write 7 failing auth tests, then implement X-API-Key middleware. Reference DEC-01.` |
| Slice 4 | `/build Slice 5 — Rate Limiting + CORS. TDD: write failing tests for rate limits and CORS, then implement slowapi + env-based origins. Reference DEC-03, DEC-06.` |
| Slice 5 | `/build Slice 6 — Async Crew Execution. TDD: write failing tests for TaskStore and async endpoints, then implement BackgroundTasks + polling. Reference DEC-02.` |
| Slice 6 | `/build Slice 7 — Docker Hardening. Multi-stage Dockerfile, non-root user, pin Qdrant v1.13.2, add health checks. Reference DEC-09.` |
| Slice 7 | `/build Slice 8 — CI/CD Pipeline. Create GitHub Actions workflow (lint -> test -> build -> push). Reference DEC-08.` |
| Slice 8 | `/build Slice 9 — Metrics Endpoint. TDD: write failing tests for /metrics, then implement MetricsCollector and middleware. Reference DEC-07.` |
| Slice 9 | `/review all 9 slices — full codebase review against SPEC.md acceptance criteria and AGENTS.md checklists.` |
