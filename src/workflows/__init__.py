"""Pluggable workflow registry (slice-21, DEC-18).

Built-in workflows register themselves on import. Consumers import
:func:`get_workflow`, :func:`list_workflows`, or :func:`register_workflow`.
"""

from __future__ import annotations

from src.workflows.base import Workflow

_REGISTRY: dict[str, Workflow] = {}


def register_workflow(workflow: Workflow) -> None:
    """Add a workflow to the registry. Duplicate names raise ``ValueError``."""
    if workflow.name in _REGISTRY:
        raise ValueError(f"Workflow '{workflow.name}' is already registered")
    _REGISTRY[workflow.name] = workflow


def get_workflow(name: str) -> Workflow:
    """Return the workflow registered under ``name`` or raise ``KeyError``."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown workflow: {name!r}")
    return _REGISTRY[name]


def list_workflows() -> list[Workflow]:
    """Return all registered workflows, ordered by registration."""
    return list(_REGISTRY.values())


# Auto-register built-in workflows. Keep imports at the bottom to avoid
# circular imports — each module calls register_workflow() at import time.
from src.workflows import research_report  # noqa: E402, F401
from src.workflows import lead_qualifier  # noqa: E402, F401
from src.workflows import sdr_outreach  # noqa: E402, F401
from src.workflows import support_triage  # noqa: E402, F401
from src.workflows import meeting_prep  # noqa: E402, F401
from src.workflows import content_pipeline  # noqa: E402, F401
from src.workflows import real_estate_cma  # noqa: E402, F401
