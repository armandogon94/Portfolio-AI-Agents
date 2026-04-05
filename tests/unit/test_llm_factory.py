import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestLLMFactory:
    def test_create_ollama(self):
        """LLMFactory creates Ollama LLM when provider is ollama."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "mistral"}):
            # Re-import to pick up new env
            from importlib import reload
            import src.config.settings

            reload(src.config.settings)

            with patch("src.llm.factory.LLM") as MockLLM:
                from importlib import reload as reload2
                import src.llm.factory

                reload2(src.llm.factory)
                from src.llm.factory import LLMFactory

                LLMFactory.create()
                MockLLM.assert_called_once()
                call_kwargs = MockLLM.call_args
                assert "ollama/" in call_kwargs.kwargs.get("model", call_kwargs.args[0] if call_kwargs.args else "")

    def test_create_anthropic_requires_key(self):
        """LLMFactory raises error when Anthropic key is missing."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""},
            clear=False,
        ):
            from importlib import reload
            import src.config.settings

            reload(src.config.settings)

            from importlib import reload as reload2
            import src.llm.factory

            reload2(src.llm.factory)
            from src.llm.factory import LLMFactory

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                LLMFactory.create()


@pytest.mark.unit
class TestEmbeddingFactory:
    def test_create_local_returns_embedder(self):
        """EmbeddingFactory creates a local embedder."""
        with patch.dict(os.environ, {"EMBEDDING_MODE": "local"}):
            from importlib import reload
            import src.config.settings

            reload(src.config.settings)

            with patch("src.llm.embeddings.FastEmbedEmbedder") as MockEmbed:
                mock_instance = MagicMock()
                mock_instance.dimension = 384
                MockEmbed.return_value = mock_instance

                from importlib import reload as reload2
                import src.llm.embeddings

                reload2(src.llm.embeddings)
                from src.llm.embeddings import EmbeddingFactory

                embedder = EmbeddingFactory.create()
                assert embedder is not None
