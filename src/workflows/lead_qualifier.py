"""Lead qualifier — sequential 3-agent sales workflow (slice-23).

Researcher gathers company signals → Scorer grades against a fixed rubric →
Report Writer produces the one-page sales brief.

The scoring rubric lives as a module-level constant (not user input) so
the same signals produce the same score across runs — a tampering guard
for webhook-driven flows where the crew's output influences downstream
systems.
"""

from __future__ import annotations

from src.workflows.base import Workflow

SCORING_RUBRIC: dict[str, float] = {
    "icp_fit": 0.35,          # Employee count / industry / stage match
    "pain_signal": 0.25,      # Evidence of the problem our product solves
    "tech_stack_match": 0.20, # Their tooling is compatible with ours
    "reachability": 0.10,     # Named contact, public email or LinkedIn
    "timing": 0.10,           # Hiring, funding, product launch within 90d
}


WORKFLOW = Workflow(
    name="lead_qualifier",
    description=(
        "Sales — qualify a prospect against a fixed ICP rubric. Researcher "
        "gathers signals, Scorer grades on the rubric, Report Writer drafts "
        "a one-page brief with a recommended next action."
    ),
    agent_roles=["researcher", "scorer", "report_writer"],
    task_names=["lead_research", "lead_scoring", "lead_report"],
    process="sequential",
    parallel_tasks=None,
    inputs_schema={
        "topic": "Prospect company name or lead handle (e.g. 'Acme Corp' or 'CTO at Acme').",
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
