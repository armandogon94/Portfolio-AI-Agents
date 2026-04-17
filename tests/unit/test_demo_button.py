"""Chainlit demo action + scenarios yaml integration (slice-28)."""

import pytest


@pytest.mark.unit
class TestDemoButton:
    def test_chainlit_exposes_run_demo_command(self):
        """The Chainlit app handles a '/demo' command that lists canned scenarios.

        Checks the module source to avoid importing Chainlit's runtime in
        a unit-test context (it spins up async websockets).
        """
        import pathlib

        src = pathlib.Path(__file__).resolve().parent.parent.parent / "src" / "chainlit_app.py"
        body = src.read_text()
        assert "/demo" in body
        assert "DEMO_MODE" in body or "demo_mode" in body
