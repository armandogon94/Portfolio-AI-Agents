"""Real-estate comparative market analysis (CMA) — slice-25.

[comps_gather, market_analyze] run in parallel → appraise → cma_report.

Security note: this workflow is **read-only**. The inputs_schema has no
``price`` / ``target_price`` / ``override`` field on purpose — a caller
cannot pre-bias the estimated value through the API. The appraiser derives
its range solely from the comps + market narrative generated upstream.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="real_estate_cma",
    description=(
        "Real Estate — comparative market analysis. Comps gatherer and "
        "market analyst run in parallel, then an appraiser produces a "
        "value range, then the report writer assembles a client-facing CMA."
    ),
    agent_roles=[
        "comps_gatherer",
        "market_analyst",
        "appraiser",
        "report_writer",
    ],
    task_names=[
        "comps_gather",
        "market_analyze",
        "appraise",
        "cma_report",
    ],
    process="sequential",
    parallel_tasks=[["comps_gather", "market_analyze"]],
    inputs_schema={
        "topic": (
            "The subject property: address and any non-price characteristics "
            "(square_feet, beds, baths, year_built). Price hints are ignored "
            "on purpose — the appraiser derives the range from comps + market."
        ),
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
