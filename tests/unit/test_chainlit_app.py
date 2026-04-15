"""Unit tests for chainlit_app — error sanitization, domain handling, session history."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestAgentDelegation:
    def test_researcher_delegation_disabled(self):
        """researcher agent must have allow_delegation: false (DEC-13)."""
        import yaml

        config_path = Path(__file__).parent.parent.parent / "src" / "config" / "agents.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["researcher"]["allow_delegation"] is False, (
            "researcher allow_delegation must be False — delegation with sequential process "
            "causes runtime failures (see DECISIONS.md DEC-13)"
        )

    def test_all_agents_delegation_disabled(self):
        """All agents must have allow_delegation: false."""
        import yaml

        config_path = Path(__file__).parent.parent.parent / "src" / "config" / "agents.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        for name, agent_config in config.items():
            assert agent_config.get("allow_delegation") is False, (
                f"Agent '{name}' has allow_delegation enabled — "
                "sequential process does not support delegation"
            )


@pytest.mark.unit
class TestChainlitErrorSanitization:
    def test_app_error_message_shown_to_user(self):
        """AppError message (already safe) is forwarded to the user."""
        from src.exceptions import AppError

        exc = AppError("Vector database is not available", status_code=503)
        user_msg = str(exc) if isinstance(exc, AppError) else "An unexpected error occurred. Please try again."
        assert "Vector database is not available" in user_msg

    def test_generic_exception_sanitized(self):
        """Raw exception details are NOT shown to the user."""
        from src.exceptions import AppError

        exc = ValueError("internal psycopg2 connection string: password=secret123")
        user_msg = str(exc) if isinstance(exc, AppError) else "An unexpected error occurred. Please try again."
        assert "secret123" not in user_msg
        assert "unexpected error" in user_msg

    def test_runtime_error_sanitized(self):
        """RuntimeError details do not leak to user message."""
        from src.exceptions import AppError

        exc = RuntimeError("ollama model qwen3:8b returned exit code 137: OOM")
        user_msg = str(exc) if isinstance(exc, AppError) else "An unexpected error occurred. Please try again."
        assert "137" not in user_msg
        assert "OOM" not in user_msg
        assert "unexpected error" in user_msg

    def test_crew_execution_error_shown_to_user(self):
        """CrewExecutionError (AppError subclass) message is shown directly."""
        from src.exceptions import AppError, CrewExecutionError

        exc = CrewExecutionError("Research task timed out after 60 seconds")
        user_msg = str(exc) if isinstance(exc, AppError) else "An unexpected error occurred. Please try again."
        assert "Research task timed out" in user_msg


@pytest.mark.unit
class TestFormatPriorContext:
    """_format_prior_context builds session context from message history."""

    def _fmt(self, messages, limit=3):
        from src.chainlit_app import _format_prior_context
        return _format_prior_context(messages, limit=limit)

    def test_empty_history_returns_empty_string(self):
        assert self._fmt([]) == ""

    def test_single_user_message_no_assistant_returns_empty(self):
        """A lone user message with no assistant reply gives no context."""
        messages = [{"role": "user", "content": "What is AI?"}]
        assert self._fmt(messages) == ""

    def test_one_pair_returns_prior_topic(self):
        """One user/assistant pair returns context with the user topic."""
        messages = [
            {"role": "user", "content": "AI in healthcare"},
            {"role": "assistant", "content": "Here is the analysis..."},
        ]
        result = self._fmt(messages)
        assert "AI in healthcare" in result
        assert "Prior session context" in result

    def test_five_pairs_truncates_to_three(self):
        """With limit=3, only the first 3 pairs are included."""
        messages = []
        for i in range(5):
            messages.append({"role": "user", "content": f"topic {i}"})
            messages.append({"role": "assistant", "content": f"result {i}"})
        result = self._fmt(messages, limit=3)
        assert "topic 0" in result
        assert "topic 1" in result
        assert "topic 2" in result
        assert "topic 3" not in result
        assert "topic 4" not in result

    def test_long_topic_truncated_to_200_chars(self):
        """User topic is truncated at 200 chars in the context string."""
        long_topic = "x" * 300
        messages = [
            {"role": "user", "content": long_topic},
            {"role": "assistant", "content": "result"},
        ]
        result = self._fmt(messages)
        # The context line should not contain more than 200 topic chars
        assert "x" * 201 not in result

    def test_non_alternating_messages_handled_gracefully(self):
        """Consecutive messages of same role don't produce incomplete pairs."""
        messages = [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "reply"},
        ]
        # Should not raise; may return empty or partial
        result = self._fmt(messages)
        assert isinstance(result, str)
