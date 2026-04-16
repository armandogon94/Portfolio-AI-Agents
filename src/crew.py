import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from crewai import Crew, Process

from src.agents.factory import AgentFactory
from src.exceptions import ValidationError
from src.models.schemas import AgentStateEvent
from src.services.state_bus import get_state_bus
from src.tasks.definitions import TaskFactory
from src.workflows import get_workflow
from src.workflows.base import Workflow

# Import tools to trigger registration via decorators
import src.tools.search  # noqa: F401
import src.tools.rag  # noqa: F401

logger = logging.getLogger(__name__)

_DEFAULT_WORKFLOW = "research_report"


def build_crew(
    workflow_name: str = _DEFAULT_WORKFLOW,
    domain: str | None = None,
    verbose: bool = True,
    step_callback: Callable[[Any], None] | None = None,
    task_id: str | None = None,
) -> Crew:
    """
    Build a complete CrewAI crew from a registered workflow template.

    Args:
        workflow_name: Name of a workflow registered in ``src.workflows``
            (default: ``"research_report"``, the v1-v3 pipeline).
        domain: Optional industry domain. Applies domain-specific YAML overrides.
        verbose: Enable verbose output from agents.
        step_callback: Optional callable invoked after each agent step.
                       Receives an AgentAction or AgentFinish object.
        task_id: Optional task identifier. When set, step events are also
                 published to the AgentStateBus for live UI updates (slice-19).

    Raises:
        ValidationError: If ``workflow_name`` is not registered.
    """
    try:
        workflow = get_workflow(workflow_name)
    except KeyError as exc:
        raise ValidationError(str(exc)) from exc

    logger.info(
        f"Building crew (workflow={workflow.name}, domain={domain or 'general'})"
    )

    # Create agents from YAML, filtered to the workflow's declared roles.
    agent_factory = AgentFactory(domain=domain)
    all_agents = agent_factory.create_all()
    missing = [role for role in workflow.agent_roles if role not in all_agents]
    if missing:
        raise ValidationError(
            f"Workflow '{workflow.name}' requires agents not in agents.yaml: {missing}"
        )
    agents = {role: all_agents[role] for role in workflow.agent_roles}
    logger.info(f"Created {len(agents)} agents: {list(agents)}")

    # Slice 22: hierarchical workflows pull the manager out of the agents list
    # and enable delegation on the remaining specialists. DEC-13 default
    # (allow_delegation=False) is preserved for sequential workflows.
    manager_agent = None
    if workflow.process == "hierarchical":
        if not workflow.manager_agent:
            raise ValidationError(
                f"Hierarchical workflow '{workflow.name}' requires a manager_agent."
            )
        if workflow.manager_agent not in agents:
            raise ValidationError(
                f"Hierarchical workflow '{workflow.name}': manager '{workflow.manager_agent}' "
                f"is not in agent_roles {workflow.agent_roles}."
            )
        manager_agent = agents.pop(workflow.manager_agent)
        for role_agent in agents.values():
            role_agent.allow_delegation = True

    # Collect parallel task names (DEC-20). Tasks in any group run with
    # async_execution=True; downstream tasks block on their completion.
    parallel_task_names: set[str] = set()
    if workflow.parallel_tasks:
        for group in workflow.parallel_tasks:
            parallel_task_names.update(group)

    # Create tasks in the workflow's declared order, binding each to its
    # YAML-configured agent.
    task_factory = TaskFactory(domain=domain)
    tasks = []
    for task_name in workflow.task_names:
        cfg = task_factory.tasks_config.get(task_name)
        if cfg is None:
            raise ValidationError(
                f"Workflow '{workflow.name}' references unknown task '{task_name}'"
            )
        agent_name = cfg.get("agent")
        # Manager agents don't appear in `agents` after pop; skip the
        # "agent not in workflow" check for hierarchical workflows that
        # assign the manager as a task owner.
        available_agents = dict(agents)
        if manager_agent is not None and agent_name == workflow.manager_agent:
            available_agents[workflow.manager_agent] = manager_agent
        if agent_name not in available_agents:
            raise ValidationError(
                f"Workflow '{workflow.name}': task '{task_name}' needs agent "
                f"'{agent_name}', which is not in the workflow's agent_roles."
            )
        tasks.append(
            task_factory.create(
                task_name,
                available_agents[agent_name],
                async_execution=task_name in parallel_task_names,
            )
        )
    logger.info(f"Created {len(tasks)} tasks for workflow {workflow.name}")

    # Telegraph parallel dependencies to the state bus so the dashboard can
    # render downstream tasks as 'waiting_on_agent' before predecessors finish.
    if task_id:
        _publish_waiting_for_parallel_deps(workflow, task_factory, task_id)

    effective_callback = (
        _wrap_callback_with_bus(step_callback, task_id) if task_id else step_callback
    )

    process = (
        Process.hierarchical
        if workflow.process == "hierarchical"
        else Process.sequential
    )

    crew_kwargs: dict[str, Any] = {
        "agents": list(agents.values()),
        "tasks": tasks,
        "process": process,
        "verbose": verbose,
        "step_callback": effective_callback,
    }
    if manager_agent is not None:
        crew_kwargs["manager_agent"] = manager_agent

    crew = Crew(**crew_kwargs)

    return crew


def _publish_waiting_for_parallel_deps(
    workflow: Workflow, task_factory: TaskFactory, task_id: str
) -> None:
    """Emit synthetic ``waiting_on_agent`` events for tasks blocked on parallel groups.

    Called once at crew-build time so the live dashboard can render the
    dependency chain before the first parallel task completes. Non-parallel
    tasks that come AFTER a parallel group are treated as waiting.
    """
    if not workflow.parallel_tasks:
        return
    parallel_names: set[str] = set()
    for group in workflow.parallel_tasks:
        parallel_names.update(group)

    bus = get_state_bus()
    ts = datetime.now(timezone.utc).isoformat()
    seen_parallel = False
    for task_name in workflow.task_names:
        if task_name in parallel_names:
            seen_parallel = True
            continue
        if not seen_parallel:
            continue
        cfg = task_factory.tasks_config.get(task_name, {}) or {}
        role = cfg.get("agent", task_name)
        bus.publish(
            task_id,
            AgentStateEvent(
                task_id=task_id,
                agent_role=role,
                state="waiting_on_agent",
                detail=f"waiting on parallel group for task '{task_name}'",
                ts=ts,
            ),
        )


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
    workflow_name: str = _DEFAULT_WORKFLOW,
) -> str:
    """Build and execute a crew on a topic. Returns the final output.

    When `task_id` is set, per-step events are published to the AgentStateBus
    for the live team dashboard (slice-19). `workflow_name` selects the
    workflow template (slice-21).
    """
    crew = build_crew(workflow_name=workflow_name, domain=domain, task_id=task_id)
    result = crew.kickoff(inputs={"topic": topic, "prior_context": prior_context})
    return str(result)
