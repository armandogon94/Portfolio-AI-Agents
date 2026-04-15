import logging
from collections.abc import Callable
from typing import Any

from crewai import Crew, Process

from src.agents.factory import AgentFactory
from src.tasks.definitions import TaskFactory

# Import tools to trigger registration via decorators
import src.tools.search  # noqa: F401
import src.tools.rag  # noqa: F401

logger = logging.getLogger(__name__)


def build_crew(
    domain: str | None = None,
    verbose: bool = True,
    step_callback: Callable[[Any], None] | None = None,
) -> Crew:
    """
    Build a complete CrewAI crew with agents, tasks, and tools.

    Args:
        domain: Optional industry domain. Applies domain-specific YAML overrides.
        verbose: Enable verbose output from agents.
        step_callback: Optional callable invoked after each agent step.
                       Receives an AgentAction or AgentFinish object.
    """
    logger.info(f"Building crew (domain={domain or 'general'})")

    # Create agents from YAML config
    agent_factory = AgentFactory(domain=domain)
    agents = agent_factory.create_all()
    logger.info(f"Created {len(agents)} agents: {list(agents.keys())}")

    # Create tasks from YAML config, bound to agents
    task_factory = TaskFactory(domain=domain)
    tasks = task_factory.create_all(agents)
    logger.info(f"Created {len(tasks)} tasks")

    # Assemble crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
        step_callback=step_callback,
    )

    return crew


def run_crew(topic: str, domain: str | None = None, prior_context: str = "") -> str:
    """Build and execute a crew on a topic. Returns the final output."""
    crew = build_crew(domain=domain)
    result = crew.kickoff(inputs={"topic": topic, "prior_context": prior_context})
    return str(result)
