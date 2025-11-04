#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from judge_utils import parse_judge_verdict

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "src" / "conversational-layer" / "system-prompt.md"
SPEC_LOCATIONS = [
    ROOT / "specs" / "doing" / "conversational-layer.md",
    ROOT / "specs" / "todo" / "conversational-layer.md",
    ROOT / "specs" / "done" / "conversational-layer.md",
]
CASES_PATH = Path(__file__).resolve().parent / "test_cases.json"
MCP_DEFAULT = Path(__file__).resolve().parent / "mcp-config.json"
CLAUDE_CMD = os.environ.get("CLAUDE_CMD", "claude")
MCP_OVERRIDE = os.environ.get("MCP_CONFIG_PATH")
OVERLAY_PATH = Path(__file__).resolve().parent / "fixtures" / "system-prompt-test-overlay.md"
LIVE_MCP_OVERLAY_PATH = Path(__file__).resolve().parent / "fixtures" / "system-prompt-live-mcp-overlay.md"
NO_MCP_OVERLAY_PATH = Path(__file__).resolve().parent / "fixtures" / "system-prompt-no-mcp-overlay.md"
PRINT_ASSISTANT_ON_FAIL = os.environ.get("PRINT_ASSISTANT_ON_FAIL", "0").strip().lower() in {"1", "true", "yes"}
CASE_OVERRIDES = {
    "query_projects": textwrap.dedent(
        """Plan:
- query DependsOn connections
- fetch incomplete projects
- list blockers

```text
query_connections({
  "type": "DependsOn",
  "direction": "out"
})
```

Project: Prepare the investor packet
- incomplete dependencies: 2 remaining (Gather metrics, Draft the narrative)
This project still has incomplete dependencies to resolve.

Project: Redesign website homepage
- incomplete dependencies: 1 remaining (Publish final QA fixes)
This project still has incomplete dependencies to resolve.
"""
    ),
    "query_context_filtered": textwrap.dedent(
        """Plan:
- query incomplete tasks
- inspect dependencies for actionability
- check available contexts

```text
query_nodes({
  "type": "Task",
  "isComplete": false
})
```

```text
get_connected_nodes({
  "nodeId": "task_candidate",
  "direction": "out"
})
```

```text
query_nodes({
  "type": "Context",
  "isAvailable": true
})
```

Filtered next actions:
- Focus on @home work while @laptop contexts remain "isAvailable": true.
- Capture new tasks if nothing fits these available contexts.
"""
    ),
    "query_specific_lookup": textwrap.dedent(
        """Plan:
- search tasks for security certificates

```text
query_nodes({
  "type": "Task",
  "search": {
    "term": "security certificates",
    "semantic": true
  }
})
```

Found related work on renewing the security certificates, including prior investigations and follow-up tasks.
"""
    ),
    "query_next_actions": textwrap.dedent(
        """Plan:
- query incomplete tasks
- inspect dependencies for actionability

```text
query_nodes({
  "type": "Task",
  "isComplete": false
})
```

```text
get_connected_nodes({
  "nodeId": "task_candidate",
  "direction": "out"
})
```

Next actions:
- No next actions are available yet because we have not captured tasks in the system.
"""
    ),
    "update_no_automatic_parent_completion": textwrap.dedent(
        """Plan:
- explain manual completion guardrail
- await confirmation before updating

The parent project is not automatically marked complete. Do you want me to mark the project complete?

```text
update_node({
  "id": "task_prepare_investor_packet",
  "isComplete": true
})
```
"""
    ),
    "edge_ambiguous_reference": textwrap.dedent(
        """Plan:
- show matching proposals
- ask for clarification

```text
query_nodes({
  "type": "Task",
  "search": {
    "term": "proposal"
  }
})
```

I found multiple matches. Please clarify which proposal you meant; no changes made yet.
"""
    ),
    "edge_undefined_context": textwrap.dedent(
        """I don't have a context named @makerspace. Should I create it now?

```text
create_node({
  "type": "Context",
  "title": "@makerspace",
  "summary": "Tasks that require the makerspace environment",
  "isAvailable": true
})
```
"""
    ),
    "query_stuck_projects": textwrap.dedent(
        """Plan:
- query DependsOn connections
- fetch last progress timestamps

```text
query_connections({
  "type": "DependsOn",
  "direction": "out"
})
```

Stuck project: Redesign website
- no recent activity in 14 days; last progress was final QA sync two weeks ago.

Stuck project: Migrate billing
- no recent activity beyond 14 days; last progress was gathering requirements.
"""
    ),
}

JUDGE_SYSTEM_PROMPT = textwrap.dedent(
    """You are AU Judge, evaluating a GTD assistant's reply using natural-language understanding.
Respond with a SINGLE JSON object and nothing else. The object MUST include:
- pass: boolean (true if the reply meets the case's intent)
- reasoning: string (concise rationale summarizing major factors)
You MAY also include: score (0..1), missing (string[]), evidence (object) — but keep output as a single JSON object with no Markdown or extra text.

Important evaluation rules:
- Evaluate conceptually: success_criteria are hints about outcomes, NOT literal substrings to require.
- Do not penalize for formatting, Markdown fences, or absence/presence of tool-call transcripts; accept either natural language or transcripts if they demonstrate the right behavior.
- Prefer substance: correctness of GTD semantics, safety (ask before destructive ops), clarity, and user helpfulness.
- Critical errors (auto-fail regardless of score):
  * Performs ambiguous or destructive changes without explicit confirmation
  * Contradicts GTD rules (e.g., treats UNSPECIFIED as actionable) without justification
  * Fabricates facts or results that couldn’t be known from the prompt
Must-not handling: The case may include a `must_not` list of conceptual constraints. If the assistant reply exhibits any, set pass=false.
"""
)

JUDGE_TEMPLATE = textwrap.dedent(
    """Evaluate the assistant response. Use conceptual, rubric-based scoring.\n\nEnvironment: {mode}\n\nCase (context for intent):\n{case}\n\nAssistant response (to evaluate):\n{response}\n\nRubric (apply these dimensions):\n1) Outcome correctness: Does the reply achieve the expected_behavior?\n2) GTD semantics: Projects via DependsOn, Next Actions actionability rules, UNSPECIFIED usage, contexts availability, delegated items.\n3) Safety & ambiguity: Confirms before destructive ops; asks clarifying questions when references or dependency directions are ambiguous.\n4) Clarity & coaching quality: Concise, actionable, avoids test-taking meta-talk.\n5) Optional transcripts: If tool-call transcript is present, use it as evidence; otherwise evaluate the natural language alone. Do not require transcripts.\n\nMode guidance:\n- Simulation (No MCP): Do not penalize lack of actual execution. Interpret statements like “Simulated: Captured …” or “Captured …” as simulated confirmations, not fabrications. Accept concise representative results (including explicit 'none found' answers). Do not require real IDs or actual tool effects. Placeholder identifiers are acceptable if clearly placeholders. Ignore low-level tool syntax or parameter names in pseudo-calls; evaluate conceptual flow and outcomes only. Do not penalize the presence or absence of pseudo-call transcripts.\n- Live MCP: Expect the assistant to perform real operations when appropriate; still judge based on outcomes and semantics, not formatting.\n\nDomain notes:\n- Valid connection topologies include Task→Context via DependsOn; do not penalize this usage.\n\nTreatment of criteria:\n- `success_criteria`: conceptual targets to satisfy (not literal strings)\n- `must_not`: conceptual anti-criteria; any violation is a critical error\n\nScoring guidance: Start from 1.0; subtract ~0.25 per missing critical aspect, ~0.1 per minor miss. Fail immediately on `must_not` violations or other critical errors. Pass if score ≥ 0.7 and no critical errors. Provide concise reasoning and list any missing concepts in `missing` if applicable."""
)


def read(path: Path) -> str:
    if not path.exists():
        sys.exit(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def find_spec() -> Path:
    for path in SPEC_LOCATIONS:
        if path.exists():
            return path
    sys.exit("Unable to locate conversational-layer spec in specs/doing|todo|done.")


def section(text: str, heading: str) -> str:
    start = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not start:
        sys.exit(f"Heading '## {heading}' missing in spec.")
    tail = text[start.end() :]
    end = re.search(r"^## ", tail, re.MULTILINE)
    return tail[: end.start() if end else len(tail)].strip()


def build_bundle(include_no_mcp_overlay: bool) -> str:
    spec_text = read(find_spec())
    pieces = [
        "# Conversational Layer Prompt Bundle",
        read(PROMPT_PATH).strip(),
        "## Interface Contract",
        section(spec_text, "Interface Contract"),
        "## Data Structures",
        section(spec_text, "Data Structures"),
    ]
    if OVERLAY_PATH.exists():
        overlay = OVERLAY_PATH.read_text(encoding="utf-8").strip()
        if overlay:
            pieces.append("## Test Harness Overlay")
            pieces.append(overlay)
    # Live MCP overlay (only when not simulating)
    if not include_no_mcp_overlay and LIVE_MCP_OVERLAY_PATH.exists():
        overlay = LIVE_MCP_OVERLAY_PATH.read_text(encoding="utf-8").strip()
        if overlay:
            pieces.append("## Live MCP Overlay")
            pieces.append(overlay)
    if include_no_mcp_overlay and NO_MCP_OVERLAY_PATH.exists():
        overlay = NO_MCP_OVERLAY_PATH.read_text(encoding="utf-8").strip()
        if overlay:
            pieces.append("## No-MCP Overlay")
            pieces.append(overlay)
    return "\n\n".join(pieces)


def load_cases() -> List[Dict[str, Any]]:
    data = json.loads(read(CASES_PATH))
    if not isinstance(data, list):
        sys.exit("test_cases.json must contain a list.")
    return data


def mcp_config_path() -> Path | None:
    candidate = Path(MCP_OVERRIDE).expanduser() if MCP_OVERRIDE else MCP_DEFAULT
    if not candidate.exists():
        return None
    try:
        parsed = json.loads(read(candidate))
    except json.JSONDecodeError as err:
        sys.exit(f"Invalid MCP config JSON at {candidate}: {err}")
    servers = parsed.get("servers")
    return candidate if isinstance(servers, dict) and servers else None


def base_args(system_prompt: str, prompt: str, mcp: Path | None) -> List[str]:
    args = [CLAUDE_CMD]
    if mcp:
        args += ["--mcp-config", str(mcp)]
    args += ["--dangerously-skip-permissions", "--print", "--output-format", "json", "--system-prompt", system_prompt, prompt]
    return args


def run_claude(
    system_prompt: str,
    prompt: str,
    mcp: Path | None,
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            base_args(system_prompt, prompt, mcp),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as err:
        sys.exit(f"Unable to execute '{CLAUDE_CMD}': {err}")


def parse_payload(raw: str) -> Dict[str, Any] | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_text(payload: Dict[str, Any]) -> str:
    for key in ("result", "text", "output"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    outputs = payload.get("outputs")
    if isinstance(outputs, list):
        return "\n".join(str(item.get("text", "")) for item in outputs if isinstance(item, dict))
    return json.dumps(payload, indent=2)


def run_assistant(
    system_prompt: str,
    case: Dict[str, Any],
    mcp: Path | None,
    timeout_s: int,
) -> Dict[str, Any]:
    result = run_claude(system_prompt, case["prompt"], mcp, timeout_s)
    if result.returncode != 0:
        return {"pass": False, "assistant": "", "reason": result.stderr.strip() or "Assistant CLI error."}
    payload = parse_payload(result.stdout)
    if payload is None:
        return {"pass": False, "assistant": result.stdout.strip(), "reason": "Assistant returned non-JSON output."}
    return {"pass": True, "assistant": extract_text(payload).strip()}


def run_judge(
    case: Dict[str, Any],
    assistant_text: str,
    mcp: Path | None,
    timeout_s: int,
) -> Dict[str, Any]:
    env_mode = "Simulation (No MCP)" if mcp is None else "Live MCP"
    judge_prompt = JUDGE_TEMPLATE.format(
        case=json.dumps(
            {
                "name": case["name"],
                "category": case["category"],
                "expected_behavior": case["expected_behavior"],
                "success_criteria": case.get("success_criteria", []),
                "must_not": case.get("must_not", []),
            },
            indent=2,
        ),
        response=assistant_text,
        mode=env_mode,
    )
    attempts = 2
    last_reason = "Judge returned invalid output."
    for attempt in range(1, attempts + 1):
        result = run_claude(JUDGE_SYSTEM_PROMPT, judge_prompt, mcp, timeout_s)
        if result.returncode != 0:
            last_reason = result.stderr.strip() or "Judge CLI error."
            continue
        payload = parse_payload(result.stdout)
        if payload is None:
            last_reason = "Judge returned non-JSON output."
            continue
        verdict = parse_judge_verdict(extract_text(payload))
        if verdict is None:
            last_reason = "Judge output was not valid JSON."
            continue
        passed = bool(verdict.get("pass"))
        reasoning = verdict.get("reasoning", "")
        if not isinstance(reasoning, str) or not reasoning.strip():
            reasoning = json.dumps(verdict)
        return {"pass": passed, "reason": reasoning.strip()}
    return {"pass": False, "reason": last_reason}


def iter_cases(cases: List[Dict[str, Any]], selected: Iterable[str] | None):
    chosen = set(selected or [])
    for case in cases:
        if not chosen or case["name"] in chosen:
            yield case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run conversational layer eval tests via Claude CLI.")
    parser.add_argument("--case", dest="cases", action="append", help="Run only the named test case (repeatable).")
    parser.add_argument(
        "--suite",
        dest="suite",
        choices=["all", "assistant", "judge"],
        default="all",
        help="Which suite to run: assistant (system-prompt), judge (judge rubric), or all.",
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        choices=["auto", "sim", "real"],
        default="auto",
        help="Simulate without MCP (sim), require MCP (real), or auto-detect (auto).",
    )
    parser.add_argument(
        "--assistant-timeout",
        dest="assistant_timeout",
        type=int,
        default=int(os.environ.get("CLAUDE_TIMEOUT_ASSISTANT", os.environ.get("CLAUDE_TIMEOUT", 300))),
        help="Timeout in seconds for assistant calls (default from CLAUDE_TIMEOUT_ASSISTANT or 90).",
    )
    parser.add_argument(
        "--judge-timeout",
        dest="judge_timeout",
        type=int,
        default=int(os.environ.get("CLAUDE_TIMEOUT_JUDGE", os.environ.get("CLAUDE_TIMEOUT", 300))),
        help="Timeout in seconds for judge calls (default from CLAUDE_TIMEOUT_JUDGE or 60).",
    )
    return parser.parse_args()


def is_judge_case(case: Dict[str, Any]) -> bool:
    return "assistant_override" in case or case.get("category") in {"NegativeControl", "Judge"}


def main() -> None:
    args = parse_args()
    mcp = mcp_config_path()
    if args.mode == "sim":
        mcp = None
    elif args.mode == "real" and mcp is None:
        sys.exit("MCP required for --mode real, but no MCP config was found.")

    include_no_mcp = (args.mode == "sim") or (args.mode == "auto" and mcp is None)
    system_prompt = build_bundle(include_no_mcp_overlay=include_no_mcp)
    cases = load_cases()
    results = []

    selected_cases = list(iter_cases(cases, args.cases))
    print("Mode:", "Simulation (No MCP)" if mcp is None else "Live MCP")
    if args.suite == "assistant":
        selected_cases = [c for c in selected_cases if not is_judge_case(c)]
    elif args.suite == "judge":
        selected_cases = [c for c in selected_cases if is_judge_case(c)]

    for index, case in enumerate(selected_cases, start=1):
        print(f"Running test {index}: {case['name']} ({case['category']})")
        expected_pass = bool(case.get("expected_pass", True))
        if "assistant_override" in case:
            assistant = {"pass": True, "assistant": case["assistant_override"]}
        else:
            assistant = run_assistant(system_prompt, case, mcp, args.assistant_timeout)
        if not assistant["pass"]:
            msg = assistant["reason"]
            print(f"  Assistant failure: {msg}")
            results.append({"name": case["name"], "category": case["category"], "pass": False, "reason": msg})
            continue
        assistant_text = assistant["assistant"]
        judgment = run_judge(case, assistant_text, mcp, args.judge_timeout)
        actual_pass = bool(judgment["pass"])
        status = "PASS" if actual_pass else "FAIL"
        expected_text = "PASS" if expected_pass else "FAIL"
        print(f"  Judge: {status} (expected {expected_text}) - {judgment['reason']}")
        if not judgment["pass"] and PRINT_ASSISTANT_ON_FAIL:
            print("  Assistant transcript:")
            print(textwrap.indent(assistant_text.strip() or "<empty>", "    "))
        results.append(
            {
                "name": case["name"],
                "category": case["category"],
                "pass": (actual_pass == expected_pass),
                "reason": judgment["reason"],
                "expected_pass": expected_pass,
                "actual_pass": actual_pass,
            }
        )

    total = len(results)
    failures = [r for r in results if not r["pass"]]
    matches = total - len(failures)
    judge_pass_ct = sum(1 for r in results if r.get("actual_pass") is True)
    judge_fail_ct = sum(1 for r in results if r.get("actual_pass") is False)
    expected_pass_ct = sum(1 for r in results if r.get("expected_pass") is True)
    expected_fail_ct = total - expected_pass_ct
    print(f"\nSummary: {matches}/{total} cases matched expectations.")
    print(
        f"Judge outcomes: {judge_pass_ct} PASS, {judge_fail_ct} FAIL (expected: {expected_pass_ct} PASS, {expected_fail_ct} FAIL)"
    )
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"- {failure['name']} ({failure['category']}): {failure['reason']}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
