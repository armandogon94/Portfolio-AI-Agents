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

---

# Phase 4 — Portfolio Demos (v4.0)

> Decisions DEC-16..DEC-28 made during the plan-mode brainstorm on 2026-04-16. Source plan: `~/.claude/plans/analyze-the-current-state-temporal-quilt.md`. Corresponding SPEC section: SPEC.md § "Phase 4 — Portfolio Demos".

---

## DEC-16: SSE for live agent events (not WebSocket)

**Status:** Accepted

**Context:** Slice 19 needs to push per-agent state updates from the FastAPI process to browser clients (the new Next.js dashboard and, later, Chainlit nested steps). The channel has one producer (the crew run) and one-or-more browser consumers; consumers never push back on the same channel.

**Decision:** Use Server-Sent Events (SSE) on `GET /crew/run/{task_id}/events`. Each event has an `event:` type (`agent_state`, `run_complete`, `run_failed`, heartbeat comment) and a JSON `data:` payload. `text/event-stream` content type, `X-Accel-Buffering: no` header.

**Alternatives rejected:**
- **WebSocket** — Bidirectional, but we don't need client-to-server messages on this channel. Adds handshake complexity, requires protocol-aware proxies, and there is no native browser `WebSocket` auto-reconnect (EventSource has it for free).
- **Long-polling** — Works without a streaming stack, but each response round-trip burns a full HTTP handshake; the event cadence during an active crew run is high enough (5-30 events/s) that polling starves on its own overhead.
- **Push via webhook** — Works for server-to-server (slice 18 already uses it), not for browsers.

**Consequences:**
- Browser side uses the native `EventSource` API with automatic reconnection.
- Works cleanly through uvicorn; no extra dep.
- Unidirectional — any future "agent accepts user input mid-run" feature would need a second channel (likely a simple POST endpoint, not a full WebSocket switch).
- SSE connections count against the rate limiter (mitigated by exempting `/crew/run/*/events` or using a high limit).

---

## DEC-17: Separate dashboard app (not Chainlit-only)

**Status:** Accepted

**Context:** The "team view" vision (prospects watching agents work in a live kanban) could live inside Chainlit as nested `cl.Step`s, or in a separate app. Chainlit is designed around chat; adding dense operational UI (columns, cards with state chips, timeline strips) fights its default message-oriented layout.

**Decision:** Ship a separate dashboard app (slice 20) as a new docker-compose service. Chainlit remains the operator/chat surface and gets nested-step upgrades but doesn't try to become a dashboard.

**Alternatives rejected:**
- **Chainlit-only upgrade** — Simpler (no new service) but caps demo polish; Chainlit's left-rail message layout isn't built for kanban columns or timeline strips, and custom elements are limited.
- **One unified SPA that replaces Chainlit** — Throws out working, tested Chainlit code; multiplies the cost of this cycle.

**Consequences:**
- Two surfaces, two audiences: Chainlit for hands-on operators (you, while testing), dashboard for pitch meetings and stakeholder review.
- New docker-compose service (slightly more to maintain).
- Information density and UX can be tailored per audience without compromise.

---

## DEC-18: Workflows as Python files, not YAML

**Status:** Accepted

**Context:** Slice 21 introduces a workflow registry. Each business workflow is a named assembly of agents + tasks + process + (optional) parallel/hierarchical config. This could live in YAML alongside `agents.yaml` and `tasks.yaml`, or in Python modules.

**Decision:** Workflows are Python files in `src/workflows/<name>.py`, each exporting a `Workflow` dataclass instance and auto-registering via `__init__.py`. Agents remain YAML-defined (`agents.yaml`), as do their generic task templates (`tasks.yaml`) when reusable.

**Alternatives rejected:**
- **Pure YAML workflows** — Works for simple pipelines, fails when tasks need parameterized prompts, conditional wiring, or references to Python-level tool instances. YAML also hides type errors until runtime.
- **Jinja-templated YAML** — Solves parameterization but introduces a templating layer that obscures logic; tests become harder to write; not reusable.
- **Database-stored workflows** — Overkill; workflows change rarely and are code-reviewed when they do.

**Consequences:**
- Workflows are importable, type-checked, and unit-testable (each file gets its own `test_<name>_workflow.py`).
- New workflows are PRs, not config pushes — acceptable for this project's scope.
- Agents stay declarative in YAML, preserving DEC-13's migration path.

---

## DEC-19: Hierarchical process is opt-in per workflow

**Status:** Accepted

**Context:** DEC-13 disabled delegation at the agent level because CrewAI's sequential process crashed when agents tried to delegate. Phase 4 wants hierarchical behavior for workflows where it makes sense (e.g., `support_triage`'s manager delegating to specialists).

**Decision:** `allow_delegation` defaults to `False` (DEC-13 stands). A workflow may opt in by declaring `process: "hierarchical"` and specifying `manager_agent`. Only in that case does `build_crew` enable delegation on participating agents.

**Alternatives rejected:**
- **All workflows hierarchical** — Doubles coordination cost (manager LLM calls) for workflows that don't need it.
- **All workflows sequential** — Loses the "manager delegates to subagents" demo surface that differentiates v4.0 from v3.0.
- **Per-agent `allow_delegation` flag in YAML** — Conflates workflow-level process with agent-level capability; a given agent may act as a lead in one workflow and a specialist in another.

**Consequences:**
- `research_report` (default) and most sequential workflows keep their fast, predictable behavior.
- `support_triage` gets real manager-delegates-to-specialist dynamics that show up in the live dashboard as hierarchical state transitions.
- Slice 22 test locks in that sequential workflows retain `allow_delegation=False`.

---

## DEC-20: Explicit parallel tasks via `async_execution=True`

**Status:** Accepted

**Context:** Workflows like `meeting_prep` and `real_estate_cma` have independent subtasks that could run concurrently. CrewAI supports `Task(async_execution=True)`, which returns a Future; subsequent sequential tasks await it.

**Decision:** Workflows declare `parallel_tasks: list[list[str]] | None`; each inner list is a concurrent group, groups run sequentially. Tasks in a concurrent group are built with `async_execution=True`.

**Alternatives rejected:**
- **Full DAG support** — More expressive but complicates UI (the kanban already struggles with non-linear dependencies); we don't need it yet.
- **Always sequential** — Forfeits real "waiting_on_agent" semantics, which is the entire point of the live team view.
- **Fork/join only at the workflow boundary** — Not flexible enough; `meeting_prep` needs two parallel-then-sequential-then-parallel patterns.

**Consequences:**
- `AgentStateBus` can legitimately emit `waiting_on_agent` events when a downstream task is blocked on parallel-group completion.
- Dashboard can show multiple `active` cards simultaneously (the "wow" moment).
- Workflows express exactly what's parallelizable; nothing is inferred.

---

## DEC-21: Twilio trial as the voice provider

**Status:** Accepted

**Context:** Slice 26 wants a free-tier API that can place outbound calls from a Python backend for demos. Options investigated: Twilio, Vonage, Telnyx, Plivo, SignalWire, self-hosted Asterisk/FreeSWITCH.

**Decision:** Use Twilio trial. Free ~$15.50 credit, free US inbound number, cleanest Python SDK, `<Gather input="speech">` provides built-in TTS + STT so no separate speech pipeline is needed for the demo. Telnyx documented as the pay-as-you-go fallback but not wired in v4.0.

**Alternatives rejected:**
- **Telnyx pay-as-you-go** — Cheapest per-minute but requires funding + ID verification before calling; higher friction for day-1 demos.
- **Vonage, Plivo** — Smaller trial credits, less-polished SDKs.
- **SignalWire** — Trial now requires credit card upfront.
- **Self-hosted Asterisk/FreeSWITCH** — Still needs a paid SIP trunk to reach PSTN; multi-hour setup.

**Consequences:**
- Twilio trial limits calls to *verified numbers* and prepends a trial-account message — fine for demos.
- Requires signup (Armando's task, external to the build).
- When trial credit runs out, the migration path to Telnyx is TwiML-compatible: minimal code changes (see DEC-21 fallback note in slice 26).
- Compliance constraint: TCPA (US). See DEC-22.

---

## DEC-22: Voice disabled by default (`VOICE_ENABLED=false`)

**Status:** Accepted

**Context:** Outbound voice calls carry real risks (TCPA statutory damages, trial credit burn, accidental spam during testing) that don't apply to the rest of the system. CI must never place a call.

**Decision:** Add `VOICE_ENABLED: bool = False` to settings. The `VoiceCallTool` checks this flag and raises `VoiceDisabledError` if anyone tries to dial while it's false. Additionally, a `TWILIO_VERIFIED_TO_NUMBERS` whitelist rejects dial targets that aren't pre-approved. `POST /crew/run workflow=receptionist voice.to=…` validates against the whitelist before starting execution.

**Alternatives rejected:**
- **Always on** — Trivial to cause accidental calls during test runs or fat-finger API hits.
- **On in dev, off in prod** — Inverts the risk (dev is where accidents happen).
- **Whitelist only, no kill-switch** — Whitelist could drift; an env-level kill switch gives Armando one toggle to make the entire voice layer inert.

**Consequences:**
- `make test` and CI never dial even if Twilio creds are present.
- Armando opts in per demo: `VOICE_ENABLED=true` + ngrok + ensure destination number is in the whitelist.
- Unit tests use mocked Twilio client; integration tests marked `@pytest.mark.voice` and opt-in only.
- README and `docs/demos/voice.md` have TCPA notices and the 15-minute first-call setup.

---

## DEC-23: WeasyPrint for PDF export

**Status:** Accepted

**Context:** Slice 27 needs to turn a completed run into a downloadable PDF. Options: WeasyPrint (pure-Python HTML/CSS → PDF), wkhtmltopdf (legacy, deprecated upstream), reportlab (imperative API), Puppeteer (headless Chromium).

**Decision:** Use WeasyPrint. Renders a Jinja-templated HTML file to PDF, supports modern CSS sufficient for our report layout.

**Alternatives rejected:**
- **wkhtmltopdf** — Deprecated; security-unmaintained.
- **reportlab** — Imperative; verbose; poor HTML fidelity.
- **Puppeteer / Playwright** — Brings a full browser into the container (~150 MB+); overkill for a report.

**Consequences:**
- Adds native-library deps (`pango`, `cairo`, `gdk-pixbuf`). Documented brew installs for Apple Silicon dev; apt installs for the Docker image.
- Report template lives in `src/templates/run_report.html`; easy to iterate.
- No client-side dependency — PDF is server-rendered and served via `GET /crew/history/{task_id}/pdf`.

---

## DEC-24: Signed shareable link (HMAC + 7-day TTL)

**Status:** Accepted

**Context:** A prospect in a pitch should be able to get a URL to a completed run, open it on their phone after the meeting, and show their team — without us provisioning accounts or exposing the whole history API.

**Decision:** Mint signed tokens via HMAC-SHA256 over `task_id + "|" + exp_unix` using `SHARE_SECRET`. Token encodes `task_id:exp_unix:sig`, base64url. `GET /share/{token}` verifies signature and expiry, then renders a whitelist of fields. TTL 7 days, fixed. Rotating `SHARE_SECRET` invalidates all outstanding tokens (manual revocation).

**Alternatives rejected:**
- **Per-user accounts + per-link ACL** — Overkill; portfolio project has no user model.
- **Random token with DB lookup** — Requires a `share_tokens` table and revocation bookkeeping; statelessness is preferable.
- **No sharing** — Prospects leave without a leave-behind; lost asset.
- **Longer TTL (30+ days)** — Shared links age poorly (LLM outputs embarrass over time); 7 days is a deliberate forcing function.

**Consequences:**
- Stateless — no DB roundtrip to verify.
- Revocation is coarse (rotate secret → invalidates everything) but acceptable.
- Whitelisted fields only in the rendered HTML (no raw tool I/O, no env config, no webhook URLs).
- `SHARE_SECRET` is a required env in production; auto-generated in dev with a warning so Armando notices.

---

## DEC-25: Deterministic fake LLM under `DEMO_MODE=true`

**Status:** Accepted

**Context:** A live pitch cannot depend on Ollama mood, network weather, or LLM hallucination. Prospects notice a stumbling demo.

**Decision:** Add `DEMO_MODE=true` env flag. When set, `LLMFactory.create()` returns a `FakeLLM` that serves responses from `src/demo/fixtures/<scenario>/<agent_role>.md`, keyed by `(workflow, topic, agent_role, task_index)`. Missing fixtures raise loudly.

**Alternatives rejected:**
- **Always-live** — Unreliable under demo conditions.
- **HTTP fixture cassettes (vcr.py)** — More general but couples demo reliability to the exact request shapes the LLM layer sends; fragile across CrewAI version bumps.
- **Pre-recorded video** — Works but kills interactivity; defeats the point of a live demo.

**Consequences:**
- Demos are byte-identical across runs, on any machine.
- Fixtures live in git (reviewable); drift is explicit, not silent.
- `DEMO_MODE=false` is default; CI exercises real LLM paths.
- Maintenance cost: each new workflow (23-25) adds one fixture set to `src/demo/fixtures/` during its slice.

---

## DEC-26: Next.js 14 (App Router, TS, Tailwind, shadcn/ui) for the dashboard

**Status:** Accepted

**Context:** Slice 20 builds the live team-view dashboard. Stack options range from zero-build (htmx + alpine.js as a single HTML file served by FastAPI) to a full SPA framework.

**Decision:** Next.js 14 with the App Router, TypeScript, Tailwind CSS, and shadcn/ui. Runs as a separate docker-compose service (`dashboard`) on port 3070. Python container stays pure.

**Alternatives rejected:**
- **htmx + alpine.js (zero-build)** — ~150 LOC of HTML; keeps repo Python-first with no `node_modules`. Rejected: user explicitly picked polish over minimalism; recruiter/prospect-facing surface justifies the Node footprint.
- **Svelte/SvelteKit** — Excellent fit for the animation-heavy live view, but smaller ecosystem, less familiar to reviewers.
- **Plain React (no framework)** — Loses file-based routing and app-dir conventions that make the code easy to navigate.
- **Vue/Nuxt** — Fine, but React is the lingua franca for portfolio dashboards.

**Consequences:**
- Repo now has two dev stacks (Python + Node); docker-compose abstracts this — `docker compose up` is still the one-command dev loop.
- Build/test pipeline grows: `npm install`, `npm test` (Vitest), `npm run test:e2e` (Playwright) in `dashboard/`.
- Portfolio surface is notably prettier (Tailwind, shadcn, Framer Motion transitions).
- Multi-stage `Dockerfile` keeps production image lean (~150 MB for Node 20 Alpine + built static).

### DEC-26a: shadcn/ui + Tailwind (no component-library lock-in)

**Status:** Accepted

**Context:** With Next.js chosen, the dashboard needs a component toolkit. Options: MUI, Chakra, shadcn/ui, DaisyUI, handrolled with Tailwind.

**Decision:** shadcn/ui + Tailwind + `lucide-react` for icons. shadcn primitives are copied into the repo (`dashboard/components/ui/*`), so there's no heavy dep and we own the source.

**Alternatives rejected:**
- **MUI / Chakra** — Large bundle, strong opinions, hard to restyle.
- **DaisyUI** — CSS-only; fine but shadcn's React primitives fit App Router + Server Components better.
- **Handrolled** — Spends design time we'd rather spend on data viz.

**Consequences:**
- Components are editable in-repo (good for portfolio showcase — reviewers can see the CSS).
- Upgrade path is manual (copy new primitive versions when needed).
- Bundle stays small.

### DEC-26b: Dashboard calls FastAPI directly over CORS (no BFF)

**Status:** Accepted

**Context:** Next.js supports Route Handlers that could proxy FastAPI calls (BFF pattern), keeping the API key server-side and shaping responses per page. Alternative: call FastAPI directly from the browser with CORS.

**Decision:** Browser → FastAPI directly. `NEXT_PUBLIC_API_URL` (e.g., `http://localhost:8060`) and `NEXT_PUBLIC_API_KEY` (dev-only) baked in at build time. CORS allow-list widened to include `http://localhost:3070`. For any operation requiring a protected secret (e.g., share token minting), that call still lives in a Next.js Route Handler so the secret never reaches the browser.

**Alternatives rejected:**
- **Full BFF** — Doubles routes, introduces a second auth hop, and adds latency for no benefit given single-origin deployments.
- **Embedded API key in the build** — Already the plan for dev; production uses a proxy-terminated auth where the browser has no API key and the dashboard backend re-attaches it.

**Consequences:**
- Fewer moving parts in dev; the browser is a first-class FastAPI client.
- Server-only work (PDF signing, share minting) intentionally stays in Next.js Route Handlers to keep secrets out of the bundle.
- CORS misconfiguration would be the top dev-time footgun — slice 20b locks it in with a regression test.

---

## DEC-27: In-process asyncio pub/sub for the Agent State Bus (not Redis)

**Status:** Accepted

**Context:** The `AgentStateBus` (slice 19) needs to deliver events from the crew background thread to SSE subscribers in the same process.

**Decision:** Implement `AgentStateBus` as an in-process asyncio pub/sub: a dict mapping `task_id` → list of `asyncio.Queue`-backed subscribers, with publish posting to all queues and subscribe yielding from a queue until a terminal event. Bounded queues with drop-oldest.

**Alternatives rejected:**
- **Redis Pub/Sub** — Needed only if we ever run multiple API instances; we don't, and Docker service count matters.
- **In-process asyncio `Broadcaster`-style library** — A small library would do the job, but we're talking ~30 lines of code; fewer deps is better.
- **Shared memory / multiprocessing queue** — Solves a problem we don't have.

**Consequences:**
- Zero new deps; trivial to test.
- Single-process only — the path to multi-instance would be swapping this class for a Redis-backed version (interface stays the same).
- Bounded queues prevent a stuck subscriber from OOM-ing the process.

---

## DEC-28: Agent events persist in `agent_events` SQLite table (extend, not new store)

**Status:** Accepted

**Context:** The shareable read-only page (slice 27) needs to reconstruct the full per-agent timeline of a completed run — after the in-process `AgentStateBus` has garbage-collected the queue and even after a server restart.

**Decision:** Add an `agent_events` table to the existing `data/results.db` SQLite file (managed by `src/services/sqlite_store.py`). Columns: `task_id`, `agent_role`, `state`, `detail`, `ts`. Insert rows from the state bus in parallel with live delivery. `replay(task_id)` returns rows in chronological order; `/share/{token}` hydrates the dashboard UI from this.

**Alternatives rejected:**
- **Separate store (new DB, new service class)** — Duplicates connection management and schema migration logic.
- **No persistence** — Shared links break across restarts; also rules out PDF export after the TaskStore TTL.
- **Store events as JSON blobs on the run row** — Harder to query, slower to render incrementally.

**Consequences:**
- One DB, one schema migration touchpoint (`sqlite_store._init_schema`).
- Live path and persistence share the same `AgentStateEvent` shape.
- Events retention matches the run row: 90 days by default, configurable; TTL cleanup is one DELETE query on startup.
- Slice 27 test 10 (`test_agent_events_table_replay_is_in_chronological_order`) locks in the behavior.
