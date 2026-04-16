"""Content pipeline — sequential 5-agent editorial workflow (slice-25).

researcher → outliner → writer → editor → seo_optimizer.
Reuses the canonical ``researcher`` and ``writer`` from v1 agents.yaml.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="content_pipeline",
    description=(
        "Content — a full editorial pipeline. Researcher gathers sources, "
        "Outliner structures the piece, Writer drafts the body, Editor "
        "polishes, SEO Optimizer produces metadata + on-page suggestions."
    ),
    agent_roles=["researcher", "outliner", "writer", "editor", "seo_optimizer"],
    task_names=[
        "research",
        "content_outline",
        "content_draft",
        "content_edit",
        "content_seo",
    ],
    process="sequential",
    parallel_tasks=None,
    inputs_schema={
        "topic": "Article topic with optional audience/reading-level hints.",
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
