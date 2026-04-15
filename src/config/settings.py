from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


class EmbeddingMode(str, Enum):
    LOCAL = "local"
    API = "api"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: LLMProvider = LLMProvider.OLLAMA

    # Ollama (local)
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"

    # Anthropic (cloud)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-6"

    # Embeddings
    embedding_mode: EmbeddingMode = EmbeddingMode.LOCAL
    openai_api_key: Optional[str] = None

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    # Security
    api_key: Optional[str] = None
    cors_origins: list[str] = ["*"]

    # Application
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    app_port: int = 8000
    chainlit_port: int = 8001

    # Persistence
    sqlite_db_path: str = "data/results.db"

    model_config = {
        "env_file": (".env", ".env.local"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
