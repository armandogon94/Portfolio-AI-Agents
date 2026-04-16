"""Unit tests for hierarchical crew process (slice-22, DEC-19).

Tests that hierarchical workflows:
  - Build with a manager_agent kwarg on Crew
  - Enable allow_delegation=True on non-manager agents
  - Keep sequential workflows at allow_delegation=False (DEC-13 preserved)
  - Raise ValidationError when manager_agent is missing or unknown
"""

from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import ValidationError
from src.workflows import _REGISTRY, register_workflow
from src.workflows.base import Workflow


@pytest.fixture
def hierarchical_workflow():
    wf = Workflow(
        name="test_hierarchical_for_unit",
        description="hierarchical test workflow",
        agent_roles=["researcher", "analyst", "writer", "validator"],
        task_names=["research", "analysis", "writing", "validation"],
        process="hierarchical",
        manager_agent="validator",  # arbitrary manager role for the test
    )
    register_workflow(wf)
    yield wf
    _REGISTRY.pop(wf.name, None)


@pytest.fixture
def missing_manager_workflow():
    wf = Workflow(
        name="test_hierarchical_missing_mgr",
        description="hierarchical without manager",
        agent_roles=["researcher", "analyst"],
        task_names=["research"],
        process="hierarchical",
        manager_agent=None,  # invalid
    )
    register_workflow(wf)
    yield wf
    _REGISTRY.pop(wf.name, None)


def _stub_factories(MockAgentFactory, MockTaskFactory):
    mock_agents = {
        "researcher": MagicMock(name="researcher"),
        "analyst": MagicMock(name="analyst"),
        "writer": MagicMock(name="writer"),
        "validator": MagicMock(name="validator"),
    }
    # allow_delegation starts False (DEC-13 default from AgentFactory)
    for agent in mock_agents.values():
        agent.allow_delegation = False
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
    return mock_agents


@pytest.mark.unit
class TestHierarchicalProcess:
    def test_hierarchical_passes_manager_agent_to_crew(self, hierarchical_workflow):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            mock_agents = _stub_factories(MockAgentFactory, MockTaskFactory)

            from src.crew import build_crew

            build_crew(workflow_name=hierarchical_workflow.name)

            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "hierarchical"
            assert kwargs["manager_agent"] is mock_agents["validator"]
            # Manager must NOT be in the `agents` list (CrewAI enforces this).
            assert mock_agents["validator"] not in kwargs["agents"]

    def test_hierarchical_enables_delegation_on_non_manager_agents(
        self, hierarchical_workflow
    ):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
        ):
            mock_agents = _stub_factories(MockAgentFactory, MockTaskFactory)

            from src.crew import build_crew

            build_crew(workflow_name=hierarchical_workflow.name)

            # Non-manager agents have delegation enabled under hierarchical.
            assert mock_agents["researcher"].allow_delegation is True
            assert mock_agents["analyst"].allow_delegation is True
            assert mock_agents["writer"].allow_delegation is True

    def test_sequential_workflow_keeps_delegation_off(self):
        """DEC-13 stands: sequential workflows must not enable delegation."""
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
        ):
            mock_agents = _stub_factories(MockAgentFactory, MockTaskFactory)

            from src.crew import build_crew

            build_crew(workflow_name="research_report")

            for role, agent in mock_agents.items():
                assert (
                    agent.allow_delegation is False
                ), f"{role} should not have delegation enabled in sequential workflow"

    def test_hierarchical_without_manager_raises(self, missing_manager_workflow):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew"),
        ):
            _stub_factories(MockAgentFactory, MockTaskFactory)

            from src.crew import build_crew

            with pytest.raises(ValidationError, match="manager"):
                build_crew(workflow_name=missing_manager_workflow.name)

    def test_hierarchical_unknown_manager_raises(self):
        wf = Workflow(
            name="test_hierarchical_bad_manager",
            description="manager role not in agent_roles",
            agent_roles=["researcher", "analyst"],
            task_names=["research"],
            process="hierarchical",
            manager_agent="nonexistent_role",
        )
        register_workflow(wf)
        try:
            with (
                patch("src.crew.AgentFactory") as MockAgentFactory,
                patch("src.crew.TaskFactory") as MockTaskFactory,
                patch("src.crew.Crew"),
            ):
                _stub_factories(MockAgentFactory, MockTaskFactory)

                from src.crew import build_crew

                with pytest.raises(ValidationError, match="manager"):
                    build_crew(workflow_name=wf.name)
        finally:
            _REGISTRY.pop(wf.name, None)
