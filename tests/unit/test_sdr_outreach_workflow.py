"""SDR outreach workflow tests (slice-23).

Sequential with a parallel drafting group:
  persona_research -> [draft_formal, draft_casual, draft_provocative] -> tone_check
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestSdrOutreachWorkflow:
    def test_workflow_registered(self):
        from src.workflows import get_workflow

        wf = get_workflow("sdr_outreach")
        assert wf.name == "sdr_outreach"

    def test_workflow_has_parallel_copywriter_group(self):
        from src.workflows import get_workflow

        wf = get_workflow("sdr_outreach")
        assert wf.parallel_tasks == [
            ["draft_formal", "draft_casual", "draft_provocative"]
        ]
        # Task list is persona_research first, drafts in the middle, tone_check last.
        assert wf.task_names[0] == "persona_research"
        assert wf.task_names[-1] == "tone_check"
        for name in ("draft_formal", "draft_casual", "draft_provocative"):
            assert name in wf.task_names

    def test_workflow_declares_five_agents(self):
        from src.workflows import get_workflow

        wf = get_workflow("sdr_outreach")
        assert set(wf.agent_roles) == {
            "persona_researcher",
            "copywriter_formal",
            "copywriter_casual",
            "copywriter_provocative",
            "tone_checker",
        }

    def test_build_crew_marks_drafting_tasks_async(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            agent_names = [
                "persona_researcher",
                "copywriter_formal",
                "copywriter_casual",
                "copywriter_provocative",
                "tone_checker",
            ]
            mock_agents = {n: MagicMock(name=n) for n in agent_names}
            for a in mock_agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = mock_agents

            MockTaskFactory.return_value.tasks_config = {
                "persona_research": {"agent": "persona_researcher"},
                "draft_formal": {"agent": "copywriter_formal"},
                "draft_casual": {"agent": "copywriter_casual"},
                "draft_provocative": {"agent": "copywriter_provocative"},
                "tone_check": {"agent": "tone_checker"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(
                    name=f"task_{t}", async_execution=async_execution
                )
            )

            from src.crew import build_crew

            build_crew(workflow_name="sdr_outreach")

            async_map = {}
            for call in MockTaskFactory.return_value.create.call_args_list:
                async_map[call.args[0]] = call.kwargs.get("async_execution", False)

            assert async_map["persona_research"] is False
            assert async_map["draft_formal"] is True
            assert async_map["draft_casual"] is True
            assert async_map["draft_provocative"] is True
            assert async_map["tone_check"] is False

            kwargs = MockCrew.call_args.kwargs
            assert len(kwargs["tasks"]) == 5

    def test_downstream_tone_check_emits_waiting_on_agent(self):
        """The tone_checker runs after the parallel drafting group —
        state-bus telegraphs its dependency (slice-22 helper reused)."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
            patch("src.crew.get_state_bus") as mock_get_bus,
        ):
            agent_names = [
                "persona_researcher",
                "copywriter_formal",
                "copywriter_casual",
                "copywriter_provocative",
                "tone_checker",
            ]
            mock_agents = {n: MagicMock(name=n) for n in agent_names}
            for a in mock_agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.tasks_config = {
                "persona_research": {"agent": "persona_researcher"},
                "draft_formal": {"agent": "copywriter_formal"},
                "draft_casual": {"agent": "copywriter_casual"},
                "draft_provocative": {"agent": "copywriter_provocative"},
                "tone_check": {"agent": "tone_checker"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock()
            )

            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus

            from src.crew import build_crew

            build_crew(workflow_name="sdr_outreach", task_id="sdr-run")

            waiting_events = [
                call.args[1]
                for call in mock_bus.publish.call_args_list
                if call.args[1].state == "waiting_on_agent"
            ]
            assert any(e.agent_role == "tone_checker" for e in waiting_events)
