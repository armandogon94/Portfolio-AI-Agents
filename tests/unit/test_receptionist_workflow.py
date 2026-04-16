"""Receptionist workflow test (slice-26)."""

import pytest


@pytest.mark.unit
class TestReceptionistWorkflow:
    def test_registered_sequential_with_three_agents(self):
        from src.workflows import get_workflow

        wf = get_workflow("receptionist")
        assert wf.name == "receptionist"
        assert wf.process == "sequential"
        assert wf.agent_roles == ["intake_agent", "caller_agent", "summary_agent"]
        assert wf.task_names == ["voice_intake", "voice_call", "voice_summary"]
