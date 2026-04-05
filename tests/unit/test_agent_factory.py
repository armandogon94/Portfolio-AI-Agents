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
        with patch("src.agents.factory.LLMFactory") as MockFactory:
            MockFactory.create.return_value = MagicMock()

            # Mock tool registry
            with patch("src.agents.factory.ToolRegistry") as MockRegistry:
                MockRegistry.get.return_value = MagicMock()

                from src.agents.factory import AgentFactory

                factory = AgentFactory()
                agents = factory.create_all()

                assert len(agents) == 4
                assert "researcher" in agents
                assert "analyst" in agents
                assert "writer" in agents
                assert "validator" in agents

    def test_agent_factory_with_domain(self):
        """AgentFactory applies domain overrides."""
        with patch("src.agents.factory.LLMFactory") as MockFactory:
            MockFactory.create.return_value = MagicMock()

            with patch("src.agents.factory.ToolRegistry") as MockRegistry:
                MockRegistry.get.return_value = MagicMock()

                from src.agents.factory import AgentFactory

                factory = AgentFactory(domain="healthcare")
                assert len(factory.domain_overrides) > 0
