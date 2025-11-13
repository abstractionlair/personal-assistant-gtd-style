"""Run the harness runner in stub mode using example config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import HarnessConfig
from .runner import HarnessRunner

DEFAULT_CONFIG = Path(__file__).with_name("example_stub_config.toml")
TEST_CASES = Path(__file__).resolve().parents[1] / "test_cases_refactored.json"


def load_test_cases(limit: int | None = None):
    data = json.loads(TEST_CASES.read_text(encoding="utf-8"))
    if limit is not None:
        return data[:limit]
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Run harness runner in stub mode")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to harness config (TOML/JSON)")
    parser.add_argument("--limit", type=int, default=1, help="Number of cases to run")
    args = parser.parse_args()

    config = HarnessConfig.load(args.config)
    runner = HarnessRunner(config=config)
    cases = load_test_cases(limit=args.limit)
    for case in cases:
        result = runner.run_test_case(case)
        print(f"Test {case['name']}: {result['judgment']['reason']}")
        print(f"Assistant: {result['assistant_text']}")
        print(f"Interrogation: {result['interrogation']}")


if __name__ == "__main__":
    main()
