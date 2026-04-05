# Project State — AI Agent System

## Architecture Summary

### 4-Agent Pipeline (Sequential)
1. **Research Analyst** — web search (DuckDuckGo) + RAG document retrieval
2. **Data Analyst** — extracts patterns and key insights
3. **Content Writer** — generates professional report with recommendations
4. **Quality Assurance Reviewer** — validates accuracy, completeness, scoring

### Key Design Patterns
- **Factory Pattern**: `LLMFactory` (src/llm/factory.py) — switches Ollama/Anthropic via env var
- **Factory Pattern**: `EmbeddingFactory` (src/llm/embeddings.py) — FastEmbed/Ollama/OpenAI
- **Factory Pattern**: `AgentFactory` (src/agents/factory.py) — creates agents from YAML config
- **Factory Pattern**: `TaskFactory` (src/tasks/definitions.py) — creates tasks from YAML
- **Repository Pattern**: `QdrantRepository` (src/repositories/qdrant_repo.py) — vector DB abstraction
- **Registry Pattern**: `ToolRegistry` (src/tools/registry.py) — @register_tool decorator
- **YAML Config**: Agent/task definitions in YAML, domain overrides in config/domains/

### File Map
```
src/
├── main.py                    # FastAPI app: /health, /crew/run, /documents/ingest, /documents/search
├── crew.py                    # build_crew() and run_crew() orchestration
├── chainlit_app.py            # Chainlit chat UI with /domain command
├── agents/factory.py          # AgentFactory: YAML → CrewAI Agent instances
├── tasks/definitions.py       # TaskFactory: YAML → CrewAI Task instances
├── tools/
│   ├── registry.py            # ToolRegistry with @register_tool decorator
│   └── search.py              # WebSearchTool, DocumentSearchTool, DocumentIngestTool
├── llm/
│   ├── factory.py             # LLMFactory: ollama/anthropic switching
│   └── embeddings.py          # FastEmbed, Ollama, OpenAI embedders
├── models/schemas.py          # Pydantic request/response models (6 schemas)
├── repositories/
│   ├── base.py                # Abstract DocumentRepository + Document dataclass
│   └── qdrant_repo.py         # QdrantRepository: add/search/delete
├── config/
│   ├── settings.py            # Pydantic Settings (15 config vars)
│   ├── agents.yaml            # 4 agent definitions
│   ├── tasks.yaml             # 4 task definitions
│   └── domains/               # healthcare.yaml, finance.yaml, real_estate.yaml
└── utils/logger.py            # Structured logging setup
```

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check with provider/mode info |
| POST | /crew/run | Execute agent pipeline `{"topic": "...", "domain": "healthcare"}` |
| POST | /documents/ingest | Add document to Qdrant `{"doc_id": "...", "content": "..."}` |
| POST | /documents/search | Semantic search `{"query": "...", "limit": 5}` |

### Ports
| Service | Port | Notes |
|---------|------|-------|
| FastAPI | 8060 | Configured in .env |
| Chainlit | 3060 | Configured in .env |
| Qdrant HTTP | 6333 | Docker, bound to 127.0.0.1 |
| Qdrant gRPC | 6334 | Docker, bound to 127.0.0.1 |
| Ollama | 11434 | Native macOS |

### Environment Configuration (.env)
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b          # User's RAM constraint
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODE=local            # FastEmbed, no API key needed
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Python Environment
- Using conda base Python 3.13 at `/opt/homebrew/Caskroom/miniconda/base/bin/python3`
- System `python3` is 3.14 — DO NOT use it (packages not installed there)
- No dedicated venv yet
