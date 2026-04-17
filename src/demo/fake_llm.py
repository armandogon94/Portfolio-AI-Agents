"""FakeLLM — deterministic LLM stub for DEMO_MODE (slice-28, DEC-25).

Fixtures live in ``src/demo/fixtures/<scenario>/<N>-<agent_role>.md``.
``.call()`` returns the next fixture in order; if the crew requests more
completions than fixtures provide, we raise loudly so a broken demo
never silently falls back to a live LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.demo import FIXTURES_ROOT

_FIXTURE_PATTERN = re.compile(r"^(\d+)-(.+)\.md$")


@dataclass
class _Fixture:
    order: int
    role: str
    content: str


@dataclass
class FakeLLM:
    """A CrewAI-compatible LLM stub that serves pre-recorded outputs.

    The only method CrewAI cares about is :meth:`call`; we also expose
    ``invoke`` and ``__call__`` as aliases so LiteLLM-style wrappers work.
    """

    scenario: str
    fixtures_dir: Path | None = None
    _fixtures: list[_Fixture] = field(default_factory=list, init=False, repr=False)
    _call_count: int = field(default=0, init=False)

    # CrewAI expects a `model` attribute for logging/telemetry.
    model: str = "fake/demo"

    def __post_init__(self) -> None:
        directory = self.fixtures_dir or (FIXTURES_ROOT / self.scenario)
        if not directory.exists():
            raise FileNotFoundError(
                f"FakeLLM: fixtures directory for '{self.scenario}' not found at {directory}"
            )
        entries: list[_Fixture] = []
        for path in sorted(directory.iterdir()):
            match = _FIXTURE_PATTERN.match(path.name)
            if not match:
                continue
            entries.append(
                _Fixture(
                    order=int(match.group(1)),
                    role=match.group(2),
                    content=path.read_text(),
                )
            )
        entries.sort(key=lambda f: f.order)
        if not entries:
            raise RuntimeError(
                f"FakeLLM: no fixtures found in {directory}. Expected files like '1-researcher.md'."
            )
        self._fixtures = entries

    def call(self, *args: Any, **kwargs: Any) -> str:
        """Return the next fixture.

        CrewAI calls this as ``llm.call(messages, tools=..., callbacks=...)``;
        we ignore the arguments because the output is predetermined.
        """
        if self._call_count >= len(self._fixtures):
            raise RuntimeError(
                f"FakeLLM scenario '{self.scenario}' exhausted: "
                f"call #{self._call_count + 1} requested but only "
                f"{len(self._fixtures)} fixtures exist. "
                f"Add more fixtures or flip DEMO_MODE=false."
            )
        fixture = self._fixtures[self._call_count]
        self._call_count += 1
        return fixture.content

    # Aliases — different CrewAI versions / wrappers may use any of these.
    invoke = call

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        return self.call(*args, **kwargs)

    @property
    def fixture_roles(self) -> list[str]:
        """Ordered list of agent roles the scenario serves."""
        return [f.role for f in self._fixtures]
