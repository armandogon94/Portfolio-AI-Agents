# Architecture Patterns & Design Decisions

## Design Patterns in Use

### Factory Pattern (LLMFactory, EmbeddingFactory, AgentFactory, TaskFactory)
- Allows seamless switching between Ollama (local) ↔ Anthropic (cloud) without code changes
- Centralizes provider instantiation logic
- Easy to add new providers (e.g., OpenAI, Cohere)

### Strategy Pattern
- Swappable LLM strategies (Ollama, Anthropic, OpenAI)
- Swappable embedding strategies (FastEmbed, Ollama, OpenAI)

### Repository Pattern
- Abstract document storage (Qdrant/ChromaDB)
- Isolates database implementation details
- Easy to swap vector DB backend

### Registry Pattern
- `@register_tool` decorator for centralized tool management
- Discoverable tools without hardcoding imports
- Self-registering tool ecosystem

### YAML Configuration Pattern
- Agent and task definitions externalized from code
- Domain-specific config overrides (healthcare, finance, real_estate)
- Configuration-driven agent specialization

## Why This Architecture

### 4-Agent Sequential Pipeline (Research → Analysis → Writing → QA)
- Clear separation of concerns
- Each agent validates before passing to next
- Reduces hallucinations through validation gates

### FastAPI over Django
- Lightweight, async-native
- Perfect for streaming agent outputs
- Lower overhead for microservice-style deployments

### Qdrant over Pinecone/Weaviate
- Self-hosted, runs on ARM64 (Pi/Mac)
- No vendor lock-in
- Cost-effective at scale

### YAML + Python Hybrid
- Non-engineers can modify agent prompts via YAML
- Code handles orchestration logic
- Best of both worlds: flexibility + maintainability
