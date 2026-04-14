# Project File Map & Quick Navigation

## Source Code (`src/`)

| File/Directory | Purpose |
|---|---|
| `main.py` | FastAPI application; routes: `/health`, `/crew/run`, `/documents/ingest`, `/documents/search` |
| `crew.py` | Agent pipeline orchestration: `build_crew()`, `run_crew()` |
| `chainlit_app.py` | Chainlit chat UI with `/domain` command for context switching |
| `agents/factory.py` | AgentFactory: YAML → CrewAI Agent instantiation |
| `tasks/definitions.py` | TaskFactory: YAML → CrewAI Task instantiation |
| `llm/factory.py` | LLMFactory: Provider switching (Ollama/Anthropic/OpenAI) |
| `llm/embeddings.py` | EmbeddingFactory: FastEmbed/Ollama/OpenAI switching |
| `tools/registry.py` | `@register_tool` decorator, tool discovery mechanism |
| `tools/search.py` | WebSearchTool, DocumentSearchTool, DocumentIngestTool |
| `repositories/qdrant_repo.py` | QdrantRepository: vector DB abstraction layer |
| `config/settings.py` | Pydantic Settings (15 config vars) with environment loading |
| `models/schemas.py` | Pydantic request/response models |

## Configuration Files (`src/config/`)

| File | Purpose |
|---|---|
| `agents.yaml` | 4 agent definitions (Research, Analysis, Writing, QA) |
| `tasks.yaml` | 4 task definitions with role/goal/description |
| `domains/healthcare.yaml` | Healthcare industry prompt overrides |
| `domains/finance.yaml` | Finance industry prompt overrides |
| `domains/real_estate.yaml` | Real Estate industry prompt overrides |

## Tests (`tests/`)

| Directory | Purpose |
|---|---|
| `unit/` | Fast tests with mocked LLMs (< 10 seconds) |
| `integration/` | Tests requiring Ollama + Qdrant running |

## Docker & Deployment

| File | Purpose |
|---|---|
| `docker-compose.dev.yml` | Local development stack (Qdrant only) |
| `docker-compose.prod.yml` | Production stack with Traefik reverse proxy |
| `Dockerfile` | Container image for FastAPI + Chainlit |

## Project Documentation

| File | Purpose |
|---|---|
| `PLAN.md` | Project scope, timelines, deliverables (~11 hours estimated) |
| `AGENTS.md` | 7 specialist roles (Architect, Test Engineer, DevOps, Security, DBA, Code Reviewer, UI/UX Designer) |
| `README.md` | Quick start guide, API examples, industry domains, testing |
| `PORT-MAP.md` | Global port allocation across all 12 projects |
| `CLAUDE.md` | Git rules, tech stack, development setup, session state |

## Build & Dependencies

| File | Purpose |
|---|---|
| `pyproject.toml` | Dependencies, build config, script entry points |
| `.env.example` | Template environment variables |

## Reference Documentation (`.claude/`)

| File | Purpose |
|---|---|
| `project-state.md` | Architecture summary, 4-agent pipeline, environment config |
| `scratchpad.md` | Session notes, current status, known issues, resume instructions |
| `fixes-applied.md` | Fixes applied (pyproject.toml invalid scripts) |
| `architecture-patterns.md` | Design patterns, architectural decisions, why this design |
| `configuration-reference.md` | All config variables, ports, database settings |
| `development-commands.md` | Complete command reference for development, testing, API calls |
| `file-map.md` | This file - project structure and navigation |
