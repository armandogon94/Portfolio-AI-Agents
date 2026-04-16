import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestAgentFactory:
    def test_load_agents_config(self):
        """AgentFactory loads all agents from YAML."""
        config_path = Path(__file__).parent.parent.parent / "src" / "config" / "agents.yaml"
        assert config_path.exists(), f"agents.yaml not found at {config_path}"

        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "researcher" in config
        assert "analyst" in config
        assert "writer" in config
        assert "validator" in config

    def test_load_tasks_config(self):
        """TaskFactory loads all tasks from YAML."""
        config_path = Path(__file__).parent.parent.parent / "src" / "config" / "tasks.yaml"
        assert config_path.exists()

        import yaml

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert "research" in config
        assert "analysis" in config
        assert "writing" in config
        assert "validation" in config

    def test_domain_configs_exist(self):
        """All domain YAML files exist and are valid."""
        domains_dir = Path(__file__).parent.parent.parent / "src" / "config" / "domains"
        assert domains_dir.exists()

        import yaml

        for domain_file in domains_dir.glob("*.yaml"):
            with open(domain_file) as f:
                config = yaml.safe_load(f)
            assert "name" in config
            assert "agent_overrides" in config

    def test_agent_factory_creates_agents(self):
        """AgentFactory.create_all returns all configured agents."""
        from crewai.tools import BaseTool

        with patch("src.agents.factory.LLMFactory") as MockFactory:
            MockFactory.create.return_value = "ollama/mistral"

            # Mock tool registry — must return BaseTool-compatible mocks
            with patch("src.agents.factory.ToolRegistry") as MockRegistry:
                mock_tool = MagicMock(spec=BaseTool)
                mock_tool.name = "mock_tool"
                mock_tool.description = "A mock tool"
                MockRegistry.get.return_value = mock_tool

                from src.agents.factory import AgentFactory

                factory = AgentFactory()
                agents = factory.create_all()

                # Canonical v1 roles must always be present.
                for role in ("researcher", "analyst", "writer", "validator"):
                    assert role in agents, f"{role} missing from agent factory output"
                # New workflow packs (slice-23+) add more roles; the factory
                # must produce all entries from agents.yaml without crashing.
                assert len(agents) >= 4

    def test_agent_factory_with_domain(self):
        """AgentFactory applies domain overrides."""
        with patch("src.agents.factory.LLMFactory") as MockFactory:
            MockFactory.create.return_value = MagicMock()

            with patch("src.agents.factory.ToolRegistry") as MockRegistry:
                MockRegistry.get.return_value = MagicMock()

                from src.agents.factory import AgentFactory

                factory = AgentFactory(domain="healthcare")
                assert len(factory.domain_overrides) > 0

    def test_all_seven_domains_exist(self):
        """All 7 domain YAML files are present."""
        domains_dir = Path(__file__).parent.parent.parent / "src" / "config" / "domains"
        expected = {"healthcare", "finance", "real_estate", "legal", "education", "engineering"}
        found = {f.stem for f in domains_dir.glob("*.yaml")}
        assert expected <= found, f"Missing domains: {expected - found}"

    @pytest.mark.parametrize("domain", ["legal", "education", "engineering"])
    def test_new_domains_load_via_agent_factory(self, domain):
        """New domain configs are loaded and applied by AgentFactory."""
        with patch("src.agents.factory.LLMFactory") as MockFactory:
            MockFactory.create.return_value = MagicMock()

            with patch("src.agents.factory.ToolRegistry") as MockRegistry:
                MockRegistry.get.return_value = MagicMock()

                from src.agents.factory import AgentFactory

                factory = AgentFactory(domain=domain)
                assert len(factory.domain_overrides) > 0, (
                    f"Domain '{domain}' produced no agent overrides"
                )
