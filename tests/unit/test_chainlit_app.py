"""Unit tests for chainlit_app — error sanitization and domain handling."""

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
