import logging
from pathlib import Path
import yaml
from crewai import Agent
from src.llm.factory import LLMFactory
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class AgentFactory:
    """Creates CrewAI agents from YAML configuration with optional domain overrides."""

    def __init__(self, domain: str | None = None):
        self.agents_config = _load_yaml(CONFIG_DIR / "agents.yaml")
        self.domain_overrides = {}

        if domain:
            domain_path = CONFIG_DIR / "domains" / f"{domain}.yaml"
            if domain_path.exists():
                domain_config = _load_yaml(domain_path)
                self.domain_overrides = domain_config.get("agent_overrides", {})
                logger.info(f"Loaded domain overrides: {domain}")

        self.llm = LLMFactory.create()

    def create(self, agent_name: str) -> Agent:
        """Create a single agent by name."""
        if agent_name not in self.agents_config:
            raise KeyError(
                f"Agent '{agent_name}' not found. Available: {list(self.agents_config.keys())}"
            )

        config = dict(self.agents_config[agent_name])

        # Apply domain overrides
        if agent_name in self.domain_overrides:
            config.update(self.domain_overrides[agent_name])

        # Resolve tool names to instances
        tool_names = config.pop("tools", [])
        tools = []
        for name in tool_names:
            try:
                tools.append(ToolRegistry.get(name))
            except KeyError:
                logger.warning(f"Tool '{name}' not found, skipping for agent '{agent_name}'")

        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=tools,
            llm=self.llm,
            allow_delegation=config.get("allow_delegation", False),
            verbose=config.get("verbose", True),
        )

    def create_all(self) -> dict[str, Agent]:
        """Create all agents defined in config."""
        return {name: self.create(name) for name in self.agents_config}
