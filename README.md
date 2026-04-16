# AI Agent System

Multi-agent system built with **CrewAI**, **Chainlit**, **Qdrant**, and **FastAPI**. Supports local development with **Ollama** on Apple Silicon and cloud deployment with **Anthropic Claude API**.

**Live:** [agents.305-ai.com](https://agents.305-ai.com)

## Architecture

```
Chainlit UI / FastAPI
        |
    CrewAI Crew
    ├── Research Agent  (web search + RAG)
    ├── Analysis Agent  (document search)
    ├── Writing Agent   (content generation)
    └── Validation Agent (quality review)
        |
    Tools & RAG
    ├── DuckDuckGo Search
    ├── Qdrant Vector DB (semantic search)
    └── Document Ingestion
        |
    LLM Provider (switchable)
    ├── Ollama (local, Apple Silicon Metal GPU)
    └── Anthropic Claude (cloud)
```

## Quick Start (Local Development)

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.12+
- Docker Desktop
- Ollama (`brew install ollama`)

### Setup

```bash
# 1. Clone and install
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env.local

# 3. Start infrastructure (Qdrant)
./scripts/dev.sh

# 4. Pull Ollama models
./scripts/pull-models.sh

# 5. Run the API
uvicorn src.main:app --reload --port 8060

# 6. Or run the chat UI
chainlit run src/chainlit_app.py --port 3060

# 7. Or run the live team dashboard (Next.js 14+, slice-20a)
cd dashboard
npm install
npm run dev           # http://localhost:3000 (in Docker: http://localhost:3061)
```

### Dashboard (Next.js 14+)

The team-view dashboard is a separate app under `dashboard/` with its own `package.json`, Dockerfile, and test pipeline.

```bash
cd dashboard
npm install
npm run dev           # dev server on port 3000 (Docker host: http://localhost:3061)
npm run build         # production standalone build
npm test              # Vitest unit tests
npm run test:e2e      # Playwright E2E (auto-starts the dev server)
```

Via Docker Compose the dashboard runs as the `dashboard` service alongside Qdrant, the API, and Chainlit:

```bash
docker compose -f docker-compose.dev.yml up -d
# Visit http://localhost:3061
```

### Switch to Cloud (Anthropic)

Edit `.env.local`:
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with config info |
| POST | `/crew/run` | Execute agent crew on a topic |
| POST | `/documents/ingest` | Add document to RAG knowledge base |
| POST | `/documents/search` | Search RAG knowledge base |

### Example

```bash
# Run crew
curl -X POST http://localhost:8060/crew/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in healthcare", "domain": "healthcare"}'

# Ingest document
curl -X POST http://localhost:8060/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "doc-1", "content": "Your document content here"}'
```

## Industry Domains

Switch agent behavior by domain:

- **general** (default) — General-purpose research and analysis
- **healthcare** — Medical terminology, HIPAA, clinical research
- **finance** — Investment analysis, SEC compliance, market trends
- **real_estate** — Property valuation, market analysis, CMA

In the API: `{"domain": "healthcare"}` in the request body.
In Chainlit: `/domain healthcare` command.

## Testing

```bash
# Unit tests (fast, mocked)
pytest -m unit

# Integration tests
pytest -m integration

# All tests
pytest

# With coverage
pytest --cov=src
```

## Project Structure

```
src/
  config/          # Settings + YAML agent/task definitions
    domains/       # Industry-specific overrides
  llm/             # LLM & embedding provider factories
  agents/          # Agent factory (YAML -> CrewAI Agent)
  tasks/           # Task factory (YAML -> CrewAI Task)
  tools/           # Tool registry + custom tools (search, RAG)
  repositories/    # Document storage abstraction (Qdrant)
  models/          # Pydantic request/response schemas
  utils/           # Logging utilities
  main.py          # FastAPI application
  chainlit_app.py  # Chainlit chat interface
  crew.py          # Crew assembly and execution
```

## Deployment

```bash
# Production with Docker
docker compose -f docker-compose.prod.yml up -d
```

Deploys behind Traefik reverse proxy with automatic HTTPS via Let's Encrypt.
