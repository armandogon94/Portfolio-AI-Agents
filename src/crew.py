import logging
from crewai import Crew, Process
from src.agents.factory import AgentFactory
from src.tasks.definitions import TaskFactory

# Import tools to trigger registration via decorators
import src.tools.search  # noqa: F401
import src.tools.rag  # noqa: F401

logger = logging.getLogger(__name__)


def build_crew(domain: str | None = None, verbose: bool = True) -> Crew:
    """
    Build a complete CrewAI crew with agents, tasks, and tools.

    Args:
        domain: Optional industry domain (healthcare, finance, real_estate).
                Applies domain-specific agent/task overrides.
        verbose: Enable verbose output from agents.
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
    )

    return crew


def run_crew(topic: str, domain: str | None = None) -> str:
    """Build and execute a crew on a topic. Returns the final output."""
    crew = build_crew(domain=domain)
    result = crew.kickoff(inputs={"topic": topic})
    return str(result)
