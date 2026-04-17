"""Demo harness — deterministic pitch mode (slice-28, DEC-25).

Public helpers:
  * ``load_scenarios()`` — dict of scenario name → {workflow, topic, …}
  * ``SCENARIOS_ROOT`` — path to ``src/demo/scenarios.yaml``
  * ``FIXTURES_ROOT`` — directory holding per-scenario fixture files

The :class:`FakeLLM` (see ``fake_llm.py``) returns canned completions so
a live demo is byte-for-byte reproducible regardless of Ollama weather.
"""

from __future__ import annotations

from pathlib import Path

import yaml

SCENARIOS_ROOT = Path(__file__).parent / "scenarios.yaml"
FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def load_scenarios() -> dict[str, dict]:
    """Read ``src/demo/scenarios.yaml`` and return the scenario dict."""
    if not SCENARIOS_ROOT.exists():
        raise FileNotFoundError(f"Demo scenarios file missing: {SCENARIOS_ROOT}")
    with open(SCENARIOS_ROOT) as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError("scenarios.yaml must be a top-level mapping")
    return data
