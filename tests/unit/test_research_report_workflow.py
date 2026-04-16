"""Regression tests for the migrated research_report workflow (slice-21).

Locks the Crew shape (agents, task order, process) before and after the
registry-based migration so the existing pipeline is byte-compatible.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestResearchReportWorkflow:
    def test_registered_by_canonical_name(self):
        from src.workflows import get_workflow

        wf = get_workflow("research_report")
        assert wf.name == "research_report"

    def test_has_four_agents_and_four_tasks_in_sequential_order(self):
        from src.workflows import get_workflow

        wf = get_workflow("research_report")
        assert wf.agent_roles == ["researcher", "analyst", "writer", "validator"]
        assert wf.task_names == ["research", "analysis", "writing", "validation"]
        assert wf.process == "sequential"
        assert wf.parallel_tasks is None

    def test_build_crew_assembles_research_report_pipeline(self):
        """build_crew(workflow_name='research_report') builds the 4-agent sequential crew."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            mock_agents = {
                "researcher": MagicMock(name="researcher"),
                "analyst": MagicMock(name="analyst"),
                "writer": MagicMock(name="writer"),
                "validator": MagicMock(name="validator"),
            }
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.tasks_config = {
                "research": {"agent": "researcher"},
                "analysis": {"agent": "analyst"},
                "writing": {"agent": "writer"},
                "validation": {"agent": "validator"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda task_name, agent, async_execution=False: MagicMock(name=f"task_{task_name}")
            )

            from src.crew import build_crew

            build_crew(workflow_name="research_report")

            call_kwargs = MockCrew.call_args.kwargs
            assert call_kwargs["process"].name == "sequential"
            assert len(call_kwargs["agents"]) == 4
            assert len(call_kwargs["tasks"]) == 4

            task_order = [
                c.args[0] for c in MockTaskFactory.return_value.create.call_args_list
            ]
            assert task_order == ["research", "analysis", "writing", "validation"]

    def test_build_crew_defaults_to_research_report_when_unspecified(self):
        """Backward compat: build_crew() without workflow_name still produces the 4-agent pipeline."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            mock_agents = {
                "researcher": MagicMock(),
                "analyst": MagicMock(),
                "writer": MagicMock(),
                "validator": MagicMock(),
            }
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.tasks_config = {
                "research": {"agent": "researcher"},
                "analysis": {"agent": "analyst"},
                "writing": {"agent": "writer"},
                "validation": {"agent": "validator"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda task_name, agent, async_execution=False: MagicMock()
            )

            from src.crew import build_crew

            build_crew()  # no workflow_name — should default to research_report
            assert len(MockCrew.call_args.kwargs["tasks"]) == 4
