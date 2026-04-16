"""Workflow dataclass — the declarative shape of a crew template (slice-21, DEC-18)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Workflow:
    """A named, pluggable crew template.

    Attributes:
        name: Stable identifier used on the API and in URLs.
        description: Human-readable summary (shown in the dashboard launcher).
        agent_roles: Names from ``src/config/agents.yaml`` to include, in the
            order they should appear in the Crew's agent list.
        task_names: Names from ``src/config/tasks.yaml`` to include, in
            execution order (sequential) or logical order (hierarchical).
        process: Either ``"sequential"`` (default) or ``"hierarchical"``.
            Hierarchical support lands in slice-22.
        manager_agent: Role name of the manager agent when
            ``process == "hierarchical"``. Unused today; reserved for slice-22.
        parallel_tasks: Optional list of concurrent groups. Each inner list
            holds task names that should run with ``async_execution=True``.
            Unused today; reserved for slice-22.
        inputs_schema: Free-form documentation of accepted ``inputs`` keys
            for the ``crew.kickoff`` call — surfaced via ``GET /workflows``.
    """

    name: str
    description: str
    agent_roles: list[str]
    task_names: list[str]
    process: str = "sequential"
    manager_agent: str | None = None
    parallel_tasks: list[list[str]] | None = None
    inputs_schema: dict[str, str] = field(default_factory=dict)
