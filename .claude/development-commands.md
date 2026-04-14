# Development Commands Reference

## Infrastructure & Setup

```bash
# Start local development infrastructure (Qdrant)
docker compose -f docker-compose.dev.yml up -d

# Pull Ollama models
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull nomic-embed-text
ollama pull qwen3:8b

# Install Python dependencies
pip install -e ".[dev]"

# Verify Qdrant is healthy
curl http://localhost:6333/healthz
```

## Running Servers

```bash
# FastAPI backend (with auto-reload)
# Use full Python path on macOS with conda
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m uvicorn src.main:app \
  --host 0.0.0.0 --port 8060 --reload

# Alternative (if python3 is aliased correctly)
python -m uvicorn src.main:app --reload --port 8060

# Chainlit chat UI
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m chainlit run \
  src/chainlit_app.py --port 3060

# Check health
curl http://localhost:8060/health
```

## Testing

```bash
# Unit tests (fast, mocked LLMs)
pytest -m unit

# Integration tests (requires Ollama + Qdrant)
pytest -m integration

# All tests
pytest

# With coverage
pytest --cov=src
```

## API Testing (curl examples)

```bash
# Health check
curl http://localhost:8060/health

# Run crew with default settings
curl -X POST http://localhost:8060/crew/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "your test topic"}'

# Run crew with domain specialization
curl -X POST http://localhost:8060/crew/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in healthcare", "domain": "healthcare"}'

# Ingest documents
curl -X POST http://localhost:8060/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"documents": ["doc1.pdf", "doc2.txt"]}'

# Search documents
curl -X POST http://localhost:8060/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning applications"}'
```

## Docker Management

```bash
# View logs
docker logs qdrant-dev
docker logs -f qdrant-dev  # Follow mode

# Stop all containers
docker compose down

# Production stack
docker compose -f docker-compose.prod.yml up -d
```

## Project Navigation & Development

```bash
# Navigate to project
cd /Users/armandogonzalez/Documents/Claude/Deep\ Research\ Claude\ Code/06-Portfolio-AI-Agents

# List Ollama models
ollama list

# Python version check (use conda, not system)
which python3
/opt/homebrew/Caskroom/miniconda/base/bin/python3 --version

# Reinstall with dev dependencies
pip install -e ".[dev]"
```

## How to Resume Work (Full Startup Sequence)

```bash
# 1. Navigate to project
cd /Users/armandogonzalez/Documents/Claude/Deep\ Research\ Claude\ Code/06-Portfolio-AI-Agents

# 2. Start Qdrant (if not running)
docker compose -f docker-compose.dev.yml up -d

# 3. Verify Qdrant health
curl http://localhost:6333/healthz

# 4. Verify Ollama has qwen3:8b
ollama list

# 5. Start FastAPI server (use full Python path)
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m uvicorn src.main:app \
  --host 0.0.0.0 --port 8060 --reload

# 6. (Optional) Start Chainlit UI in another terminal
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m chainlit run \
  src/chainlit_app.py --port 3060

# 7. Test health endpoint
curl http://localhost:8060/health

# 8. Test crew execution
curl -X POST http://localhost:8060/crew/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "your test topic"}'
```
