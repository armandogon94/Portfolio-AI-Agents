# AI Agent System - CrewAI Multi-Agent Framework

> **Port allocation:** See [PORTS.md](PORTS.md) before changing any docker-compose ports. All ports outside the assigned ranges are taken by other projects.

## Project Overview
Production-ready multi-agent system with CrewAI, Chainlit UI, Qdrant vector DB, and RAG.
Deploys to `agents.305-ai.com`. Supports local development with Ollama and cloud deployment with Anthropic API.

## Tech Stack
- **Agent Framework:** CrewAI 0.30+ (with LiteLLM for multi-provider support)
- **Chat UI:** Chainlit 1.0+
- **Vector DB:** Qdrant 2.7+ (ARM64 Docker images available)
- **LLM (Local):** Ollama with llama3.1:8b or mistral:7b
- **LLM (Cloud):** Anthropic Claude via API
- **Embeddings (Local):** FastEmbed (BAAI/bge-small-en-v1.5) or Ollama nomic-embed-text
- **Embeddings (Cloud):** OpenAI text-embedding-3-small
- **Backend:** FastAPI 0.104+
- **Search Tool:** DuckDuckGo (langchain_community)
- **Python:** 3.12+ (native Apple Silicon support)

## Development Setup

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.12+ via pyenv
- Docker Desktop (for Qdrant)
- Ollama installed (`brew install ollama`)

### Quick Start
```bash
# Start infrastructure
docker compose -f docker-compose.dev.yml up -d

# Pull Ollama models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Install Python deps (always use uv, never conda/pip)
uv sync --extra dev

# Run locally
cp .env.example .env.local
python -m src.main
```

### Environment Variables
- `LLM_PROVIDER`: `ollama` (local) or `anthropic` (cloud)
- `OLLAMA_MODEL`: Model name (default: `llama3.1:8b`)
- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)
- `ANTHROPIC_API_KEY`: Required for cloud deployment
- `EMBEDDING_MODE`: `local` or `api`
- `QDRANT_HOST`: Vector DB host (default: `localhost`)
- `QDRANT_PORT`: Vector DB port (default: `6333`)

## Architecture Patterns
- **Factory Pattern:** LLMFactory for provider switching (Ollama/Anthropic/OpenAI)
- **Strategy Pattern:** Swappable LLM and embedding strategies
- **Repository Pattern:** Abstract document storage (Qdrant/ChromaDB)
- **Registry Pattern:** Centralized tool management
- **YAML Config:** Agent and task definitions in YAML, orchestration in Python

## Project Structure
```
src/
  agents/          # Agent definitions and factories
  tasks/           # Task definitions
  tools/           # Custom tools (RAG, search, etc.)
  config/          # YAML configs for agents/tasks + domain configs
    domains/       # Industry-specific configs (healthcare, finance, etc.)
  llm/             # LLM provider abstraction (factory + strategies)
  repositories/    # Document storage abstraction
  models/          # Pydantic schemas
  utils/           # Logging, helpers
tests/
  unit/            # Fast tests with mocked LLMs
  integration/     # Tests requiring local Ollama + Qdrant
```

## Commands
- `pytest -m unit` - Run unit tests (fast, mocked)
- `pytest -m integration` - Run integration tests (requires Ollama + Qdrant)
- `docker compose -f docker-compose.dev.yml up -d` - Start local infrastructure
- `docker compose -f docker-compose.prod.yml up -d` - Start production stack

## Apple Silicon Notes
- All stack components run natively on ARM64
- Qdrant: Use `qdrant/qdrant:latest` (ARM64 images available, ~10% slower but consistent)
- Ollama: Native Metal GPU acceleration (automatic, no config needed)
- sentence-transformers: Set `PYTORCH_ENABLE_MPS_FALLBACK=1` if MPS errors occur
- FastEmbed preferred over sentence-transformers for lighter footprint
- 16GB RAM: llama3.1:8b works well; 32GB: can run 13B models
