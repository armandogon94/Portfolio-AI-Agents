"""Lead-qualifier workflow tests (slice-23).

Sequential 3-agent pipeline: researcher → scorer → report_writer.
Output is a scored report tied to a rubric defined in the module.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestLeadQualifierWorkflow:
    def test_workflow_registered_and_sequential(self):
        from src.workflows import get_workflow

        wf = get_workflow("lead_qualifier")
        assert wf.name == "lead_qualifier"
        assert wf.process == "sequential"
        assert wf.parallel_tasks is None

    def test_workflow_uses_three_agents_in_correct_order(self):
        from src.workflows import get_workflow

        wf = get_workflow("lead_qualifier")
        assert wf.agent_roles == ["researcher", "scorer", "report_writer"]
        assert wf.task_names == [
            "lead_research",
            "lead_scoring",
            "lead_report",
        ]

    def test_scoring_rubric_is_module_level_constant(self):
        """Rubric must not be user-configurable — ensures deterministic grading
        across runs and closes a tampering vector via webhook payloads."""
        from src.workflows import lead_qualifier as lq

        assert hasattr(lq, "SCORING_RUBRIC")
        rubric = lq.SCORING_RUBRIC
        assert isinstance(rubric, dict)
        assert len(rubric) >= 3  # at least 3 criteria
        for criterion, weight in rubric.items():
            assert isinstance(criterion, str) and criterion
            assert isinstance(weight, (int, float))
            assert 0 < weight <= 1.0
        # Weights should sum to ~1.0 (tolerance for floats)
        assert abs(sum(rubric.values()) - 1.0) < 0.01

    def test_build_crew_assembles_three_sequential_tasks(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            mock_agents = {
                "researcher": MagicMock(),
                "scorer": MagicMock(),
                "report_writer": MagicMock(),
            }
            for a in mock_agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.tasks_config = {
                "lead_research": {"agent": "researcher"},
                "lead_scoring": {"agent": "scorer"},
                "lead_report": {"agent": "report_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(
                    name=f"task_{t}", async_execution=async_execution
                )
            )

            from src.crew import build_crew

            build_crew(workflow_name="lead_qualifier")

            call_names = [
                c.args[0]
                for c in MockTaskFactory.return_value.create.call_args_list
            ]
            assert call_names == ["lead_research", "lead_scoring", "lead_report"]

            # None should be async for a sequential workflow
            for call in MockTaskFactory.return_value.create.call_args_list:
                assert call.kwargs.get("async_execution") is False

            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "sequential"
            assert len(kwargs["tasks"]) == 3
