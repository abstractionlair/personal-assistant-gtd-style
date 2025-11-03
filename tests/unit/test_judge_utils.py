import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judge_utils import parse_judge_verdict


@pytest.mark.parametrize(
    "payload, expected",
    [
        ('{"pass": true, "reasoning": "ok"}', {"pass": True, "reasoning": "ok"}),
        ('  {"pass": false, "reasoning": "needs more"}  ', {"pass": False, "reasoning": "needs more"}),
    ],
)
def test_parse_judge_verdict_accepts_bare_json(payload, expected):
    verdict = parse_judge_verdict(payload)
    assert verdict == expected


def test_parse_judge_verdict_handles_markdown_fence():
    payload = """```json
{
  "pass": true,
  "reasoning": "done"
}
```"""
    verdict = parse_judge_verdict(payload)
    assert verdict == {"pass": True, "reasoning": "done"}


def test_parse_judge_verdict_handles_text_around_fence():
    payload = """Here you go:

```json
{"pass": false, "reasoning": "missing criteria"}
```

Thanks!"""
    verdict = parse_judge_verdict(payload)
    assert verdict == {"pass": False, "reasoning": "missing criteria"}


def test_parse_judge_verdict_with_text_before_json():
    payload = "Verdict: {\"pass\": true, \"reasoning\": \"satisfied\"}"
    verdict = parse_judge_verdict(payload)
    assert verdict == {"pass": True, "reasoning": "satisfied"}


def test_parse_judge_verdict_returns_none_for_invalid_json():
    payload = "pass: true, reasoning: yes"
    verdict = parse_judge_verdict(payload)
    assert verdict is None
