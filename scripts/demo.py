#!/usr/bin/env python
"""Deterministic demo harness CLI (slice-28).

Examples:
    scripts/demo.py --list
    scripts/demo.py --scenario lead-qualifier-acme
    scripts/demo.py --scenario lead-qualifier-acme --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `src` importable when run as a script.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic demo scenario using pre-recorded fixtures."
    )
    parser.add_argument("--scenario", help="Scenario name (see --list).")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print available scenarios and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the scenario's fixtures without emitting content.",
    )
    args = parser.parse_args(argv)

    from src.demo import load_scenarios
    from src.demo.fake_llm import FakeLLM

    scenarios = load_scenarios()

    if args.list:
        width = max(len(k) for k in scenarios)
        print("Available demo scenarios:\n")
        for name, entry in sorted(scenarios.items()):
            desc = entry.get("description", "")
            print(f"  {name.ljust(width)}  {desc}")
        return 0

    if not args.scenario:
        parser.error("--scenario or --list is required")

    if args.scenario not in scenarios:
        print(
            f"error: unknown scenario {args.scenario!r}. "
            f"See `{sys.argv[0]} --list`.",
            file=sys.stderr,
        )
        return 2

    entry = scenarios[args.scenario]
    try:
        llm = FakeLLM(scenario=args.scenario)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    print(f"Scenario: {args.scenario}")
    print(f"Workflow: {entry.get('workflow', '?')}")
    print(f"Domain:   {entry.get('domain', 'general')}")
    print(f"Topic:    {entry.get('topic', '')}")
    print(f"Fixtures: {len(llm.fixture_roles)} ({', '.join(llm.fixture_roles)})")
    print()

    if args.dry_run:
        print("[dry-run] fixtures are valid; skipping content emission.")
        return 0

    for role in llm.fixture_roles:
        content = llm.call()
        print(f"---- {role} ----")
        print(content.rstrip())
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
