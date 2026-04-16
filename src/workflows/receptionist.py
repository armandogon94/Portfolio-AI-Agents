"""Receptionist — voice-capable outbound call workflow (slice-26, DEC-21, DEC-22).

Sequential: intake_agent parses the request → caller_agent dials via
Twilio and drives the TwiML conversation → summary_agent writes the
post-call report.

This workflow requires ``VOICE_ENABLED=true`` and a verified destination
number in ``TWILIO_VERIFIED_TO_NUMBERS`` at run time. Unit-test runs
mock Twilio entirely.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="receptionist",
    description=(
        "Voice — a receptionist that places an outbound call via Twilio and "
        "writes the post-call report. Gated by VOICE_ENABLED and a verified-"
        "number whitelist (DEC-22). Demo-only; TCPA applies."
    ),
    agent_roles=["intake_agent", "caller_agent", "summary_agent"],
    task_names=["voice_intake", "voice_call", "voice_summary"],
    process="sequential",
    parallel_tasks=None,
    inputs_schema={
        "topic": (
            "Free-text call request: destination, goal, any details the "
            "agent should mention (e.g. 'Book a table for 4 at 7pm at Luigi's')."
        ),
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
