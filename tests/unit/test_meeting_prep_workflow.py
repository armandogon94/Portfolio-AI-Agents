"""Meeting-prep workflow tests (slice-24).

Sequential + one parallel group:
  [attendee_research, topic_research] -> build_agenda -> build_talking_points
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestMeetingPrepWorkflow:
    def test_registered_as_sequential_with_parallel_group(self):
        from src.workflows import get_workflow

        wf = get_workflow("meeting_prep")
        assert wf.name == "meeting_prep"
        assert wf.process == "sequential"
        assert wf.parallel_tasks == [["attendee_research", "topic_research"]]

    def test_five_declared_roles_four_tasks(self):
        from src.workflows import get_workflow

        wf = get_workflow("meeting_prep")
        assert wf.agent_roles == [
            "attendee_researcher",
            "topic_researcher",
            "agenda_writer",
            "talking_points_writer",
        ]
        assert wf.task_names == [
            "attendee_research",
            "topic_research",
            "build_agenda",
            "build_talking_points",
        ]

    def test_build_crew_marks_researcher_tasks_async(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            agent_names = [
                "attendee_researcher",
                "topic_researcher",
                "agenda_writer",
                "talking_points_writer",
            ]
            agents = {n: MagicMock(name=n) for n in agent_names}
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "attendee_research": {"agent": "attendee_researcher"},
                "topic_research": {"agent": "topic_researcher"},
                "build_agenda": {"agent": "agenda_writer"},
                "build_talking_points": {"agent": "talking_points_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(
                    async_execution=async_execution
                )
            )

            from src.crew import build_crew

            build_crew(workflow_name="meeting_prep")

            async_map = {
                c.args[0]: c.kwargs.get("async_execution", False)
                for c in MockTaskFactory.return_value.create.call_args_list
            }
            assert async_map["attendee_research"] is True
            assert async_map["topic_research"] is True
            assert async_map["build_agenda"] is False
            assert async_map["build_talking_points"] is False

            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "sequential"

    def test_agenda_writer_emits_waiting_on_agent(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
            patch("src.crew.get_state_bus") as mock_get_bus,
        ):
            agents = {
                n: MagicMock(name=n)
                for n in (
                    "attendee_researcher",
                    "topic_researcher",
                    "agenda_writer",
                    "talking_points_writer",
                )
            }
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "attendee_research": {"agent": "attendee_researcher"},
                "topic_research": {"agent": "topic_researcher"},
                "build_agenda": {"agent": "agenda_writer"},
                "build_talking_points": {"agent": "talking_points_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock()
            )

            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus

            from src.crew import build_crew

            build_crew(workflow_name="meeting_prep", task_id="mp-run")

            waiting = [
                call.args[1]
                for call in mock_bus.publish.call_args_list
                if call.args[1].state == "waiting_on_agent"
            ]
            roles_waiting = {e.agent_role for e in waiting}
            assert "agenda_writer" in roles_waiting
            assert "talking_points_writer" in roles_waiting
