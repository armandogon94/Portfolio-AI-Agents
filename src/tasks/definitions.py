import logging
from pathlib import Path
import yaml
from crewai import Agent, Task

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class TaskFactory:
    """Creates CrewAI tasks from YAML configuration with optional domain overrides."""

    def __init__(self, domain: str | None = None):
        self.tasks_config = _load_yaml(CONFIG_DIR / "tasks.yaml")
        self.domain_overrides = {}

        if domain:
            domain_path = CONFIG_DIR / "domains" / f"{domain}.yaml"
            if domain_path.exists():
                domain_config = _load_yaml(domain_path)
                self.domain_overrides = domain_config.get("task_overrides", {})

    def create(
        self, task_name: str, agent: Agent, async_execution: bool = False
    ) -> Task:
        """Create a single task by name, bound to an agent.

        Args:
            task_name: Key in tasks.yaml.
            agent: Agent that will execute this task.
            async_execution: If True, CrewAI runs the task concurrently
                with other async tasks in the same group (slice-22, DEC-20).
        """
        if task_name not in self.tasks_config:
            raise KeyError(
                f"Task '{task_name}' not found. Available: {list(self.tasks_config.keys())}"
            )

        config = dict(self.tasks_config[task_name])

        # Apply domain overrides
        if task_name in self.domain_overrides:
            config.update(self.domain_overrides[task_name])

        # Remove agent reference from config (we pass it explicitly)
        config.pop("agent", None)

        return Task(
            description=config["description"],
            agent=agent,
            expected_output=config["expected_output"],
            async_execution=async_execution,
        )

    def create_all(self, agents: dict[str, Agent]) -> list[Task]:
        """Create all tasks, mapping each to its configured agent."""
        tasks = []
        for task_name, config in self.tasks_config.items():
            agent_name = config.get("agent")
            if agent_name not in agents:
                logger.warning(f"Agent '{agent_name}' for task '{task_name}' not found, skipping")
                continue
            tasks.append(self.create(task_name, agents[agent_name]))
        return tasks
