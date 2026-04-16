"""Unit tests for the WorkflowRegistry (slice-21, DEC-18)."""

import pytest


@pytest.mark.unit
class TestWorkflowRegistry:
    def test_register_and_get(self):
        from src.workflows import _REGISTRY, get_workflow, register_workflow
        from src.workflows.base import Workflow

        wf = Workflow(
            name="test_only_registry_registered_by_name",
            description="for tests",
            agent_roles=["researcher"],
            task_names=["research"],
        )
        try:
            register_workflow(wf)
            assert get_workflow(wf.name) is wf
        finally:
            _REGISTRY.pop(wf.name, None)

    def test_get_unknown_raises_keyerror(self):
        from src.workflows import get_workflow

        with pytest.raises(KeyError):
            get_workflow("definitely_not_a_real_workflow_name")

    def test_list_workflows_returns_registered(self):
        from src.workflows import list_workflows

        names = [w.name for w in list_workflows()]
        assert "research_report" in names

    def test_duplicate_registration_raises_valueerror(self):
        from src.workflows import _REGISTRY, register_workflow
        from src.workflows.base import Workflow

        wf = Workflow(
            name="test_only_duplicate",
            description="t",
            agent_roles=["researcher"],
            task_names=["research"],
        )
        try:
            register_workflow(wf)
            with pytest.raises(ValueError, match="already registered"):
                register_workflow(wf)
        finally:
            _REGISTRY.pop(wf.name, None)
