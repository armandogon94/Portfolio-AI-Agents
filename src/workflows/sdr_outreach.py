"""SDR outreach — persona-driven multi-variant outbound (slice-23).

Persona researcher runs first. Three copywriter variants (formal, casual,
provocative) draft in parallel. Tone checker picks the best variant with
a justification.

This is the headline parallelism demo for the Sales pack — the dashboard
lights three cards at once.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="sdr_outreach",
    description=(
        "Sales — persona researcher produces a buyer sketch, then three "
        "copywriters draft outbound variants in parallel (formal, casual, "
        "provocative). A tone checker picks the winner."
    ),
    agent_roles=[
        "persona_researcher",
        "copywriter_formal",
        "copywriter_casual",
        "copywriter_provocative",
        "tone_checker",
    ],
    task_names=[
        "persona_research",
        "draft_formal",
        "draft_casual",
        "draft_provocative",
        "tone_check",
    ],
    process="sequential",
    parallel_tasks=[
        ["draft_formal", "draft_casual", "draft_provocative"],
    ],
    inputs_schema={
        "topic": "Description of the target contact (name, title, company).",
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
