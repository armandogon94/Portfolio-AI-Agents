"""Support triage — hierarchical delegation workflow (slice-24, DEC-19).

triage_manager (manager) delegates to:
  - kb_searcher (RAG)
  - sentiment_analyst
  - response_writer

The slice-22 hierarchical plumbing pops the manager out of the agents
list, enables ``allow_delegation=True`` on the specialists, and passes
the manager as ``Crew(manager_agent=...)``.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="support_triage",
    description=(
        "Support — hierarchical triage. A triage_manager delegates KB lookup, "
        "sentiment analysis, and response drafting to specialists, then "
        "stitches their work into a single customer-facing plan."
    ),
    agent_roles=[
        "triage_manager",
        "kb_searcher",
        "sentiment_analyst",
        "response_writer",
    ],
    task_names=[
        "triage_route",
        "kb_search",
        "sentiment_analyze",
        "response_draft",
    ],
    process="hierarchical",
    manager_agent="triage_manager",
    parallel_tasks=None,
    inputs_schema={
        "topic": "The raw inbound support ticket text.",
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
