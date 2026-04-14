# Known Issues & Gotchas

## Active Issues (2026-04-01)

### 1. Python Version Mismatch
- `python3` command resolves to system Python 3.14 (no packages installed)
- Use full conda Python path: `/opt/homebrew/Caskroom/miniconda/base/bin/python3` (conda 3.13)
- All scripts and development work must use the full path or create an alias

**Workaround:**
```bash
alias python=/opt/homebrew/Caskroom/miniconda/base/bin/python3
```

### 2. CrewAI Deprecation Warning
- Non-blocking warnings about `agent.multimodal` in `crewai/crew.py:1312-1313`
- Does not affect functionality
- Can be suppressed if needed

### 3. CORS Wide Open
- `src/main.py` allows all origins (`*`) — OK for local dev
- **MUST be restricted for production** to `agents.305-ai.com`
- Update CORS middleware before cloud deployment

### 4. No Authentication
- API endpoints lack JWT or bearer token authentication
- Fine for local development
- **MUST implement authentication before production deployment**
- Candidates: JWT with RS256, OAuth2 with password flow, API key rotation

## Apple Silicon Notes

- All stack components run natively on ARM64 (M1/M2/M3/M4)
- **Qdrant:** Use `qdrant/qdrant:latest` (ARM64 images available, ~10% slower but consistent)
- **Ollama:** Native Metal GPU acceleration (automatic, no config needed)
- **sentence-transformers:** Set `PYTORCH_ENABLE_MPS_FALLBACK=1` if MPS errors occur
- **FastEmbed:** Preferred over sentence-transformers for lighter memory footprint
- **RAM Requirements:**
  - 16GB RAM: llama3.1:8b works well (qwen3:8b tested)
  - 32GB RAM: can run 13B models

## Not Yet Done (As of 2026-04-01)

- [ ] Create a dedicated Python venv (currently using conda base Python 3.13)
- [ ] Run the full test suite (`pytest -m unit` or `-m integration`)
- [ ] Test Chainlit chat UI (`chainlit run src/chainlit_app.py --port 3060`)
- [ ] Test RAG document ingestion/search pipeline
- [ ] Test domain-specific configs (healthcare, finance, real_estate)
- [ ] Deploy to production (agents.305-ai.com)
- [ ] Add authentication to API endpoints
- [ ] Restrict CORS origins for production
- [ ] Set up CI/CD pipeline
- [ ] Performance tuning & load testing

## Environment Setup Tips

### Docker Issues
- If Qdrant won't start: check Docker daemon is running (`docker ps`)
- If port 6333 is in use: `lsof -i :6333` to find process, then kill or change port
- Qdrant ARM64 images are slower (~10%) but stable

### Ollama Issues
- Models must be pulled explicitly: `ollama pull qwen3:8b`
- Model switching works at runtime (no restart needed)
- Ensure Ollama service is running: `ps aux | grep ollama`

### FastAPI Issues
- Always use `--reload` for development (auto-restarts on code changes)
- Port 8060 must be available (check with `lsof -i :8060`)
- Health endpoint should return `{"status": "ok"}` with 200 status

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused (port 6333)` | Qdrant not running | `docker compose -f docker-compose.dev.yml up -d` |
| `ModuleNotFoundError: No module named 'src'` | Wrong Python or missing install | `pip install -e ".[dev]"` with correct Python |
| `PYTORCH_ENABLE_MPS_FALLBACK=1` warnings | sentence-transformers on Apple Silicon | Set env var or use FastEmbed instead |
| `CrewAI deprecated multimodal` | Non-blocking deprecation warning | Can be ignored or suppressed |
