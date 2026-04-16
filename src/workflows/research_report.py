"""Research-report workflow — the v1/v2/v3 default pipeline (slice-21).

Four sequential agents: researcher → analyst → writer → validator.
Matches the behavior of the pre-v4 ``src/crew.py`` build_crew() and keeps
``POST /crew/run`` backward-compatible for callers that don't supply a
``workflow`` field.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="research_report",
    description=(
        "Classic 4-agent research pipeline: Researcher gathers sources, "
        "Analyst extracts insights, Writer drafts the report, Validator "
        "reviews the final output. Sequential process."
    ),
    agent_roles=["researcher", "analyst", "writer", "validator"],
    task_names=["research", "analysis", "writing", "validation"],
    process="sequential",
    parallel_tasks=None,
    inputs_schema={
        "topic": "The subject the crew will research and report on.",
        "prior_context": "Optional prior session context for continuity.",
    },
)


def register() -> None:
    """Register this workflow with the global registry."""
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
