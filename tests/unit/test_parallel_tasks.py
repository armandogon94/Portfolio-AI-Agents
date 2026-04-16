"""Unit tests for parallel tasks within a workflow (slice-22, DEC-20)."""

from unittest.mock import MagicMock, patch

import pytest

from src.workflows import _REGISTRY, register_workflow
from src.workflows.base import Workflow


@pytest.fixture
def parallel_workflow():
    wf = Workflow(
        name="test_parallel_for_unit",
        description="two researchers fan into one writer",
        agent_roles=["researcher", "analyst", "writer"],
        task_names=["research", "analysis", "writing"],
        process="sequential",
        # research and analysis run concurrently; writing waits on both.
        parallel_tasks=[["research", "analysis"]],
    )
    register_workflow(wf)
    yield wf
    _REGISTRY.pop(wf.name, None)


def _stub_factories(MockAgentFactory, MockTaskFactory):
    mock_agents = {
        "researcher": MagicMock(name="researcher"),
        "analyst": MagicMock(name="analyst"),
        "writer": MagicMock(name="writer"),
    }
    for agent in mock_agents.values():
        agent.allow_delegation = False
    MockAgentFactory.return_value.create_all.return_value = mock_agents
    MockTaskFactory.return_value.tasks_config = {
        "research": {"agent": "researcher"},
        "analysis": {"agent": "analyst"},
        "writing": {"agent": "writer"},
    }
    MockTaskFactory.return_value.create.side_effect = (
        lambda task_name, agent, async_execution=False: MagicMock(
            name=f"task_{task_name}", async_execution=async_execution
        )
    )
    return mock_agents


@pytest.mark.unit
class TestParallelTasks:
    def test_parallel_group_tasks_get_async_execution_true(self, parallel_workflow):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
        ):
            _stub_factories(MockAgentFactory, MockTaskFactory)

            from src.crew import build_crew

            build_crew(workflow_name=parallel_workflow.name)

            calls = MockTaskFactory.return_value.create.call_args_list
            async_by_name = {
                c.args[0]: c.kwargs.get("async_execution", False) for c in calls
            }
            assert async_by_name == {
                "research": True,
                "analysis": True,
                "writing": False,
            }

    def test_state_bus_emits_waiting_on_agent_for_downstream_tasks(
        self, parallel_workflow
    ):
        """Tasks after a parallel group are telegraphed to the state bus
        as ``waiting_on_agent`` so the live dashboard can render the
        dependency before the predecessors finish."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
            patch("src.crew.get_state_bus") as mock_get_bus,
        ):
            _stub_factories(MockAgentFactory, MockTaskFactory)

            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus

            from src.crew import build_crew

            build_crew(workflow_name=parallel_workflow.name, task_id="run-42")

            published = [call.args for call in mock_bus.publish.call_args_list]
            waiting_events = [
                event
                for (task_id, event) in published
                if event.state == "waiting_on_agent"
            ]
            assert len(waiting_events) >= 1, "writing should be telegraphed as waiting"
            # The writing task waits on the researcher/analyst parallel group.
            assert any(e.agent_role == "writer" for e in waiting_events)

    def test_no_parallel_tasks_emits_no_waiting_events(self):
        """Sequential workflows (no parallel_tasks) must not emit waiting_on_agent."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
            patch("src.crew.get_state_bus") as mock_get_bus,
        ):
            mock_agents = {
                "researcher": MagicMock(name="researcher"),
                "analyst": MagicMock(name="analyst"),
                "writer": MagicMock(name="writer"),
                "validator": MagicMock(name="validator"),
            }
            for a in mock_agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.tasks_config = {
                "research": {"agent": "researcher"},
                "analysis": {"agent": "analyst"},
                "writing": {"agent": "writer"},
                "validation": {"agent": "validator"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(name=f"t_{t}")
            )

            mock_bus = MagicMock()
            mock_get_bus.return_value = mock_bus

            from src.crew import build_crew

            build_crew(workflow_name="research_report", task_id="run-seq")

            waiting = [
                call.args[1]
                for call in mock_bus.publish.call_args_list
                if call.args[1].state == "waiting_on_agent"
            ]
            assert waiting == []
