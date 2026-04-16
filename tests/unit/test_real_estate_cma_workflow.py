"""Real-estate CMA workflow tests (slice-25).

[comps_gather, market_analyze] (parallel) -> appraise -> cma_report.
CMA is read-only; the workflow must not accept a price-override input.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestRealEstateCmaWorkflow:
    def test_registered_with_parallel_comps_and_market(self):
        from src.workflows import get_workflow

        wf = get_workflow("real_estate_cma")
        assert wf.name == "real_estate_cma"
        assert wf.process == "sequential"
        assert wf.parallel_tasks == [["comps_gather", "market_analyze"]]

    def test_four_roles_four_tasks_in_order(self):
        from src.workflows import get_workflow

        wf = get_workflow("real_estate_cma")
        assert wf.agent_roles == [
            "comps_gatherer",
            "market_analyst",
            "appraiser",
            "report_writer",
        ]
        assert wf.task_names == [
            "comps_gather",
            "market_analyze",
            "appraise",
            "cma_report",
        ]

    def test_inputs_schema_has_no_price_override_field(self):
        """Security — the CMA must be data-driven. Reject any input field
        that would let a caller pre-bias the estimated value."""
        from src.workflows import get_workflow

        wf = get_workflow("real_estate_cma")
        keys = {k.lower() for k in wf.inputs_schema}
        forbidden = {"price", "estimated_value", "override", "target_price"}
        assert not (keys & forbidden), (
            f"CMA inputs_schema must not include price-steering fields; "
            f"found: {keys & forbidden}"
        )

    def test_build_crew_marks_parallel_group_async(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            agents = {
                n: MagicMock(name=n)
                for n in (
                    "comps_gatherer",
                    "market_analyst",
                    "appraiser",
                    "report_writer",
                )
            }
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "comps_gather": {"agent": "comps_gatherer"},
                "market_analyze": {"agent": "market_analyst"},
                "appraise": {"agent": "appraiser"},
                "cma_report": {"agent": "report_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(
                    async_execution=async_execution
                )
            )

            from src.crew import build_crew

            build_crew(workflow_name="real_estate_cma")

            async_map = {
                c.args[0]: c.kwargs.get("async_execution", False)
                for c in MockTaskFactory.return_value.create.call_args_list
            }
            assert async_map == {
                "comps_gather": True,
                "market_analyze": True,
                "appraise": False,
                "cma_report": False,
            }
            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "sequential"

    def test_appraiser_emits_waiting_on_agent(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
            patch("src.crew.get_state_bus") as mock_get_bus,
        ):
            agents = {
                n: MagicMock(name=n)
                for n in (
                    "comps_gatherer",
                    "market_analyst",
                    "appraiser",
                    "report_writer",
                )
            }
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "comps_gather": {"agent": "comps_gatherer"},
                "market_analyze": {"agent": "market_analyst"},
                "appraise": {"agent": "appraiser"},
                "cma_report": {"agent": "report_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock()
            )

            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus

            from src.crew import build_crew

            build_crew(workflow_name="real_estate_cma", task_id="cma-run")

            waiting_roles = {
                call.args[1].agent_role
                for call in mock_bus.publish.call_args_list
                if call.args[1].state == "waiting_on_agent"
            }
            assert "appraiser" in waiting_roles
            assert "report_writer" in waiting_roles
