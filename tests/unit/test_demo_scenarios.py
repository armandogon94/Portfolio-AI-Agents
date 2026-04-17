"""Demo-scenario registry + CLI tests (slice-28)."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.unit
class TestDemoScenarios:
    def test_scenarios_yaml_has_all_expected_scenarios(self):
        from src.demo import load_scenarios

        scenarios = load_scenarios()
        expected = {
            "lead-qualifier-acme",
            "sdr-outreach-cto",
            "support-triage-refund",
            "meeting-prep-monday",
            "content-pipeline-blog",
            "cma-123-main",
            "receptionist-book-table",
        }
        assert expected <= set(scenarios), (
            f"Missing: {expected - set(scenarios)}"
        )
        for name, entry in scenarios.items():
            assert "workflow" in entry, f"{name} missing workflow field"
            assert "topic" in entry, f"{name} missing topic field"

    def test_demo_cli_list_prints_all_scenarios(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "demo.py"), "--list"],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr
        stdout = result.stdout
        for name in (
            "lead-qualifier-acme",
            "sdr-outreach-cto",
            "support-triage-refund",
            "meeting-prep-monday",
            "content-pipeline-blog",
            "cma-123-main",
            "receptionist-book-table",
        ):
            assert name in stdout
