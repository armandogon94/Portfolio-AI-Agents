# AI Agent System — Session Scratchpad

## Last Session: 2026-04-01

### What Was Done

1. **Full project analysis** — explored entire src/ tree, tests, configs, Docker setup. Confirmed this is fully implemented production code (not scaffolding).

2. **Fixed `pyproject.toml`** — removed invalid `[project.scripts]` entries that used shell command syntax instead of Python callable format. The entries `start`, `dev`, `chat` were causing `pip install -e .` to fail with "Invalid script entry point" error. Replaced with comments showing how to run the commands directly.

3. **Created `.env`** — configured for local Ollama with `qwen3:8b` model (user's RAM constraint prevents larger models).

4. **Started Qdrant** — pulled and started via `docker compose -f docker-compose.dev.yml up -d`. Container name: `qdrant-dev`, ports 6333/6334.

5. **Installed dependencies** — `pip install -e ".[dev]"` into conda base Python 3.13. All deps resolved successfully after the pyproject.toml fix.

6. **Started FastAPI server** — running on port 8060 with reload.

7. **Successfully tested crew execution** — sent a test query through all 4 agents (Research → Analysis → Writing → QA). Got a 3,860-char report back with status "completed". The full pipeline works end-to-end with qwen3:8b.

---

### Current State

- **Server**: Was running at `http://localhost:8060` (will need restart in new session)
- **Qdrant**: Was running via Docker (may still be running, check with `docker ps`)
- **Ollama**: Running with `qwen3:8b` model
- **Chat UI**: Not started yet (Chainlit)
- **Tests**: Not run yet
- **No venv**: Project installed into conda base Python 3.13 (no dedicated venv created)

---

### Known Issues

1. **Python version mismatch**: `python3` resolves to Python 3.14 (system), but `pip` installs to conda Python 3.13. Must use `/opt/homebrew/Caskroom/miniconda/base/bin/python3` explicitly, or activate conda.

2. **CrewAI deprecation warnings**: During crew execution, got `DeprecationWarning: deprecated` from `crewai/crew.py:1312-1313` related to `agent.multimodal`. Non-blocking.

3. **CORS wide open**: `src/main.py` allows all origins (`*`). Should restrict for production.

4. **No auth**: API endpoints have no authentication. Fine for local dev, needs JWT or similar for prod.

---

### How to Resume

```bash
cd /Users/armandogonzalez/Documents/Claude/Deep\ Research\ Claude\ Code/06-Portfolio-AI-Agents

# 1. Start Qdrant (if not still running)
docker compose -f docker-compose.dev.yml up -d

# 2. Verify Qdrant health
curl http://localhost:6333/healthz

# 3. Make sure Ollama has qwen3:8b
ollama list

# 4. Start the API server
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8060 --reload

# 5. (Optional) Start Chainlit chat UI
/opt/homebrew/Caskroom/miniconda/base/bin/python3 -m chainlit run src/chainlit_app.py --port 3060

# 6. Test
curl http://localhost:8060/health
curl -X POST http://localhost:8060/crew/run -H "Content-Type: application/json" -d '{"topic": "your topic"}'
```

---

### What Hasn't Been Done Yet

- [ ] Create a dedicated Python venv for this project (currently using conda base)
- [ ] Run the test suite (`pytest -m unit`)
- [ ] Test the Chainlit chat UI
- [ ] Test RAG document ingestion/search pipeline
- [ ] Test domain-specific configs (healthcare, finance, real_estate)
- [ ] Deploy to production (agents.305-ai.com)
- [ ] Add authentication to API endpoints
- [ ] Restrict CORS origins for production
- [ ] Initialize git repository
