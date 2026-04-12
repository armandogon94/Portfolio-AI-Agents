# Task List — Production Hardening v2.0

> **Plan:** [plan.md](plan.md) | **Spec:** [../SPEC.md](../SPEC.md) | **Decisions:** [../DECISIONS.md](../DECISIONS.md)

## Phase 1: Foundation

### Slice 1: Developer Tooling
- [x] **1.1** Create Makefile with standard targets (dev, test, lint, build, up, down, logs, clean, help)
- [x] **1.2** Add uv venv and generate uv.lock

### Checkpoint: Foundation
- [x] `make help` works, `make test` passes (16/16), `make lint` clean, `make build` succeeds, `uv.lock` committed

---

## Phase 2: Core Infrastructure

### Slice 2: Error Handling + DI
- [x] **2.1** RED — Write failing tests for exceptions and DI (`test_exceptions.py`, `test_dependencies.py`)
- [x] **2.2** GREEN — Implement `src/exceptions.py`, exception handlers, Qdrant DI via Depends()
- [x] **2.3** REFACTOR — Clean up, verify no bare `str(e)` remains

### Slice 3: Structured Logging
- [x] **3.1** RED — Write failing tests for JSON logging and request ID (`test_logging.py`)
- [x] **3.2** GREEN — Implement JSON formatter, request ID middleware
- [x] **3.3** REFACTOR — Verify logging integration, run full suite

### Checkpoint: Core Infrastructure
- [ ] Custom exceptions return ErrorResponse, Qdrant is singleton, JSON logs in prod, X-Request-ID on all responses

---

## Phase 3: Security

### Slice 4: API Key Auth
- [x] **4.1** RED — Write 7 failing auth tests (`test_auth.py`)
- [x] **4.2** GREEN — Implement `src/middleware/auth.py`, add `api_key` to Settings
- [x] **4.3** REFACTOR — Verify 401 uses ErrorResponse, run full suite

### Slice 5: Rate Limiting + CORS
- [x] **5.1** RED — Write failing rate limit and CORS tests (`test_rate_limiting.py`, `test_cors.py`)
- [x] **5.2** GREEN — Implement slowapi, env-based CORS origins
- [x] **5.3** REFACTOR — Verify rate limit + auth work together

### Checkpoint: Security
- [ ] Auth on all endpoints except /health, rate limiting returns 429, CORS env-based

---

## Phase 4: Async Execution

### Slice 6: Async Crew Execution
- [ ] **6.1** RED — Write failing tests for TaskStore and async endpoints (`test_task_store.py`, `test_async_crew.py`)
- [ ] **6.2** GREEN — Implement `src/services/task_store.py`, refactor `/crew/run` to 202 + BackgroundTasks, add `/crew/status/{task_id}`
- [ ] **6.3** REFACTOR — Verify Chainlit unaffected, TaskStore TTL cleanup

### Checkpoint: Async Execution
- [ ] POST /crew/run -> 202, GET /crew/status/{id} works, Chainlit unchanged

---

## Phase 5: Docker + CI/CD

### Slice 7: Docker Hardening
- [ ] **7.1** Multi-stage Dockerfile (builder + runtime), non-root user
- [ ] **7.2** Pin Qdrant v1.13.2, add health checks for all compose services, Chainlit in prod
- [ ] **7.3** Verify full Docker stack (build, dev, health, down)

### Slice 8: CI/CD Pipeline
- [ ] **8.1** Create `.github/workflows/ci.yml` (lint -> test -> build -> push)
- [ ] **8.2** Verify CI readiness (`make lint && make test` exit 0)

### Checkpoint: Docker + CI/CD
- [ ] Image builds, runs as non-root, health checks pass, CI YAML valid

---

## Phase 6: Observability

### Slice 9: Metrics Endpoint
- [ ] **9.1** RED — Write failing metrics tests (`test_metrics.py`)
- [ ] **9.2** GREEN — Implement MetricsCollector, metrics middleware, GET `/metrics`
- [ ] **9.3** REFACTOR — Final cleanup, full suite passes

### Checkpoint: Complete
- [ ] All 36 tasks done, 80%+ coverage, `make lint` clean, 9 commits on main

---

## Commit Log (fill in as completed)

| Slice | Commit Message | SHA |
|-------|---------------|-----|
| 1 | `feat(slice-1): add Makefile, uv venv, and dependency lock` | c1fe064 |
| 2 | `feat(slice-2): custom exceptions and Qdrant DI` | 3bb1591 |
| 3 | `feat(slice-3): structured JSON logging and request ID` | 973f1d7 |
| 4 | `feat(slice-4): API key authentication` | 273f6dc |
| 5 | `feat(slice-5): rate limiting and CORS hardening` | |
| 6 | `feat(slice-6): async crew execution with task polling` | |
| 7 | `feat(slice-7): multi-stage Docker with health checks` | |
| 8 | `feat(slice-8): GitHub Actions CI/CD pipeline` | |
| 9 | `feat(slice-9): metrics endpoint and request monitoring` | |
