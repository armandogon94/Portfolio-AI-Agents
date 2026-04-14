# Configuration Reference

## Environment Variables (.env or .env.local)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` (local) or `anthropic` (cloud) |
| `OLLAMA_MODEL` | `qwen3:8b` | Model name (user's current RAM-constrained choice) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `ANTHROPIC_API_KEY` | (required) | Only if using anthropic provider |
| `EMBEDDING_MODE` | `local` | `local` (FastEmbed) or `api` (OpenAI) |
| `QDRANT_HOST` | `localhost` | Vector DB host |
| `QDRANT_PORT` | `6333` | Vector DB HTTP port |
| `QDRANT_COLLECTION` | `documents` | Vector collection name |
| `API_PORT` | `8060` | FastAPI server port |
| `CHATLIT_PORT` | `3060` | Chainlit UI port |

## Ports in Use

| Port | Service | Purpose |
|------|---------|---------|
| 3060 | Chainlit UI | Frontend chat interface |
| 8060 | FastAPI | Backend API, agent execution |
| 6333 | Qdrant HTTP | Vector database |
| 6334 | Qdrant gRPC | Vector database protocol |
| 11434 | Ollama | Local LLM server (macOS) |

**Global context:** See PORT-MAP.md for all 12 projects' port allocations.

## Database Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| PostgreSQL DB | `agents_db` | Shared VPS database |
| Redis Cache | DB 6 | Shared Redis instance |

## Project Infrastructure

- **Location:** `/mnt/Deep Research Claude Code/06-Portfolio-AI-Agents`
- **Development Stack:** Docker Compose (Qdrant only)
- **Production Stack:** Docker Compose with Traefik reverse proxy
- **Deployment URL:** `agents.305-ai.com`

## Configuration Files

- `src/config/settings.py` — Pydantic Settings (15 config vars), loaded from environment
- `src/config/agents.yaml` — 4 agent definitions (Research, Analysis, Writing, QA)
- `src/config/tasks.yaml` — 4 task definitions
- `src/config/domains/` — Domain-specific config overrides:
  - `healthcare.yaml`
  - `finance.yaml`
  - `real_estate.yaml`

## Quick Start Configuration

```bash
# Copy example config
cp .env.example .env.local

# Modify as needed
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=qwen3:8b
export QDRANT_HOST=localhost
```
