"""Run test cases through the harness with configurable config/test list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .config import HarnessConfig
from dataclasses import asdict, is_dataclass
from .runner import HarnessRunner

DEFAULT_CONFIG = Path(__file__).with_name("example_stub_config.toml")
DEFAULT_CASES = Path(__file__).resolve().parents[1] / "test_cases_refactored.json"


def load_cases(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if limit is None:
        return cases
    return cases[:limit]


def run_cases(config_path: Path, cases_path: Path, limit: int | None = None) -> Iterable[tuple[str, dict[str, Any]]]:
    config = HarnessConfig.load(config_path)
    runner = HarnessRunner(config=config)
    cases = load_cases(cases_path, limit)
    for case in cases:
        yield case["name"], runner.run_test_case(case)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run harness test cases")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--print-transcript", action="store_true", help="Print full transcript JSON for each case")
    args = parser.parse_args()

    for name, result in run_cases(args.config, args.cases, args.limit):
        print(f"=== {name} ===")
        print(f"Assistant: {result['assistant_text']}")
        print(f"Judgment: {result['judgment']}")
        print(f"Interrogation: {result['interrogation']}")
        if args.print_transcript:
            t = result.get("transcript")
            if is_dataclass(t):
                t = asdict(t)
            print("Transcript:")
            print(json.dumps(t, indent=2))
        print()


if __name__ == "__main__":
    main()
