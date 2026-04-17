"""FakeLLM unit tests (slice-28, DEC-25)."""

from pathlib import Path

import pytest


def _make_fixtures(tmp_path: Path) -> Path:
    scenario = tmp_path / "lead-qualifier-acme"
    scenario.mkdir()
    (scenario / "1-researcher.md").write_text("Research notes for Acme.")
    (scenario / "2-scorer.md").write_text('{"score": 82, "notes": "strong fit"}')
    (scenario / "3-report_writer.md").write_text("# Acme brief\n\nBuy now.")
    return scenario


@pytest.mark.unit
class TestFakeLLM:
    def test_cycles_fixtures_in_order(self, tmp_path):
        from src.demo.fake_llm import FakeLLM

        scenario_dir = _make_fixtures(tmp_path)
        llm = FakeLLM(scenario="lead-qualifier-acme", fixtures_dir=scenario_dir)

        assert llm.call("prompt 1") == "Research notes for Acme."
        assert llm.call("prompt 2") == '{"score": 82, "notes": "strong fit"}'
        assert llm.call("prompt 3") == "# Acme brief\n\nBuy now."

    def test_missing_fixture_raises_loudly(self, tmp_path):
        from src.demo.fake_llm import FakeLLM

        scenario_dir = _make_fixtures(tmp_path)
        llm = FakeLLM(scenario="lead-qualifier-acme", fixtures_dir=scenario_dir)

        for _ in range(3):
            llm.call("ok")
        with pytest.raises(RuntimeError, match="exhausted"):
            llm.call("one too many")

    def test_deterministic_output_across_runs(self, tmp_path):
        from src.demo.fake_llm import FakeLLM

        scenario_dir = _make_fixtures(tmp_path)
        a = FakeLLM(scenario="lead-qualifier-acme", fixtures_dir=scenario_dir)
        b = FakeLLM(scenario="lead-qualifier-acme", fixtures_dir=scenario_dir)

        assert [a.call(str(i)) for i in range(3)] == [
            b.call(str(i)) for i in range(3)
        ]

    def test_factory_returns_fake_llm_when_demo_mode_on(self):
        from unittest.mock import patch

        from src.llm.factory import LLMFactory

        with patch("src.llm.factory.settings") as s:
            s.demo_mode = True
            s.demo_scenario = "lead-qualifier-acme"
            s.llm_provider.value = "ollama"
            # Use a fixture dir that exists in the repo — scenarios.yaml demo.
            llm = LLMFactory.create()

        from src.demo.fake_llm import FakeLLM

        assert isinstance(llm, FakeLLM)

    def test_factory_uses_live_llm_when_demo_mode_off(self):
        from unittest.mock import MagicMock, patch

        with (
            patch("src.llm.factory.settings") as s,
            patch("src.llm.factory.LLM") as MockLLM,
        ):
            s.demo_mode = False
            from src.config.settings import LLMProvider

            s.llm_provider = LLMProvider.OLLAMA
            s.ollama_model = "qwen3:8b"
            s.ollama_base_url = "http://localhost:11434"
            MockLLM.return_value = MagicMock()

            from src.llm.factory import LLMFactory

            LLMFactory.create()
            MockLLM.assert_called_once()
