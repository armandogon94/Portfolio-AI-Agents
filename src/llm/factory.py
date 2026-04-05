import logging
from crewai import LLM
from src.config.settings import settings, LLMProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Creates LLM instances based on the configured provider."""

    @staticmethod
    def create(temperature: float = 0.7, max_tokens: int = 2048) -> LLM:
        provider = settings.llm_provider

        if provider == LLMProvider.OLLAMA:
            return LLMFactory._create_ollama(temperature, max_tokens)
        elif provider == LLMProvider.ANTHROPIC:
            return LLMFactory._create_anthropic(temperature, max_tokens)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @staticmethod
    def _create_ollama(temperature: float, max_tokens: int) -> LLM:
        model = settings.ollama_model
        base_url = settings.ollama_base_url
        logger.info(f"Creating Ollama LLM: {model} at {base_url}")
        return LLM(
            model=f"ollama/{model}",
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @staticmethod
    def _create_anthropic(temperature: float, max_tokens: int) -> LLM:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        model = settings.anthropic_model
        logger.info(f"Creating Anthropic LLM: {model}")
        return LLM(
            model=f"anthropic/{model}",
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
