"""Content-pipeline workflow tests (slice-25).

Sequential 5-agent editorial: researcher -> outliner -> writer -> editor -> seo_optimizer.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestContentPipelineWorkflow:
    def test_registered_sequential(self):
        from src.workflows import get_workflow

        wf = get_workflow("content_pipeline")
        assert wf.name == "content_pipeline"
        assert wf.process == "sequential"
        assert wf.parallel_tasks is None

    def test_five_agents_in_editorial_order(self):
        from src.workflows import get_workflow

        wf = get_workflow("content_pipeline")
        assert wf.agent_roles == [
            "researcher",
            "outliner",
            "writer",
            "editor",
            "seo_optimizer",
        ]
        assert wf.task_names == [
            "research",
            "content_outline",
            "content_draft",
            "content_edit",
            "content_seo",
        ]

    def test_build_crew_produces_five_sequential_tasks(self):
        with (
            patch("src.crew.AgentFactory") as MockAgentFactory,
            patch("src.crew.TaskFactory") as MockTaskFactory,
            patch("src.crew.Crew") as MockCrew,
        ):
            agents = {
                n: MagicMock(name=n)
                for n in (
                    "researcher",
                    "outliner",
                    "writer",
                    "editor",
                    "seo_optimizer",
                )
            }
            for a in agents.values():
                a.allow_delegation = False
            MockAgentFactory.return_value.create_all.return_value = agents
            MockTaskFactory.return_value.tasks_config = {
                "research": {"agent": "researcher"},
                "content_outline": {"agent": "outliner"},
                "content_draft": {"agent": "writer"},
                "content_edit": {"agent": "editor"},
                "content_seo": {"agent": "seo_optimizer"},
            }
            MockTaskFactory.return_value.create.side_effect = (
                lambda t, a, async_execution=False: MagicMock()
            )

            from src.crew import build_crew

            build_crew(workflow_name="content_pipeline")

            call_names = [
                c.args[0]
                for c in MockTaskFactory.return_value.create.call_args_list
            ]
            assert call_names == [
                "research",
                "content_outline",
                "content_draft",
                "content_edit",
                "content_seo",
            ]
            for call in MockTaskFactory.return_value.create.call_args_list:
                assert call.kwargs.get("async_execution") is False

            kwargs = MockCrew.call_args.kwargs
            assert kwargs["process"].name == "sequential"
            assert len(kwargs["tasks"]) == 5
