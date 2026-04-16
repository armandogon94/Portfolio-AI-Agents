import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from crewai import Crew, Process

from src.agents.factory import AgentFactory
from src.models.schemas import AgentStateEvent
from src.tasks.definitions import TaskFactory

# Import tools to trigger registration via decorators
import src.tools.search  # noqa: F401
import src.tools.rag  # noqa: F401

logger = logging.getLogger(__name__)


def build_crew(
    domain: str | None = None,
    verbose: bool = True,
    step_callback: Callable[[Any], None] | None = None,
    task_id: str | None = None,
) -> Crew:
    """
    Build a complete CrewAI crew with agents, tasks, and tools.

    Args:
        domain: Optional industry domain. Applies domain-specific YAML overrides.
        verbose: Enable verbose output from agents.
        step_callback: Optional callable invoked after each agent step.
                       Receives an AgentAction or AgentFinish object.
        task_id: Optional task identifier. When set, step events are also
                 published to the AgentStateBus for live UI updates (slice-19).
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

    effective_callback = _wrap_callback_with_bus(step_callback, task_id) if task_id else step_callback

    # Assemble crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
        step_callback=effective_callback,
    )

    return crew


def _wrap_callback_with_bus(
    user_callback: Callable[[Any], None] | None,
    task_id: str,
) -> Callable[[Any], None]:
    """Compose a step_callback that emits to the AgentStateBus, then defers to user_callback.

    See DECISIONS.md DEC-16 (SSE contract) and DEC-27 (bus implementation).
    """
    from src.services.state_bus import get_state_bus

    bus = get_state_bus()

    def _composite(step: Any) -> None:
        try:
            event = _step_to_event(step, task_id)
            if event is not None:
                bus.publish(task_id, event)
        except Exception:  # pragma: no cover — never break the crew on telemetry
            logger.exception("Failed to publish agent state event")
        if user_callback is not None:
            user_callback(step)

    return _composite


def _step_to_event(step: Any, task_id: str) -> AgentStateEvent | None:
    """Map a CrewAI step (AgentAction / AgentFinish) to an AgentStateEvent.

    Agent role is a placeholder (`agent`) in slice-19; slice-22 will track the
    active agent per hierarchical/parallel workflow.
    """
    from crewai.agents.crew_agent_executor import AgentAction, AgentFinish

    ts = datetime.now(timezone.utc).isoformat()
    if isinstance(step, AgentAction):
        detail = f"tool: {step.tool}" if getattr(step, "tool", None) else "step"
        return AgentStateEvent(
            task_id=task_id, agent_role="agent",
            state="waiting_on_tool", detail=detail, ts=ts,
        )
    if isinstance(step, AgentFinish):
        return AgentStateEvent(
            task_id=task_id, agent_role="agent",
            state="active", detail="step complete", ts=ts,
        )
    return None


def run_crew(
    topic: str,
    domain: str | None = None,
    prior_context: str = "",
    task_id: str | None = None,
) -> str:
    """Build and execute a crew on a topic. Returns the final output.

    When `task_id` is set, per-step events are published to the AgentStateBus
    for the live team dashboard (slice-19).
    """
    crew = build_crew(domain=domain, task_id=task_id)
    result = crew.kickoff(inputs={"topic": topic, "prior_context": prior_context})
    return str(result)
