# Design Decisions — AI Agent System v2.0

> Decisions made during the production hardening spec (2026-04-11).
> Format follows ADR-lite: Status, Context, Decision, Alternatives Rejected, Consequences.

---

## DEC-01: API Key Authentication (not JWT)

**Status:** Accepted

**Context:** The API needs authentication before production deployment. This is a portfolio project — there are no user accounts, no registration flow, and no role-based access. The authentication mechanism must be simple to implement, test, and demo.

**Decision:** Use a static API key passed via `X-API-Key` request header. The key is configured through the `API_KEY` environment variable. When `API_KEY` is not set (development), authentication is bypassed entirely.

**Alternatives rejected:**
- **JWT with access/refresh tokens** — Requires a user model, token generation, token refresh, token storage. This is appropriate for multi-tenant SaaS, not a single-deployment portfolio project. The complexity-to-value ratio is too high.
- **OAuth2 with external provider** — Adds external dependency (Auth0, Google, etc.) and redirect flows. Overkill for API-only access.
- **No authentication** — Leaves the API completely open. Even a portfolio piece should demonstrate security awareness.

**Consequences:**
- Simple to implement (one FastAPI dependency)
- Easy to test (just include/exclude a header)
- No token expiry, rotation, or refresh complexity
- No user identity — all authenticated requests are equivalent
- Can always layer JWT on top later if user accounts become necessary

---

## DEC-02: Async Crew Execution with BackgroundTasks (not Celery)

**Status:** Accepted

**Context:** CrewAI crew execution takes 30-120+ seconds. The current synchronous approach blocks the HTTP request, which can timeout. The system needs a way to submit work and check on it later.

**Decision:** Use FastAPI's built-in `BackgroundTasks` with an in-memory `TaskStore`. POST `/crew/run` returns 202 with a `task_id` immediately. GET `/crew/status/{task_id}` allows polling for results. Tasks auto-expire after 1 hour.

**Alternatives rejected:**
- **Celery + Redis** — Adds two new infrastructure dependencies (Celery worker process + Redis broker). The operational complexity is disproportionate for a single-instance portfolio project. Would require a new Docker service, celery configuration, and worker management.
- **Server-Sent Events (SSE)** — Good for streaming progress updates, but doesn't solve the fundamental problem of request-blocking. Would require holding the connection open for the entire crew run duration.
- **Keep synchronous** — Current approach. Unacceptable: requests timeout, no way to check progress, poor UX.

**Consequences:**
- Zero new dependencies (BackgroundTasks is built into FastAPI)
- Task state is in-memory — lost on restart (acceptable for portfolio)
- Simple polling pattern is easy to understand and demo
- Chainlit continues to call `run_crew()` directly (unaffected)
- Not suitable for multi-instance deployment (no shared state) — but that's a non-goal

---

## DEC-03: In-App Rate Limiting with slowapi (not Traefik)

**Status:** Accepted

**Context:** Expensive endpoints (`/crew/run` triggers LLM calls, `/documents/ingest` writes to Qdrant) need rate limiting to prevent abuse.

**Decision:** Use `slowapi` (a Starlette/FastAPI rate limiting library based on `limits`) for per-endpoint rate limiting. Limits: `/crew/run` at 5/min, `/documents/*` at 30/min. State is in-memory.

**Alternatives rejected:**
- **Traefik rate limiting** — Works only in production behind the reverse proxy. Cannot be tested locally without Traefik. Splits the security configuration across two systems.
- **Both (app + proxy)** — Defense-in-depth is ideal but adds complexity for a portfolio project. Can add Traefik rate limiting later as a production enhancement.
- **No rate limiting** — Leaves expensive endpoints unprotected. Even in a demo, demonstrating rate limiting is valuable.

**Consequences:**
- Testable without Traefik (in unit tests via TestClient)
- Works in both dev and prod identically
- In-memory state resets on restart (acceptable)
- Straightforward per-endpoint configuration via decorators

---

## DEC-04: Qdrant Connection via FastAPI Depends() (not per-request)

**Status:** Accepted

**Context:** Currently, every request to `/documents/ingest` and `/documents/search` creates a new `QdrantRepository` instance, which opens a new connection to Qdrant, creates an embedder, and checks if the collection exists. This is wasteful and introduces latency.

**Decision:** Initialize `QdrantRepository` once during FastAPI's lifespan startup. Store it on `app.state.qdrant_repo`. Inject it into route handlers via `Depends(get_qdrant_repo)`.

The `src/tools/rag.py` module keeps its own lazy-init singleton (`_get_repo()`) because CrewAI tools execute outside the FastAPI request cycle and cannot use `Depends()`.

**Alternatives rejected:**
- **Module-level global singleton** — Works but isn't testable (can't override in tests without monkeypatching).
- **Per-request instantiation (current)** — Wasteful: creates connection + embedder + collection check on every request.
- **Dependency injection container (python-inject, etc.)** — Overkill for 1-2 injected dependencies. FastAPI's built-in DI is sufficient.

**Consequences:**
- Single connection reused across all requests (faster, fewer resources)
- Easy to test (override the dependency in `app.dependency_overrides`)
- Two init paths: FastAPI DI for HTTP requests, lazy singleton for CrewAI tools
- Startup fails fast if Qdrant is unreachable

---

## DEC-05: Custom Exception Hierarchy (not RFC 7807)

**Status:** Accepted

**Context:** All errors currently return generic HTTP 500 with `str(e)` as the detail message. This provides no structured error information to API consumers.

**Decision:** Create a custom exception hierarchy rooted at `AppError` with subclasses for specific error categories (`NotFoundError`, `ValidationError`, `ServiceUnavailableError`, `CrewExecutionError`). Register FastAPI exception handlers that convert these to structured `ErrorResponse` objects.

```python
class ErrorResponse(BaseModel):
    error: str        # Exception class name (e.g., "NotFoundError")
    detail: str       # Human-readable message
    status_code: int  # HTTP status code
```

**Alternatives rejected:**
- **RFC 7807 Problem Details** — Well-specified but adds complexity (type URIs, instance IDs). Overkill for an API with 5 endpoints.
- **Keep generic HTTPException** — Current approach. No distinction between error types, everything is 500.

**Consequences:**
- Each exception type maps to a specific HTTP status code (404, 422, 500, 503)
- Consistent error response format across all endpoints
- Easy to extend: add new exception subclasses as needed
- API consumers can programmatically handle errors by `error` field

---

## DEC-06: Environment-Based CORS (not always-open)

**Status:** Accepted

**Context:** CORS is currently configured as `allow_origins=["*"]`, which allows any website to make requests to the API. This is fine for local development but unacceptable in production.

**Decision:** Make CORS origins configurable via `CORS_ORIGINS` environment variable (comma-separated list). Default is `["*"]` (development). Production sets `CORS_ORIGINS=https://agents.305-ai.com`.

**Alternatives rejected:**
- **Always restrict** — Breaks local development (frontend may run on different port or domain).
- **Keep allow-all** — Security risk in production.

**Consequences:**
- Dev convenience preserved (default allows all)
- Prod security enforced via environment config
- Single line in docker-compose.prod.yml to set

---

## DEC-07: JSON Logging + /metrics Endpoint (not Prometheus Stack)

**Status:** Accepted

**Context:** The project needs observability — at minimum, structured logs and runtime metrics. The question is how much infrastructure to add.

**Decision:** Two components:
1. **Structured JSON logging** via `python-json-logger` in production (human-readable in dev)
2. **GET `/metrics`** endpoint returning JSON with request counts, error counts, response times, uptime, and active tasks

**Alternatives rejected:**
- **Full Prometheus + Grafana** — Adds 2+ Docker services, requires prometheus_client library, Grafana dashboards, and configuration. Massive operational overhead for a portfolio project.
- **OpenTelemetry** — Comprehensive but requires a collector service and backend. Too much infrastructure.
- **No observability** — Misses an opportunity to demonstrate production awareness.

**Consequences:**
- Minimal dependencies (one library for JSON logging, metrics are in-memory)
- Demonstrates awareness of production observability patterns
- In-memory metrics reset on restart (acceptable for portfolio)
- Easy to add Prometheus export later by reading from MetricsCollector

---

## DEC-08: GitHub Actions CI/CD (not GitLab or manual)

**Status:** Accepted

**Context:** The project needs automated linting, testing, and Docker image building on every push.

**Decision:** GitHub Actions workflow with 4 stages: lint (ruff) -> test (pytest -m unit) -> build (docker build) -> push (ghcr.io, main branch only).

**Alternatives rejected:**
- **GitLab CI** — Project is hosted on GitHub.
- **No CI/CD** — Manual testing is error-prone and doesn't demonstrate DevOps competence.
- **Self-hosted runners** — Unnecessary complexity for a portfolio project.

**Consequences:**
- Free for public GitHub repos
- Standard and widely understood
- Unit tests run without Docker services (fast CI)
- Docker push only on main (PRs get lint + test + build only)

---

## DEC-09: Multi-Stage Docker with Pinned Versions

**Status:** Accepted

**Context:** The current Dockerfile is single-stage: it includes `build-essential` in the final image. Qdrant uses `:latest` tag, which is non-reproducible.

**Decision:**
1. Multi-stage Dockerfile: `builder` stage installs deps, `runtime` stage copies only installed packages and source
2. Non-root user (`appuser`) in runtime stage
3. Pin Qdrant to `v1.13.2` in all compose files
4. Add health checks for agents-api and chainlit-ui in compose

**Alternatives rejected:**
- **Keep single-stage** — Larger image, build tools in production, runs as root.
- **Use distroless base** — Too restrictive (no shell for debugging).
- **Keep `:latest`** — Non-reproducible builds across environments.

**Consequences:**
- Smaller production image (no build-essential, no pip cache)
- Non-root reduces container escape attack surface
- Pinned versions ensure reproducible deployments
- Health checks enable proper container orchestration

---

## DEC-10: uv for Dependency Locking and Virtual Environments (not pip-tools or Poetry)

**Status:** Accepted (updated 2026-04-11 — changed from pip-tools to uv per user preference)

**Context:** Dependencies in `pyproject.toml` use floating version constraints (`>=X.Y.Z`). Different installs can produce different dependency trees. Need a venv manager and lock file solution.

**Decision:** Use `uv` for virtual environment management and dependency locking. `uv venv` creates the `.venv`, `uv pip install` installs deps, `uv lock` generates `uv.lock`. Docker uses `uv pip install --system` from the lock file.

**Alternatives rejected:**
- **Poetry** — Requires migrating from hatchling to Poetry's build system.
- **pip-tools** — Works but slower, separate tool for venv management.
- **conda/miniconda** — Not project-isolated (global base env shared across projects).
- **Keep floating versions** — Risk of different dependency versions across environments.

**Consequences:**
- `uv.lock` ensures reproducible installs (committed to git)
- `uv` is extremely fast (10-100x faster than pip)
- `.venv` is project-isolated (not global conda base)
- Dockerfile uses `COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`
- `make install` bootstraps the full environment from scratch

---

## DEC-11: Standard Makefile Targets

**Status:** Accepted

**Context:** Every development action requires typing multi-word Docker or pytest commands. A Makefile provides short, memorable aliases.

**Decision:** Makefile with these targets:

| Target | Command |
|--------|---------|
| `make dev` | `docker compose -f docker-compose.dev.yml up -d` |
| `make down` | `docker compose -f docker-compose.dev.yml down` |
| `make test` | `pytest -m unit` |
| `make test-int` | `pytest -m integration` |
| `make test-all` | `pytest --cov=src` |
| `make lint` | `ruff check src/ tests/` |
| `make lint-fix` | `ruff check --fix src/ tests/` |
| `make format` | `ruff format src/ tests/` |
| `make build` | `docker build -t agents-api .` |
| `make logs` | `docker compose -f docker-compose.dev.yml logs -f` |
| `make clean` | Remove caches, build artifacts |
| `make lock` | `pip-compile` for lock files |
| `make shell` | `docker exec -it agents-api-dev bash` |
| `make health` | `curl localhost:8060/health` |

**Alternatives rejected:**
- **Just scripts** — Less discoverable than `make <tab>`.
- **Task runner (invoke, nox)** — Adds a dependency. Make is universal.
- **No convenience layer** — Forces memorizing long commands.

**Consequences:**
- Zero dependencies (make is pre-installed on macOS)
- `make <tab>` auto-completes all targets
- Consistent across all portfolio projects
- Self-documenting via `make help`

---

## DEC-12: Main Branch with Per-Slice Commits (not Feature Branches)

**Status:** Accepted

**Context:** The project is developed solo. The question is whether each slice should be a feature branch with a PR, or commits directly to main.

**Decision:** Work directly on `main` with one commit per slice. Commit message format: `feat(slice-N): <description>`.

**Alternatives rejected:**
- **Feature branch per slice** — Adds PR ceremony without a reviewer. Useful for teams, overhead for solo work.
- **Single commit for all slices** — Loses the ability to bisect or revert individual slices.

**Consequences:**
- Clean, linear history on main
- Each slice is a single atomic commit
- Easy to revert a specific slice if needed
- `git log --oneline` shows the progression clearly
- CI runs on every push to main (validates each slice)

---

## DEC-13: Disable Agent Delegation (not hierarchical process)

**Status:** Accepted

**Context:** The `researcher` agent was configured with `allow_delegation: true` in `agents.yaml`. CrewAI's delegation feature requires either a hierarchical crew process (with a manager agent) or explicit delegation targets. Neither is configured — the crew uses `Process.sequential` with no manager.

**Decision:** Set `allow_delegation: false` on all agents. The sequential process assigns each task to a specific agent in order; delegation would create unrouted subtask requests that fail silently or raise errors at runtime.

**Alternatives rejected:**
- **Hierarchical process with manager** — Requires an additional LLM call per task for the manager agent to route work. With a single shared Ollama instance on constrained RAM, this doubles coordination overhead with no user-visible benefit.
- **Keep allow_delegation: true** — Causes confusing runtime failures when the researcher tries to delegate with no valid targets.

**Consequences:**
- Agents execute their assigned tasks directly without attempting to create subtasks.
- Simpler, more predictable execution flow.
- Can be revisited if a hierarchical multi-agent workflow is needed in the future.

---

## DEC-14: SQLite for Completed Run History (not replacing in-memory TaskStore)

**Status:** Accepted

**Context:** The in-memory `TaskStore` is sufficient for polling in-flight tasks (TTL=1h), but all history is lost on restart. Users want to review past research runs.

**Decision:** Add a `SQLiteResultStore` that persists completed task results to `data/results.db`. The in-memory `TaskStore` remains for in-flight task state (pending/running). On task completion, `_execute_crew` calls `sqlite_store.save()`. A new `GET /crew/history` endpoint exposes recent runs.

**Alternatives rejected:**
- **Replace TaskStore with SQLite entirely** — SQLite writes introduce latency on every status update (pending→running→completed). The in-memory store is fast and sufficient for the polling window.
- **PostgreSQL** — Adds Docker infrastructure dependency. SQLite requires zero infrastructure and is appropriate for single-instance deployments.

**Consequences:**
- Completed runs persist across restarts.
- `data/results.db` is created automatically; `data/` is git-ignored.
- History is read-only via API (no delete endpoint).

---

## DEC-15: httpx + BeautifulSoup for URL/PDF Ingest (not headless browser)

**Status:** Accepted

**Context:** Users want to ingest web pages and PDFs into Qdrant so agents can use them as RAG context. Two options: (a) httpx + BeautifulSoup + pypdf; (b) headless browser (Playwright).

**Decision:** Use httpx for HTTP fetching, BeautifulSoup for HTML→text extraction, pypdf for PDF parsing. SSRF protection validates URL scheme and blocks private IP ranges before fetching.

**Alternatives rejected:**
- **Playwright (headless browser)** — Adds ~150MB dependency and process overhead. Needed for JavaScript-heavy SPAs, but most research-relevant content (news, docs, PDFs) is served as static HTML. The extra complexity is not justified for this use case.

**Consequences:**
- Works for ~90% of web content (static HTML, server-rendered pages, PDFs).
- Does not work for JavaScript-rendered SPAs (e.g., React/Vue apps without SSR).
- Rate limited to 10/minute per IP to prevent abuse of outbound HTTP.
