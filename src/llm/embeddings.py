import logging
from typing import Protocol, runtime_checkable
from src.config.settings import settings, EmbeddingMode

logger = logging.getLogger(__name__)


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding providers."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FastEmbedEmbedder:
    """Local embeddings using FastEmbed (ONNX, CPU-only, ~100MB)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name)
        self.dimension = 384  # bge-small-en-v1.5 dimension
        logger.info(f"FastEmbed initialized: {model_name}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(e) for e in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


class OllamaEmbedder:
    """Local embeddings using Ollama nomic-embed-text."""

    def __init__(self):
        from langchain_ollama import OllamaEmbeddings

        self.model = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=settings.ollama_base_url,
        )
        self.dimension = 768
        logger.info("Ollama embeddings initialized: nomic-embed-text")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


class OpenAIEmbedder:
    """API embeddings using OpenAI text-embedding-3-small."""

    def __init__(self):
        from langchain_openai import OpenAIEmbeddings

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required when EMBEDDING_MODE=api")
        self.model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )
        self.dimension = 1536
        logger.info("OpenAI embeddings initialized: text-embedding-3-small")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


class EmbeddingFactory:
    """Creates embedding instances based on configuration."""

    @staticmethod
    def create() -> FastEmbedEmbedder | OllamaEmbedder | OpenAIEmbedder:
        mode = settings.embedding_mode

        if mode == EmbeddingMode.LOCAL:
            try:
                return FastEmbedEmbedder()
            except ImportError:
                logger.warning("FastEmbed not available, falling back to Ollama embeddings")
                return OllamaEmbedder()
        elif mode == EmbeddingMode.API:
            return OpenAIEmbedder()
        else:
            raise ValueError(f"Unknown embedding mode: {mode}")
