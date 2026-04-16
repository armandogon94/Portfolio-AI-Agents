"""Meeting prep — parallel research + sequential synthesis (slice-24, DEC-20).

[attendee_research, topic_research] run concurrently, then agenda_writer
assembles the agenda, then talking_points_writer turns it into bullets.

The agenda_writer and talking_points_writer are telegraphed to the state
bus as ``waiting_on_agent`` at build time by the slice-22 helper.
"""

from __future__ import annotations

from src.workflows.base import Workflow

WORKFLOW = Workflow(
    name="meeting_prep",
    description=(
        "Ops — meeting prep. Attendee researcher and topic researcher run "
        "in parallel; agenda writer assembles a time-boxed agenda; talking "
        "points writer produces on-screen bullets for the chair."
    ),
    agent_roles=[
        "attendee_researcher",
        "topic_researcher",
        "agenda_writer",
        "talking_points_writer",
    ],
    task_names=[
        "attendee_research",
        "topic_research",
        "build_agenda",
        "build_talking_points",
    ],
    process="sequential",
    parallel_tasks=[["attendee_research", "topic_research"]],
    inputs_schema={
        "topic": "The meeting description: topic, attendees, duration.",
        "prior_context": "Optional prior session context.",
    },
)


def register() -> None:
    from src.workflows import register_workflow

    register_workflow(WORKFLOW)


register()
