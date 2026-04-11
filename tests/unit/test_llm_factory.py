import pytest
from unittest.mock import patch, MagicMock

from src.config.settings import LLMProvider, EmbeddingMode


@pytest.mark.unit
class TestLLMFactory:
    def test_create_ollama(self):
        """LLMFactory creates Ollama LLM when provider is ollama."""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.OLLAMA
        mock_settings.ollama_model = "mistral"
        mock_settings.ollama_base_url = "http://localhost:11434"

        with patch("src.llm.factory.settings", mock_settings):
            with patch("src.llm.factory.LLM") as MockLLM:
                from src.llm.factory import LLMFactory

                LLMFactory.create()
                MockLLM.assert_called_once()
                call_kwargs = MockLLM.call_args.kwargs
                assert "ollama/mistral" == call_kwargs.get("model", "")

    def test_create_anthropic_requires_key(self):
        """LLMFactory raises error when Anthropic key is missing."""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.ANTHROPIC
        mock_settings.anthropic_api_key = None

        with patch("src.llm.factory.settings", mock_settings):
            from src.llm.factory import LLMFactory

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                LLMFactory.create()


@pytest.mark.unit
class TestEmbeddingFactory:
    def test_create_local_returns_embedder(self):
        """EmbeddingFactory creates a local embedder."""
        mock_settings = MagicMock()
        mock_settings.embedding_mode = EmbeddingMode.LOCAL

        mock_instance = MagicMock()
        mock_instance.dimension = 384

        with patch("src.llm.embeddings.settings", mock_settings):
            with patch("src.llm.embeddings.FastEmbedEmbedder", return_value=mock_instance):
                from src.llm.embeddings import EmbeddingFactory

                embedder = EmbeddingFactory.create()
                assert embedder is not None
                assert embedder.dimension == 384
