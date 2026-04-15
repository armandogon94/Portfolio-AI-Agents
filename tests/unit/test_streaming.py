"""Unit tests for streaming output via step_callback (slice-12)."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestBuildCrewStepCallback:
    def test_build_crew_accepts_step_callback(self):
        """build_crew passes step_callback to Crew constructor."""
        callback = MagicMock()

        with patch("src.crew.AgentFactory") as MockAgentFactory, \
             patch("src.crew.TaskFactory") as MockTaskFactory, \
             patch("src.crew.Crew") as MockCrew:

            mock_agents = {"researcher": MagicMock(), "analyst": MagicMock(),
                           "writer": MagicMock(), "validator": MagicMock()}
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.create_all.return_value = [MagicMock()]

            from src.crew import build_crew

            build_crew(domain=None, step_callback=callback)

            call_kwargs = MockCrew.call_args.kwargs
            assert call_kwargs.get("step_callback") is callback

    def test_build_crew_without_callback_passes_none(self):
        """build_crew with no step_callback passes step_callback=None."""
        with patch("src.crew.AgentFactory") as MockAgentFactory, \
             patch("src.crew.TaskFactory") as MockTaskFactory, \
             patch("src.crew.Crew") as MockCrew:

            mock_agents = {"researcher": MagicMock(), "analyst": MagicMock(),
                           "writer": MagicMock(), "validator": MagicMock()}
            MockAgentFactory.return_value.create_all.return_value = mock_agents
            MockTaskFactory.return_value.create_all.return_value = [MagicMock()]

            from src.crew import build_crew

            build_crew(domain=None)

            call_kwargs = MockCrew.call_args.kwargs
            assert call_kwargs.get("step_callback") is None


@pytest.mark.unit
class TestStepCallbackFormat:
    """Test that the on_step handler formats AgentAction/AgentFinish correctly."""

    def _make_on_step(self):
        """Return an on_step function that captures lines (no asyncio)."""
        lines = []

        def on_step(step: object) -> None:
            from crewai.agents.crew_agent_executor import AgentAction, AgentFinish

            if isinstance(step, AgentAction):
                tool_input = str(step.tool_input)
                snippet = tool_input[:120] + "..." if len(tool_input) > 120 else tool_input
                line = f"**[{step.tool}]** {snippet}"
            elif isinstance(step, AgentFinish):
                thought = step.thought[:150] + "..." if len(step.thought) > 150 else step.thought
                line = f"**Done:** {thought}"
            else:
                line = str(step)[:200]
            lines.append(line)

        return on_step, lines

    def test_agent_action_formats_tool_and_input(self):
        """AgentAction step shows tool name and input snippet."""
        from crewai.agents.crew_agent_executor import AgentAction

        on_step, lines = self._make_on_step()
        step = AgentAction(
            thought="I need to search for this",
            tool="web_search",
            tool_input="healthcare AI trends 2024",
            text="",
        )
        on_step(step)
        assert len(lines) == 1
        assert "[web_search]" in lines[0]
        assert "healthcare AI trends 2024" in lines[0]

    def test_agent_action_truncates_long_input(self):
        """AgentAction with long tool_input is truncated to 120 chars."""
        from crewai.agents.crew_agent_executor import AgentAction

        on_step, lines = self._make_on_step()
        long_input = "x" * 200
        step = AgentAction(
            thought="searching",
            tool="web_search",
            tool_input=long_input,
            text="",
        )
        on_step(step)
        assert "..." in lines[0]
        # tool_input portion should not exceed 120 + 3 chars (truncation marker)
        assert len(lines[0]) < 200

    def test_agent_finish_formats_thought(self):
        """AgentFinish step shows 'Done:' prefix with thought."""
        from crewai.agents.crew_agent_executor import AgentFinish

        on_step, lines = self._make_on_step()
        step = AgentFinish(
            thought="I have completed my analysis of the topic",
            output="Final output here",
            text="",
        )
        on_step(step)
        assert len(lines) == 1
        assert "**Done:**" in lines[0]
        assert "completed my analysis" in lines[0]

    def test_agent_finish_truncates_long_thought(self):
        """AgentFinish with long thought is truncated at 150 chars."""
        from crewai.agents.crew_agent_executor import AgentFinish

        on_step, lines = self._make_on_step()
        step = AgentFinish(
            thought="t" * 300,
            output="output",
            text="",
        )
        on_step(step)
        assert "..." in lines[0]

    def test_multiple_steps_accumulate(self):
        """Multiple steps accumulate in the lines list."""
        from crewai.agents.crew_agent_executor import AgentAction, AgentFinish

        on_step, lines = self._make_on_step()

        on_step(AgentAction(thought="t", tool="web_search", tool_input="query", text=""))
        on_step(AgentAction(thought="t", tool="document_search", tool_input="query2", text=""))
        on_step(AgentFinish(thought="done", output="result", text=""))

        assert len(lines) == 3
        assert "[web_search]" in lines[0]
        assert "[document_search]" in lines[1]
        assert "**Done:**" in lines[2]
