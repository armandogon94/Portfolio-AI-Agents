"""Support-triage workflow tests (slice-24).

Hierarchical: triage_manager delegates to kb_searcher, sentiment_analyst,
response_writer.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestSupportTriageWorkflow:
    def test_registered_as_hierarchical(self):
        from src.workflows import get_workflow

        wf = get_workflow("support_triage")
        assert wf.name == "support_triage"
        assert wf.process == "hierarchical"
        assert wf.manager_agent == "triage_manager"

    def test_agent_roles_and_task_order(self):
        from src.workflows import get_workflow

        wf = get_workflow("support_triage")
        assert wf.agent_roles == [
            "triage_manager",
            "kb_searcher",
            "sentiment_analyst",
            "response_writer",
        ]
        assert wf.task_names == [
            "triage_route",
            "kb_search",
            "sentiment_analyze",
            "response_draft",
        ]

    def test_build_crew_pops_manager_and_enables_delegation_on_specialists(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            agents = {
                "triage_manager": MagicMock(name="mgr"),
                "kb_searcher": MagicMock(name="kb"),
                "sentiment_analyst": MagicMock(name="sent"),
                "response_writer": MagicMock(name="rw"),
            }
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "triage_route": {"agent": "triage_manager"},
                "kb_search": {"agent": "kb_searcher"},
                "sentiment_analyze": {"agent": "sentiment_analyst"},
                "response_draft": {"agent": "response_writer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock(name=f"task_{t}")
            )

            from src.crew import build_crew

            build_crew(workflow_name="support_triage")

            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "hierarchical"
            # Manager is out of the agents list, passed via manager_agent kwarg.
            assert kwargs["manager_agent"] is agents["triage_manager"]
            assert agents["triage_manager"] not in kwargs["agents"]
            # Specialists get delegation enabled; manager remains untouched by
            # slice-22 code (CrewAI's _create_manager_agent flips it to True
            # at runtime, not us).
            assert agents["kb_searcher"].allow_delegation is True
            assert agents["sentiment_analyst"].allow_delegation is True
            assert agents["response_writer"].allow_delegation is True
            assert agents["triage_manager"].allow_delegation is False
