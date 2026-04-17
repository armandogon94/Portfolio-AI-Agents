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
    # Dashboard origin for CORS allow-list (slice-20b, DEC-26b). In dev this
    # is always appended to cors_origins. In prod it's only appended when
    # cors_origins is not "*".
    dashboard_origin: str = "http://localhost:3061"

    # Application
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    app_port: int = 8000
    chainlit_port: int = 8001

    # Persistence
    sqlite_db_path: str = "data/results.db"

    # Share links (slice-27, DEC-24). Auto-generated in dev with a WARN;
    # required in production (lifespan check emits a warning if missing).
    share_secret: Optional[str] = None

    # Voice (slice-26, DEC-21, DEC-22) — disabled by default. Only turn on
    # for deliberate demos; TCPA applies to every outbound call.
    voice_enabled: bool = False
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    twilio_webhook_base: str = "http://localhost:8060"
    # Whitelist — the tool refuses to dial numbers that aren't here.
    twilio_verified_to_numbers: list[str] = []

    model_config = {
        "env_file": (".env", ".env.local"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
