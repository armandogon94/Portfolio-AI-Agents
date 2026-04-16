# AI Agent System
## CrewAI Multi-Agent Framework with RAG & Chainlit UI

---

## PROJECT OVERVIEW

Production-ready multi-agent system demonstrating:
- CrewAI framework (agent orchestration)
- Chainlit chat interface (user-friendly UI)
- Qdrant vector database (RAG/semantic search)
- Multiple specialized agents (research, analysis, writing)
- Industry-specific configurations (Healthcare, Finance, Real Estate, etc.)
- Tool integration (web search, document analysis, data retrieval)

**Why it matters:** Showcase of advanced AI capabilities. Demonstrates agentic AI patterns used in modern enterprise applications.

**Subdomain:** agents.305-ai.com

---

## TECH STACK

- **Agent Framework:** CrewAI 0.30+
- **Chat UI:** Chainlit 1.0+
- **Vector DB:** Qdrant 2.7+
- **Language Model:** Anthropic Claude (via API)
- **Backend:** FastAPI 0.104+
- **Vector Embeddings:** OpenAI or local model
- **Tools:** DuckDuckGo search, file reading, API calls

---

## ARCHITECTURE

```
User Interface (Chainlit)
        ↓
   CrewAI Agents
   ├── Research Agent (gather info)
   ├── Analysis Agent (process data)
   ├── Writing Agent (generate content)
   └── Validation Agent (quality check)
        ↓
   Tool Integration
   ├── Web Search (DuckDuckGo)
   ├── Document Retrieval (Qdrant RAG)
   ├── Data Analysis (Python)
   └── External APIs
        ↓
   Claude API (Intelligence)
```

---

## AGENT DEFINITIONS

### File: `agents/agents_config.py`

```python
from crewai import Agent, Task, Crew
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import ReadFileTool
from tools.document_retrieval import RagTool
from langchain.tools import Tool

# Initialize tools
search_tool = DuckDuckGoSearchRun()
read_file_tool = ReadFileTool()
rag_tool = RagTool()  # Custom Qdrant RAG

# RESEARCH AGENT
researcher = Agent(
    role="Research Analyst",
    goal="Find and summarize information about given topics",
    backstory="Expert researcher with deep knowledge across multiple domains",
    tools=[search_tool, rag_tool],
    verbose=True,
    allow_delegation=True
)

# ANALYSIS AGENT
analyst = Agent(
    role="Data Analyst",
    goal="Analyze information and extract key insights",
    backstory="Skilled analyst who uncovers patterns and trends",
    tools=[read_file_tool],
    verbose=True,
    allow_delegation=False
)

# WRITING AGENT
writer = Agent(
    role="Content Writer",
    goal="Create clear, engaging written content",
    backstory="Professional writer with strong communication skills",
    tools=[],
    verbose=True,
    allow_delegation=False
)

# VALIDATION AGENT
validator = Agent(
    role="Quality Assurance",
    goal="Ensure content accuracy and completeness",
    backstory="Meticulous reviewer focused on quality",
    tools=[],
    verbose=True,
    allow_delegation=False
)
```

### File: `agents/tasks_config.py`

```python
from crewai import Task

research_task = Task(
    description="Research the topic: {topic}",
    agent=researcher,
    expected_output="A comprehensive summary of findings with sources"
)

analysis_task = Task(
    description="Analyze the research findings and extract key insights",
    agent=analyst,
    expected_output="Key patterns, trends, and actionable insights"
)

writing_task = Task(
    description="Write a professional report based on the analysis",
    agent=writer,
    expected_output="Well-structured written report with clear recommendations"
)

validation_task = Task(
    description="Review the report for accuracy and completeness",
    agent=validator,
    expected_output="Quality assessment and any needed corrections"
)

# Create crew
crew = Crew(
    agents=[researcher, analyst, writer, validator],
    tasks=[research_task, analysis_task, writing_task, validation_task],
    verbose=True,
    process=Process.hierarchical,
    manager_agent=researcher
)
```

---

## RAG IMPLEMENTATION

### File: `tools/document_retrieval.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.tools import Tool
from typing import Optional

class RagTool:
    def __init__(self, collection_name: str = "documents"):
        self.client = QdrantClient(url="http://qdrant:6333")
        self.embeddings = OpenAIEmbeddings()
        self.collection_name = collection_name

    def ingest_document(self, doc_id: str, content: str):
        """Add document to vector database"""
        # Create embedding
        embedding = self.embeddings.embed_query(content)

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=hash(doc_id),
                    vector=embedding,
                    payload={"content": content, "doc_id": doc_id}
                )
            ]
        )

    def retrieve_similar(self, query: str, limit: int = 5) -> list:
        """Retrieve similar documents"""
        query_embedding = self.embeddings.embed_query(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )

        return [
            {
                "doc_id": hit.payload["doc_id"],
                "content": hit.payload["content"],
                "score": hit.score
            }
            for hit in results
        ]

    def to_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="document_search",
            func=lambda query: str(self.retrieve_similar(query)),
            description="Search documents using semantic similarity"
        )
```

---

## CHAINLIT INTERFACE

### File: `chainlit_app.py`

```python
import chainlit as cl
from crewai import Crew
from agents.agents_config import researcher, analyst, writer, validator
from agents.tasks_config import crew

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("crew", crew)
    cl.user_session.set("messages", [])

@cl.on_message
async def on_message(message: cl.Message):
    crew = cl.user_session.get("crew")
    messages = cl.user_session.get("messages")

    # Append user message
    messages.append({"role": "user", "content": message.content})

    # Show thinking process
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Execute crew
        result = crew.kickoff(inputs={"topic": message.content})

        # Send final response
        msg.content = result
        await msg.update()

        # Store in session
        messages.append({"role": "assistant", "content": result})
        cl.user_session.set("messages", messages)

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()

@cl.on_chat_end
def on_chat_end():
    print("Chat ended")
```

---

## INDUSTRY-SPECIFIC CONFIGURATIONS

### File: `configs/healthcare_config.py`

```python
healthcare_system_prompt = """
You are an expert healthcare analyst with knowledge of:
- Medical terminology and diagnoses
- Healthcare regulations (HIPAA, FDA)
- Clinical research methodologies
- Healthcare data analysis
- Treatment protocols and best practices

When analyzing healthcare topics, consider:
- Evidence-based medicine
- Patient safety and ethics
- Regulatory compliance
- Cost-effectiveness
"""

healthcare_tools = [
    DuckDuckGoSearchRun(),  # Medical research
    RagTool(),  # Internal healthcare documents
    # Custom clinical data retrieval tool
]
```

### File: `configs/finance_config.py`

```python
finance_system_prompt = """
You are an expert financial analyst with knowledge of:
- Investment strategies and portfolio management
- Financial modeling and valuation
- Risk analysis and compliance
- Market trends and economic indicators
- Financial reporting standards

When analyzing financial topics, consider:
- Regulatory requirements (SEC, FINRA)
- Tax implications
- Market volatility
- Return on investment metrics
"""
```

### File: `configs/real_estate_config.py`

```python
real_estate_system_prompt = """
You are an expert real estate analyst with knowledge of:
- Property valuation and appraisal
- Market analysis and trends
- Investment strategies
- Construction and development
- Real estate law and regulations

When analyzing real estate topics, consider:
- Comparable market analysis (CMA)
- Property condition assessment
- Financing options
- Market cycles and timing
"""
```

---

## DOCKER COMPOSE

```yaml
qdrant:
  image: qdrant/qdrant:latest
  container_name: qdrant
  ports:
    - "127.0.0.1:6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
  networks:
    - backend
  restart: unless-stopped

agents-api:
  image: ghcr.io/armando/agents-api:latest
  depends_on:
    - qdrant
  environment:
    QDRANT_HOST: qdrant
    QDRANT_PORT: 6333
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  networks:
    - backend
    - frontend
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
  restart: unless-stopped
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.agents.rule=Host(`agents.305-ai.com`)"
    - "traefik.http.routers.agents.entrypoints=websecure"
    - "traefik.http.routers.agents.tls.certresolver=letsencrypt"
    - "traefik.http.services.agents.loadbalancer.server.port=8000"
```

---

## ESTIMATED TIMELINE

- **Agent Setup:** 3 hours
- **RAG Implementation:** 2.5 hours
- **Chainlit UI:** 2 hours
- **Industry Configs:** 2 hours
- **Testing:** 1.5 hours

**Total:** ~11 hours

---

**Agent System Version:** 1.0
**Status:** Superseded by Phase 4 task plan below.

---

# Phase 4 — Portfolio Demos — Task Plan (v4.0)

> **Inputs:** [SPEC.md § "Phase 4 — Portfolio Demos"](SPEC.md), [DECISIONS.md DEC-16..DEC-28](DECISIONS.md), approved plan at `~/.claude/plans/analyze-the-current-state-temporal-quilt.md`.
> **Baseline:** `main` at `46b2feb` (rate-limiter fix after slice 18).
> **Status:** Written 2026-04-16. Execute slice-by-slice via `/build`.
> **Mode:** local Docker + TDD + vertical slices. No `/ship` this cycle.

## Planning method

Each slice from SPEC.md decomposes into **TDD sub-tasks** in this order:

1. **RED** — write failing tests (Vitest/pytest/Playwright as applicable). Run → confirm failure.
2. **GREEN** — implement just enough to pass. Run → confirm green.
3. **REFACTOR** — clean up, lint (`ruff check`, `tsc --noEmit`, `eslint`), reconfirm green.
4. **VERIFY** — docker/integration step (only when the slice crosses processes).
5. **COMMIT** — one `feat(slice-N): …` commit per slice unless explicitly noted.

Tasks are sized **S** (1-2 files) or **M** (3-5 files). If a task would touch more than 5 files, it's split.

## Skills per task type

| Task type | Primary skill | Also invoke |
|-----------|---------------|-------------|
| RED test writing | `test-driven-development` | `api-and-interface-design` when defining a new contract |
| GREEN backend code | `incremental-implementation` | `source-driven-development` (CrewAI, Twilio, WeasyPrint docs), `security-and-hardening` (auth, tokens, TCPA) |
| GREEN frontend code | `frontend-ui-engineering` | `source-driven-development` (Next.js App Router, shadcn/ui) |
| Registry migration (slice 21) | `deprecation-and-migration` | `incremental-implementation` |
| Review after slice | `code-review-and-quality` | `security-and-hardening` (voice/share/CORS), `performance-optimization` (SSE, parallel tasks) |
| Context management (many workflow files) | `context-engineering` | — |

## Dependency graph (execution order)

```
19 (State Bus + SSE)
   │
   ├─► 20a (Dashboard scaffold)
   │       │
   │       ▼
   │    21 (Workflow Registry)
   │       │
   │       ├─► 20b (Launcher + history) ───────┐
   │       │                                   │
   │       └─► 22 (Hierarchical + Parallel) ───┤
   │                                           ▼
   └───────────────────────────────────────► 20c (Live team view)
                                               │
                                               ├─► 23 (Sales pack)
                                               ├─► 24 (Support & Ops pack)
                                               ├─► 25 (Content & RE pack)
                                               ├─► 26 (Voice receptionist)
                                               ▼
                                           27 (Share + PDF) ───► 28 (Demo harness)
```

**Rationale:** 19 first (foundation). 20a before 21 so the dashboard service exists to receive the `GET /workflows` contract. 21 before 20b so the launcher is real. 22 before 23-25 because those workflows rely on hierarchical/parallel process support. 20c after 22 so the live view can exercise parallel cards. 26 before 27 because the share page whitelist must already know about voice-run shape. 28 last because it needs fixtures for all preceding workflows.

---

## Slice 19 — Agent State Bus + SSE endpoint

**Dependencies:** none (touches `src/` only).
**Target commit:** `feat(slice-19): agent state bus and SSE events endpoint`.

### Tasks

- [ ] **19.1 — RED: `AgentStateBus` tests** (S)
  - Acceptance: 5 failing tests in `tests/unit/test_agent_state_bus.py` (publish→subscribe, multi-subscriber same task, task isolation, queue-full drop, TTL cleanup).
  - Verify: `uv run pytest tests/unit/test_agent_state_bus.py` → 5 FAIL.
  - Files: `tests/unit/test_agent_state_bus.py` (new).

- [ ] **19.2 — RED: SSE endpoint tests** (S)
  - Acceptance: 4 failing tests in `tests/unit/test_sse_endpoint.py` (unknown 404, ordered events via TestClient stream, auto-close on terminal event, auth gating).
  - Verify: `uv run pytest tests/unit/test_sse_endpoint.py` → 4 FAIL.
  - Files: `tests/unit/test_sse_endpoint.py` (new).

- [ ] **19.3 — GREEN: `AgentStateBus` implementation** (S)
  - Acceptance: 19.1 tests pass; `asyncio.Queue`-per-subscriber, bounded (maxsize=1000), drop-oldest-with-WARN logging, per-`task_id` subscriber list, TTL cleanup on publish.
  - Verify: `uv run pytest tests/unit/test_agent_state_bus.py -v` → 5 PASS.
  - Files: `src/services/state_bus.py` (new), `src/dependencies.py` (expose singleton).

- [ ] **19.4 — GREEN: Event model + crew wiring** (S)
  - Acceptance: `AgentStateEvent` Pydantic model, `AgentRunState` enum; `src/crew.py` step_callback emits events to the bus via `asyncio.run_coroutine_threadsafe` (same pattern as Chainlit streaming).
  - Verify: manual — run crew, tail bus in a test script; no syntax errors.
  - Files: `src/models/schemas.py` (edit), `src/crew.py` (edit).

- [ ] **19.5 — GREEN: SSE endpoint** (S)
  - Acceptance: `GET /crew/run/{task_id}/events` returns `StreamingResponse(media_type="text/event-stream")`; emits `event: agent_state` and `event: run_complete`; 15s heartbeat comment; `X-Accel-Buffering: no`. 19.2 tests pass.
  - Verify: `uv run pytest tests/unit/test_sse_endpoint.py -v` → 4 PASS; `curl -N http://localhost:8060/crew/run/{id}/events` while a run is active prints event lines.
  - Files: `src/main.py` (edit).

- [ ] **19.6 — REFACTOR + VERIFY** (S)
  - Acceptance: `uv run ruff check src/ tests/` clean; full suite `uv run pytest -m unit` green; manual curl smoke test passes.
  - Verify: `uv run pytest -m unit && uv run ruff check src/ tests/`.

- [ ] **19.7 — COMMIT** (S)
  - `git add src/services/state_bus.py src/models/schemas.py src/crew.py src/main.py src/dependencies.py tests/unit/test_agent_state_bus.py tests/unit/test_sse_endpoint.py && git commit -m "feat(slice-19): agent state bus and SSE events endpoint"`.

### Checkpoint 19
- [ ] 152 prior unit tests + 9 new = 161 green.
- [ ] `curl -N` smoke shows live events.
- [ ] No regressions in existing streaming (Chainlit `on_step`).

---

## Slice 20a — Next.js Dashboard scaffold + CI

**Dependencies:** none (new directory).
**Target commit:** `feat(slice-20a): scaffold next.js dashboard service on port 3061`.

### Tasks

- [ ] **20a.1 — PORTS.md check** (S)
  - Acceptance: port 3061 free; PORTS.md updated with `3061 → Dashboard (dev)`.
  - Verify: grep PORTS.md across all portfolio projects (if tracked); none collide.
  - Files: `PORTS.md` (edit).

- [ ] **20a.2 — Scaffold Next.js app** (M)
  - Acceptance: `dashboard/` created via `npx create-next-app@latest dashboard --ts --tailwind --app --no-src-dir --eslint --import-alias "@/*"`; app runs on `npm run dev`.
  - Verify: `cd dashboard && npm install && npm run build` → exits 0.
  - Files: `dashboard/app/*`, `dashboard/package.json`, `dashboard/tsconfig.json`, `dashboard/next.config.js`, `dashboard/tailwind.config.ts`, `dashboard/postcss.config.js`, `dashboard/.eslintrc.json`, `dashboard/.env.example`.

- [ ] **20a.3 — Add Vitest + Playwright configs** (M)
  - Acceptance: `npm test` runs Vitest; `npm run test:e2e` runs Playwright against `http://localhost:3061`; `vitest.config.ts` + `playwright.config.ts` committed.
  - Verify: `cd dashboard && npm test` → 0 tests OK; `npm run test:e2e` → 0 tests OK.
  - Files: `dashboard/vitest.config.ts`, `dashboard/playwright.config.ts`, `dashboard/package.json` (edit scripts), dev-deps install.

- [ ] **20a.4 — RED smoke tests** (S)
  - Acceptance: `__tests__/smoke.test.tsx` asserts title "AI Agent Team Dashboard"; `e2e/home.spec.ts` asserts same on `http://localhost:3061`. Both initially fail (title not set).
  - Verify: `npm test && npm run test:e2e` → FAIL.
  - Files: `dashboard/__tests__/smoke.test.tsx`, `dashboard/e2e/home.spec.ts`.

- [ ] **20a.5 — GREEN: set title + landing layout** (S)
  - Acceptance: `app/layout.tsx` sets `metadata.title`; `app/page.tsx` renders the title. 20a.4 tests pass.
  - Verify: `npm test && npm run test:e2e` → PASS.
  - Files: `dashboard/app/layout.tsx`, `dashboard/app/page.tsx`.

- [ ] **20a.6 — docker-compose wiring** (M)
  - Acceptance: `dashboard` service in `docker-compose.dev.yml` (node:20-alpine, port 3061:3000, volume-mount, `npm ci && npm run dev`, `depends_on: [agents-api]`, env `NEXT_PUBLIC_API_URL=http://localhost:8060`). `docker compose up` brings 4 healthy services.
  - Verify: `docker compose -f docker-compose.dev.yml config` validates; `docker compose up -d && docker compose ps` → all `healthy`.
  - Files: `docker-compose.dev.yml` (edit).

- [ ] **20a.7 — prod Dockerfile** (S)
  - Acceptance: `dashboard/Dockerfile` multi-stage (`deps` → `builder` → `runner`, node:20-alpine); `docker-compose.prod.yml` uses it with healthcheck on `/`.
  - Verify: `docker build -f dashboard/Dockerfile dashboard/` → exits 0; prod compose `config` validates.
  - Files: `dashboard/Dockerfile` (new), `docker-compose.prod.yml` (edit).

- [ ] **20a.8 — README update + COMMIT** (S)
  - Acceptance: README has "Dashboard" section with `cd dashboard && npm install && npm run dev`; commit as one unit.
  - Verify: `git diff --stat` shows expected files only; `git commit`.

### Checkpoint 20a
- [ ] 4 services healthy under `docker compose up`.
- [ ] Vitest + Playwright green.
- [ ] No Python test regressions.

---

## Slice 21 — Workflow Registry

**Dependencies:** Slice 19 (bus is consumed by `build_crew` already; no change needed — but keep sequential workflows emitting the same events).
**Target commit:** `feat(slice-21): pluggable workflow registry`.

### Tasks

- [ ] **21.1 — RED: registry tests** (S)
  - Acceptance: 4 failing tests in `tests/unit/test_workflow_registry.py` (register, get, unknown→raise, duplicate→raise).
  - Verify: `uv run pytest tests/unit/test_workflow_registry.py` → 4 FAIL.
  - Files: `tests/unit/test_workflow_registry.py` (new).

- [ ] **21.2 — RED: research_report migration tests** (S)
  - Acceptance: 3 failing tests in `tests/unit/test_research_report_workflow.py` (registered by name, produces crew with 4 agents, matches golden output shape for sample topic).
  - Verify: `uv run pytest tests/unit/test_research_report_workflow.py` → 3 FAIL.
  - Files: `tests/unit/test_research_report_workflow.py` (new).

- [ ] **21.3 — RED: endpoint integration tests** (S)
  - Acceptance: 3 failing tests in `tests/unit/test_workflows_endpoint.py` (GET /workflows returns list, POST /crew/run default workflow = research_report, unknown workflow → 422).
  - Verify: `uv run pytest tests/unit/test_workflows_endpoint.py` → 3 FAIL.
  - Files: `tests/unit/test_workflows_endpoint.py` (new).

- [ ] **21.4 — GREEN: registry module** (M)
  - Acceptance: 21.1 + 21.2 pass. `Workflow` dataclass (name, description, agent_roles, task_specs, process, parallel_tasks, inputs_schema), `register_workflow()`, `get_workflow()`, `list_workflows()`. Auto-discovery via `__init__.py`.
  - Verify: `uv run pytest tests/unit/test_workflow_registry.py tests/unit/test_research_report_workflow.py -v` → 7 PASS.
  - Files: `src/workflows/__init__.py` (new), `src/workflows/base.py` (new), `src/workflows/research_report.py` (new — migrated from `src/crew.py`), `src/crew.py` (edit — delegate to registry).

- [ ] **21.5 — GREEN: API schema + endpoint** (S)
  - Acceptance: 21.3 passes. `CrewRunRequest.workflow: str = "research_report"`, `WorkflowInfo` model, `GET /workflows` route.
  - Verify: `uv run pytest tests/unit/test_workflows_endpoint.py -v` → 3 PASS; all v2/v3 tests still pass (`uv run pytest -m unit`).
  - Files: `src/models/schemas.py` (edit), `src/main.py` (edit).

- [ ] **21.6 — REFACTOR + VERIFY** (S)
  - Acceptance: `ruff check` clean; full suite green; no behavior change for research_report runs (byte-compatible output for the golden sample).
  - Verify: `uv run pytest -m unit && uv run ruff check src/ tests/`.

- [ ] **21.7 — COMMIT** (S)

### Checkpoint 21
- [ ] 10 new tests green; 161 prior still green (171 total).
- [ ] `POST /crew/run` without `workflow` field produces identical output to pre-21.
- [ ] `GET /workflows` returns a JSON list with `research_report` present.

---

## Slice 20b — Run launcher + history

**Dependencies:** Slice 20a (scaffold), Slice 21 (workflows endpoint).
**Target commit:** `feat(slice-20b): dashboard launcher and history pages`.

### Tasks

- [ ] **20b.1 — Install MSW + set up handlers** (S)
  - Acceptance: MSW 2.x installed; `dashboard/__tests__/mocks/handlers.ts` stubs `GET /workflows`, `POST /crew/run`, `GET /crew/history`.
  - Verify: `npm test` still green.
  - Files: `dashboard/package.json` (edit), `dashboard/__tests__/mocks/handlers.ts` (new), `dashboard/__tests__/setup.ts` (edit).

- [ ] **20b.2 — RED: launcher tests** (M)
  - Acceptance: 3 failing tests in `launcher.test.tsx` (renders form fields, submits → navigates to `/runs/:id`, empty-topic shows error).
  - Verify: `npm test` → 3 FAIL.
  - Files: `dashboard/__tests__/launcher.test.tsx` (new).

- [ ] **20b.3 — RED: history tests** (S)
  - Acceptance: 2 failing tests in `history.test.tsx` (renders 3 rows, empty state).
  - Verify: `npm test` → 2 FAIL.
  - Files: `dashboard/__tests__/history.test.tsx` (new).

- [ ] **20b.4 — GREEN: API client + types** (S)
  - Acceptance: `lib/api.ts` (`apiClient.runCrew`, `listWorkflows`, `listHistory`), `lib/types.ts` (TS mirrors of Python schemas). No tests yet.
  - Verify: `npm run build && tsc --noEmit` → clean.
  - Files: `dashboard/lib/api.ts` (new), `dashboard/lib/types.ts` (new).

- [ ] **20b.5 — GREEN: launcher page** (M)
  - Acceptance: 20b.2 passes. `app/page.tsx` renders form using shadcn `Select`/`Input`/`Button`; client component; on submit calls `apiClient.runCrew()` → `router.push('/runs/'+id)`. shadcn primitives installed via `npx shadcn@latest add select input button card`.
  - Verify: `npm test -- launcher` → 3 PASS.
  - Files: `dashboard/app/page.tsx`, `dashboard/components/WorkflowSelector.tsx` (new), `dashboard/components/ui/*` (shadcn).

- [ ] **20b.6 — GREEN: history page** (S)
  - Acceptance: 20b.3 passes. `app/runs/page.tsx` renders table from `listHistory()`.
  - Verify: `npm test -- history` → 2 PASS.
  - Files: `dashboard/app/runs/page.tsx` (new).

- [ ] **20b.7 — CORS widening (backend)** (S)
  - Acceptance: `DASHBOARD_ORIGIN` setting; `src/main.py` CORS allow-list includes `DASHBOARD_ORIGIN` in dev; regression test `tests/unit/test_cors.py` asserts the origin is allowed.
  - Verify: `uv run pytest tests/unit/test_cors.py -v` → PASS including new assertion.
  - Files: `src/config/settings.py` (edit), `src/main.py` (edit), `tests/unit/test_cors.py` (edit).

- [ ] **20b.8 — Playwright E2E** (S)
  - Acceptance: `e2e/launcher.spec.ts` fills form + submits against the running stack (DEMO_MODE=true crew so no real LLM) and lands on `/runs/*`.
  - Verify: `npm run test:e2e -- launcher` → PASS.
  - Files: `dashboard/e2e/launcher.spec.ts` (new).

- [ ] **20b.9 — REFACTOR + COMMIT** (S)

### Checkpoint 20b
- [ ] Launcher + history live against the real API; E2E green.
- [ ] CORS test locks in port 3061 origin.

---

## Slice 22 — Hierarchical + Parallel Processes

**Dependencies:** Slice 21 (registry).
**Target commit:** `feat(slice-22): hierarchical and parallel crew process support`.

### Tasks

- [ ] **22.1 — RED: hierarchical tests** (S)
  - Acceptance: 3 failing tests in `tests/unit/test_hierarchical_process.py` (manager agent required, sequential stays non-delegating, unknown manager → ConfigurationError).
  - Verify: `uv run pytest tests/unit/test_hierarchical_process.py` → 3 FAIL.
  - Files: `tests/unit/test_hierarchical_process.py` (new).

- [ ] **22.2 — RED: parallel tests** (S)
  - Acceptance: 3 failing tests in `tests/unit/test_parallel_tasks.py` (tasks marked `async_execution=True`, state bus emits `waiting_on_agent`, fan-in completes in expected order).
  - Verify: `uv run pytest tests/unit/test_parallel_tasks.py` → 3 FAIL.
  - Files: `tests/unit/test_parallel_tasks.py` (new).

- [ ] **22.3 — GREEN: Workflow base extension** (S)
  - Acceptance: `src/workflows/base.py` gains `process`, `manager_agent`, `parallel_tasks`. Type-checked.
  - Verify: `uv run pytest tests/unit/test_workflow_registry.py` still green.
  - Files: `src/workflows/base.py` (edit).

- [ ] **22.4 — GREEN: build_crew extension** (M)
  - Acceptance: 22.1 + 22.2 pass. `build_crew` honors `process="hierarchical"` (enables delegation on participating agents, sets manager), honors `parallel_tasks` (sets `async_execution=True`). State bus emits `waiting_on_agent` when a downstream task is blocked.
  - Verify: `uv run pytest tests/unit/test_hierarchical_process.py tests/unit/test_parallel_tasks.py -v` → 6 PASS.
  - Files: `src/crew.py` (edit), `src/services/state_bus.py` (edit — emit waiting_on_agent).

- [ ] **22.5 — REFACTOR + VERIFY** (S)
  - Acceptance: research_report remains sequential, `allow_delegation=False` (regression); full suite green.
  - Verify: `uv run pytest -m unit` → all green.

- [ ] **22.6 — COMMIT** (S)

### Checkpoint 22
- [ ] 6 new tests green; sequential workflows unchanged.
- [ ] Synthetic hierarchical test workflow produces delegation events in the bus.

---

## Slice 20c — Live team view (SSE)

**Dependencies:** Slice 19 (SSE), Slice 22 (parallel cards to demo).
**Target commit:** `feat(slice-20c): live team-view kanban with SSE`.

### Tasks

- [ ] **20c.1 — RED: run-view tests (scripted SSE)** (M)
  - Acceptance: 4 failing tests in `__tests__/run-view.test.tsx` (cards render per agent, move columns on events, waiting_on_agent highlights correct blocker, run_complete stops elapsed counter).
  - Verify: `npm test -- run-view` → 4 FAIL.
  - Files: `dashboard/__tests__/run-view.test.tsx` (new), `dashboard/__tests__/mocks/sse.ts` (new — mock EventSource that replays a scripted sequence).

- [ ] **20c.2 — RED: Playwright live-run** (S)
  - Acceptance: `e2e/live-run.spec.ts` launches a `DEMO_MODE=true` research_report run from `/`, opens `/runs/[id]`, asserts full queued→active→done sequence. Initially fails (components not built).
  - Verify: `npm run test:e2e -- live-run` → FAIL.
  - Files: `dashboard/e2e/live-run.spec.ts` (new).

- [ ] **20c.3 — GREEN: typed SSE client** (S)
  - Acceptance: `lib/sse.ts` — typed `useAgentEvents(taskId)` hook that wraps `EventSource`, reconnects on error, closes on `run_complete`. Proper useEffect cleanup for StrictMode double-mount.
  - Verify: No runtime errors in the test harness.
  - Files: `dashboard/lib/sse.ts` (new).

- [ ] **20c.4 — GREEN: kanban components** (M)
  - Acceptance: `AgentCard.tsx` (role chip, state chip, current task, tool log), `StateChip.tsx` (colored badge per state), `KanbanColumn.tsx` (header + card slot), `ToolLog.tsx` (collapsible), `TimelineStrip.tsx` (horizontal bar). Framer Motion for card transitions (≤200ms, respects `prefers-reduced-motion`).
  - Verify: Storybook-less visual check — `npm run dev`, open `/runs/test-id` with a mocked event stream.
  - Files: `dashboard/components/AgentCard.tsx`, `dashboard/components/StateChip.tsx`, `dashboard/components/KanbanColumn.tsx`, `dashboard/components/ToolLog.tsx`, `dashboard/components/TimelineStrip.tsx` (all new).

- [ ] **20c.5 — GREEN: `/runs/[id]/page.tsx`** (S)
  - Acceptance: 20c.1 passes. Client component, reducer keyed by `agent_role`, 4 Kanban columns, timeline strip, elapsed-time counter, "Copy Share Link" + "Export PDF" buttons (disabled until slice 27).
  - Verify: `npm test -- run-view` → 4 PASS.
  - Files: `dashboard/app/runs/[id]/page.tsx` (new).

- [ ] **20c.6 — VERIFY: Playwright live-run** (S)
  - Acceptance: 20c.2 passes against the running stack.
  - Verify: `npm run test:e2e -- live-run` → PASS.

- [ ] **20c.7 — REFACTOR + COMMIT** (S)

### Checkpoint 20c
- [ ] Live view renders cards in real time for both sequential and parallel crew runs.
- [ ] Full dashboard test suite (Vitest + Playwright) green.
- [ ] Python suite unchanged.

---

## Slice 23 — Business Workflow Pack 1 (Sales)

**Dependencies:** Slice 22 (parallel support), Slice 21 (registry).
**Target commit:** `feat(slice-23): sales workflow pack — lead_qualifier + sdr_outreach`.

### Tasks

- [ ] **23.1 — RED: lead_qualifier tests** (S)
  - Acceptance: 3 failing tests (output schema matches, score in 0-100, evidence_links present).
  - Files: `tests/unit/test_lead_qualifier_workflow.py` (new).

- [ ] **23.2 — RED: sdr_outreach tests** (S)
  - Acceptance: 3 failing tests (three distinct variants, tone_checker picks one, variants differ by non-trivial diff threshold).
  - Files: `tests/unit/test_sdr_outreach_workflow.py` (new).

- [ ] **23.3 — GREEN: extend agents.yaml** (S)
  - Acceptance: new agent roles (`scorer`, `report_writer`, `persona_researcher`, `copywriter`, `tone_checker`) with backstories + tools + domain-independent defaults.
  - Files: `src/config/agents.yaml` (edit).

- [ ] **23.4 — GREEN: lead_qualifier workflow** (S)
  - Acceptance: 23.1 passes. Sequential 3-agent workflow with rubric constant and JSON output validator.
  - Files: `src/workflows/lead_qualifier.py` (new).

- [ ] **23.5 — GREEN: sdr_outreach workflow** (S)
  - Acceptance: 23.2 passes. Parallel drafting (3 copywriters), tone_checker picks winner.
  - Files: `src/workflows/sdr_outreach.py` (new).

- [ ] **23.6 — Demo doc** (S)
  - Acceptance: `docs/demos/sales.md` with 5-min click-by-click pitch script for both workflows.
  - Files: `docs/demos/sales.md` (new).

- [ ] **23.7 — REFACTOR + COMMIT** (S)

### Checkpoint 23
- [ ] Both workflows run end-to-end from the dashboard.
- [ ] Live team view shows 3 parallel copywriters simultaneously (visual proof of slice 22).

---

## Slice 24 — Business Workflow Pack 2 (Support & Ops)

**Dependencies:** Slice 22.
**Target commit:** `feat(slice-24): support workflow pack — support_triage + meeting_prep`.

### Tasks

- [ ] **24.1 — RED: support_triage tests** (S)
  - Acceptance: 3 failing tests (uses hierarchical process, output schema, manager delegates visible in events).
  - Files: `tests/unit/test_support_triage_workflow.py` (new).

- [ ] **24.2 — RED: meeting_prep tests** (S)
  - Acceptance: 3 failing tests (parallel attendee + topic researchers, agenda depends on both, talking_points runs last).
  - Files: `tests/unit/test_meeting_prep_workflow.py` (new).

- [ ] **24.3 — GREEN: extend agents.yaml** (S)
  - Acceptance: `triage_manager`, `kb_searcher`, `sentiment_analyst`, `response_writer`, `attendee_researcher`, `topic_researcher`, `agenda_writer`, `talking_points_writer`.
  - Files: `src/config/agents.yaml` (edit).

- [ ] **24.4 — GREEN: support_triage workflow** (S)
  - Acceptance: 24.1 passes. Hierarchical with `triage_manager`.
  - Files: `src/workflows/support_triage.py` (new).

- [ ] **24.5 — GREEN: meeting_prep workflow** (S)
  - Acceptance: 24.2 passes. Sequential + parallel groups.
  - Files: `src/workflows/meeting_prep.py` (new).

- [ ] **24.6 — Demo doc** (S)
  - Files: `docs/demos/support.md` (new).

- [ ] **24.7 — REFACTOR + COMMIT** (S)

### Checkpoint 24
- [ ] Hierarchical + parallel patterns both demoable.

---

## Slice 25 — Business Workflow Pack 3 (Content & RE)

**Dependencies:** Slice 22.
**Target commit:** `feat(slice-25): content_pipeline + real_estate_cma workflows`.

### Tasks

- [ ] **25.1 — RED: content_pipeline tests** (S) — schema, markdown has headers, 5-agent pipeline registered.
- [ ] **25.2 — RED: real_estate_cma tests** (S) — parallel gather+market, estimated_value_range has low+high, confidence present.
- [ ] **25.3 — GREEN: extend agents.yaml** (S) — `outliner`, `editor`, `seo_optimizer`, `comps_gatherer`, `market_analyst`, `appraiser`.
- [ ] **25.4 — GREEN: content_pipeline workflow** (S).
- [ ] **25.5 — GREEN: real_estate_cma workflow** (S).
- [ ] **25.6 — Demo doc** (S) — `docs/demos/verticals.md`.
- [ ] **25.7 — REFACTOR + COMMIT** (S).

### Checkpoint 25
- [ ] All 6 new business workflows run end-to-end (5 new this slice's pack + 2 from slice 23 + 2 from slice 24 - research_report already existed).

---

## Slice 26 — Voice-capable receptionist (Twilio trial)

**Dependencies:** Slice 21 (registry), Slice 22 (sequential + tool plumbing).
**Target commit:** `feat(slice-26): twilio-trial voice receptionist workflow`.

### Tasks

- [ ] **26.1 — Dependency install** (S)
  - Acceptance: `twilio` added to `pyproject.toml`; `uv sync` updates lockfile.
  - Verify: `uv run python -c "import twilio; print(twilio.__version__)"`.
  - Files: `pyproject.toml` (edit).

- [ ] **26.2 — RED: VoiceCallTool tests** (S)
  - Acceptance: 3 failing tests (disabled-by-default raises, enabled calls Twilio with expected args via mock, `TWILIO_VERIFIED_TO_NUMBERS` whitelist rejects).
  - Files: `tests/unit/test_voice_tool.py` (new).

- [ ] **26.3 — RED: TwiML webhook tests** (S)
  - Acceptance: 4 failing tests (valid XML, rejects unsigned request, rejects unknown task_id, ends call after max_turns).
  - Files: `tests/unit/test_twiml_webhook.py` (new).

- [ ] **26.4 — RED: receptionist workflow test** (S)
  - Acceptance: 1 failing test (produces summary when mocked call completes).
  - Files: `tests/unit/test_receptionist_workflow.py` (new).

- [ ] **26.5 — GREEN: settings + schemas** (S)
  - Acceptance: `VOICE_ENABLED`, `TWILIO_*`, `TWILIO_VERIFIED_TO_NUMBERS`, `TWILIO_WEBHOOK_BASE`; `CrewRunRequest.voice: VoiceOptions | None` with `to`, `max_turns=6`, `max_duration_s=120`.
  - Files: `src/config/settings.py` (edit), `src/models/schemas.py` (edit).

- [ ] **26.6 — GREEN: VoiceCallTool** (M)
  - Acceptance: 26.2 passes. Registered in tool registry; raises `VoiceDisabledError` when off; verifies destination against whitelist before dialing.
  - Files: `src/tools/voice.py` (new), `src/exceptions.py` (edit — add `VoiceDisabledError`).

- [ ] **26.7 — GREEN: voice session state + workflow** (M)
  - Acceptance: 26.4 passes. `VoiceSession` state machine per task_id; `receptionist` workflow wires intake → caller → summary.
  - Files: `src/services/voice_session.py` (new), `src/workflows/receptionist.py` (new).

- [ ] **26.8 — GREEN: TwiML webhook endpoint** (M)
  - Acceptance: 26.3 passes. `POST /voice/twiml/{task_id}` verifies `X-Twilio-Signature` HMAC using `TWILIO_AUTH_TOKEN`; returns TwiML from the next utterance. Never logs full signature.
  - Files: `src/main.py` (edit), `src/middleware/auth.py` (edit — skip auth on this route but wrap in Twilio-signature check).

- [ ] **26.9 — Integration test (opt-in)** (S)
  - Acceptance: `tests/integration/test_twilio_live.py` marked `@pytest.mark.voice`; README has toggle instructions.
  - Files: `tests/integration/test_twilio_live.py` (new).

- [ ] **26.10 — Demo doc + README** (S)
  - Acceptance: `docs/demos/voice.md` with 15-min first-call setup (ngrok, Twilio signup, verified numbers); README TCPA banner.
  - Files: `docs/demos/voice.md` (new), `README.md` (edit).

- [ ] **26.11 — REFACTOR + COMMIT** (S)

### Checkpoint 26
- [ ] All unit tests green; no CI call to Twilio.
- [ ] `VOICE_ENABLED=false` hard-blocks dialing.
- [ ] Twilio signature check enforced on webhook.

---

## Slice 27 — Shareable read-only run page + PDF export

**Dependencies:** Slice 19 (events in bus), Slice 20c (run-view components), Slice 26 (voice run shape known).
**Target commit:** `feat(slice-27): shareable run page + weasyprint pdf export`.

### Tasks

- [ ] **27.1 — Dependency install** (S) — `weasyprint` in `pyproject.toml`; Apple Silicon brew deps documented in README.

- [ ] **27.2 — RED: share_token tests** (S)
  - Acceptance: 3 failing tests (mint/verify roundtrip, tampered fails, expired raises).
  - Files: `tests/unit/test_share_token.py` (new).

- [ ] **27.3 — RED: share_route tests** (S)
  - Acceptance: 4 failing tests (valid→200 HTML, invalid→403, expired→410, unknown task_id→404).
  - Files: `tests/unit/test_share_route.py` (new).

- [ ] **27.4 — RED: pdf_export tests** (S)
  - Acceptance: 2 failing tests (valid PDF bytes via magic header, requires API key).
  - Files: `tests/unit/test_pdf_export.py` (new).

- [ ] **27.5 — RED: agent_events persistence test** (S)
  - Acceptance: 1 failing test (replay returns rows in chronological order).
  - Files: `tests/unit/test_sqlite_store.py` (edit).

- [ ] **27.6 — GREEN: share_token service** (S)
  - Acceptance: 27.2 passes. `SHARE_SECRET` setting; HMAC-SHA256 over `task_id|exp_unix`; dev auto-gen with WARN.
  - Files: `src/services/share_token.py` (new), `src/config/settings.py` (edit).

- [ ] **27.7 — GREEN: agent_events table + replay** (M)
  - Acceptance: 27.5 passes. Schema migration on init; state bus writes events in parallel with live delivery; `replay(task_id)` method.
  - Files: `src/services/sqlite_store.py` (edit), `src/services/state_bus.py` (edit).

- [ ] **27.8 — GREEN: share route + whitelist render** (M)
  - Acceptance: 27.3 passes. `GET /share/{token}` returns HTML with whitelisted fields only (no tool I/O, no env, no webhook URLs). Uses Jinja template.
  - Files: `src/main.py` (edit), `src/templates/run_report.html` (new).

- [ ] **27.9 — GREEN: pdf export** (S)
  - Acceptance: 27.4 passes. `GET /crew/history/{task_id}/pdf` renders the same template via WeasyPrint.
  - Files: `src/services/pdf_export.py` (new), `src/main.py` (edit).

- [ ] **27.10 — GREEN: dashboard share page** (S)
  - Acceptance: `dashboard/app/share/[token]/page.tsx` reuses 20c components in read-only mode (no launcher buttons).
  - Files: `dashboard/app/share/[token]/page.tsx` (new).

- [ ] **27.11 — GREEN: wire up buttons on `/runs/[id]`** (S)
  - Acceptance: "Copy Share Link" fetches token via Next.js Route Handler `app/api/share/mint/route.ts` (server-side to keep `SHARE_SECRET` out of browser); "Export PDF" downloads.
  - Files: `dashboard/app/runs/[id]/page.tsx` (edit), `dashboard/app/api/share/mint/route.ts` (new).

- [ ] **27.12 — REFACTOR + COMMIT** (S)

### Checkpoint 27
- [ ] Share link opens in a private window with no auth; renders timeline from `agent_events` even after server restart.
- [ ] PDF downloads cleanly on macOS.
- [ ] `SHARE_SECRET` rotation invalidates all outstanding tokens (manual verification).

---

## Slice 28 — Demo Harness

**Dependencies:** Slices 23, 24, 25, 26 (workflows to demo).
**Target commit:** `feat(slice-28): deterministic demo harness and fake llm`.

### Tasks

- [ ] **28.1 — RED: fake_llm tests** (S)
  - Acceptance: 3 failing tests (returns fixture for known key, raises on missing fixture, DEMO_MODE off → live LLM).
  - Files: `tests/unit/test_fake_llm.py` (new).

- [ ] **28.2 — RED: scenario runner tests** (S)
  - Acceptance: 2 failing tests (scenario runs deterministically — same bytes twice, `--list` prints all scenarios).
  - Files: `tests/unit/test_demo_scenarios.py` (new).

- [ ] **28.3 — RED: Chainlit demo action test** (S)
  - Acceptance: 1 failing test (Run Demo action triggers scenario POST).
  - Files: `tests/unit/test_demo_button.py` (new).

- [ ] **28.4 — GREEN: FakeLLM + LLMFactory branch** (S)
  - Acceptance: 28.1 passes. `DEMO_MODE=true` → FakeLLM; otherwise unchanged.
  - Files: `src/demo/fake_llm.py` (new), `src/llm/factory.py` (edit), `src/config/settings.py` (edit — DEMO_MODE).

- [ ] **28.5 — GREEN: scenarios.yaml + fixtures** (M)
  - Acceptance: 7 scenarios defined (`lead-qualifier-acme`, `sdr-outreach-cto`, `support-triage-refund`, `meeting-prep-monday`, `content-pipeline-blog`, `cma-123-main`, `receptionist-book-table`). One fixture per agent per scenario in `src/demo/fixtures/<scenario>/<agent_role>.md`.
  - Files: `src/demo/scenarios.yaml` (new), `src/demo/fixtures/**` (new).

- [ ] **28.6 — GREEN: scripts/demo.py** (S)
  - Acceptance: 28.2 passes. `--scenario NAME`, `--list`, `--dry-run` flags; exits non-zero on missing fixture with the missing key named.
  - Files: `scripts/demo.py` (new).

- [ ] **28.7 — GREEN: Chainlit "Run demo" action** (S)
  - Acceptance: 28.3 passes. `cl.Action` lists scenarios from YAML; invocation sets `DEMO_MODE=true` for the API call.
  - Files: `src/chainlit_app.py` (edit).

- [ ] **28.8 — GREEN: Dashboard "Run Demo" button** (S)
  - Acceptance: Button on `/` when `NEXT_PUBLIC_DEMO_ENABLED=true`; runs via existing launcher code path with `demo_mode: true` flag.
  - Files: `dashboard/app/page.tsx` (edit), `dashboard/.env.example` (edit).

- [ ] **28.9 — REFACTOR + COMMIT** (S)

### Checkpoint 28 (and Phase 4 complete)
- [ ] `python scripts/demo.py --scenario lead-qualifier-acme` byte-identical on two consecutive runs.
- [ ] Dashboard "Run Demo" runs end-to-end deterministically.
- [ ] All v4 success criteria in SPEC.md § Phase 4 met.

---

## Phase 4 Risks & Mitigations

| Risk | Likelihood | Mitigation | Owner slice |
|------|-----------|------------|-------------|
| SSE buffering under docker-compose | Low | `X-Accel-Buffering: no`; test with curl -N from container | 19 |
| Next.js hydration double-mounts EventSource | Medium | Proper useEffect cleanup; StrictMode test locks it in | 20c |
| Registry migration breaks backward compat | Medium | Golden-output test on research_report (21.2) | 21 |
| Parallel tasks race on shared Qdrant singleton | Low | Slice-2 singleton is thread-safe; slice 22 regression test | 22 |
| TCPA violation during voice demo | Medium-High | `VOICE_ENABLED=false` default + verified-number whitelist + README TCPA banner | 26 |
| Twilio webhook spoofing | Medium | X-Twilio-Signature HMAC check (test 26.3) | 26 |
| Shareable link leaks raw tool I/O | Medium | Whitelisted fields only; test 27.3 asserts | 27 |
| WeasyPrint native deps on Apple Silicon | Low | brew install documented in README | 27 |
| Fixture drift / missing fixtures silently fall back to live LLM | Medium | FakeLLM raises loudly on miss (test 28.1) | 28 |
| Port 3061 collision with other portfolio project | Low | PORTS.md check task 20a.1 | 20a |
| Local Ollama (qwen3:8b) too slow for Twilio 5s webhook | Medium | Precompute next utterance; fallback TwiML redirects | 26 |

---

## Parallelization Opportunities

Mostly sequential (each slice unlocks the next), but within a slice:
- **Slice 20a**: tasks 20a.2 (scaffold) and 20a.3 (test configs) can run in parallel.
- **Slices 23-25**: business workflow packs could, in principle, be done by three parallel agents *after* slice 22 lands. For a solo developer this is overkill; noted for completeness.
- **Slice 28**: fixture authoring (28.5) for each scenario is independent.

For a solo developer, the recommended execution is **strictly sequential in the order listed above** (19 → 20a → 21 → 20b → 22 → 20c → 23 → 24 → 25 → 26 → 27 → 28).

---

## Phase 4 Success Criteria (mirrors SPEC.md)

- [ ] All 10 slices (19, 20a, 20b, 20c, 21, 22, 23, 24, 25, 26, 27, 28) committed on `main`, one commit each.
- [ ] 152 prior unit tests + ~75 new = ~227 green.
- [ ] `docker compose -f docker-compose.dev.yml up` boots 4 services healthy.
- [ ] Every workflow runs end-to-end via the dashboard under `DEMO_MODE=true`.
- [ ] Live team view shows real-time state for sequential, hierarchical, and parallel workflows.
- [ ] Share link + PDF export round-trip tested for at least one completed run.
- [ ] Voice slice unit tests green; opt-in live call verified once manually (optional).
- [ ] `docs/demos/{dashboard,sales,support,verticals,voice}.md` each contain a scripted 5-min pitch.

---

## Next Step — copy-paste to start slice 19

```
/build Slice 19 from PLAN.md — Agent State Bus + SSE endpoint.
Source: SPEC.md § "Slice 19 — Agent State Bus + live event endpoint", DEC-16, DEC-27 in DECISIONS.md.
Execute the TDD task list 19.1 → 19.7 in order. Use:
  - test-driven-development (RED before GREEN)
  - incremental-implementation (vertical, one commit at the end)
  - api-and-interface-design (SSE contract)
  - source-driven-development (verify FastAPI StreamingResponse + CrewAI step_callback signatures against current docs)
  - security-and-hardening (auth gating on the SSE route; no event data leakage on unknown task_id)
Run: uv run pytest tests/unit/test_agent_state_bus.py tests/unit/test_sse_endpoint.py (RED first), implement, then uv run pytest -m unit (full suite green) and uv run ruff check src/ tests/. Commit as feat(slice-19): agent state bus and SSE events endpoint. End your turn with the /build prompt for slice 20a.
```
