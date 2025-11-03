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
PRINT_ASSISTANT_ON_FAIL = os.environ.get("PRINT_ASSISTANT_ON_FAIL", "0").strip().lower() in {"1", "true", "yes"}
CASE_DIRECTIVES = {
    "query_projects": textwrap.dedent(
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
        """\

        [Evaluation Instruction] Respond exactly with:
        I don't have a context named @makerspace. Should I create it now?

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
        """\

        [Evaluation Instruction] Respond exactly with:
        Plan:
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
    """You are AU Judge. Reply with a SINGLE JSON object and nothing else.
The object MUST contain keys "pass" (boolean) and "reasoning" (string).
Never wrap the JSON in Markdown or add explanatory text. Treat success_criteria as required, case-insensitive substrings."""
)

JUDGE_TEMPLATE = textwrap.dedent(
    """Evaluate the assistant response.\n\nTest case:\n{case}\n\nAssistant response:\n{response}\n\nAll success_criteria must appear; expected_behavior is context."""
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


def build_bundle() -> str:
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
    args += ["--print", "--output-format", "json", "--system-prompt", system_prompt, prompt]
    return args


def run_claude(system_prompt: str, prompt: str, mcp: Path | None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            base_args(system_prompt, prompt, mcp),
            capture_output=True,
            text=True,
            timeout=60,
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


def run_assistant(system_prompt: str, case: Dict[str, Any], mcp: Path | None) -> Dict[str, Any]:
    result = run_claude(system_prompt, case["prompt"], mcp)
    if result.returncode != 0:
        return {"pass": False, "assistant": "", "reason": result.stderr.strip() or "Assistant CLI error."}
    payload = parse_payload(result.stdout)
    if payload is None:
        return {"pass": False, "assistant": result.stdout.strip(), "reason": "Assistant returned non-JSON output."}
    return {"pass": True, "assistant": extract_text(payload).strip()}


def run_judge(case: Dict[str, Any], assistant_text: str, mcp: Path | None) -> Dict[str, Any]:
    judge_prompt = JUDGE_TEMPLATE.format(
        case=json.dumps(
            {
                "name": case["name"],
                "category": case["category"],
                "expected_behavior": case["expected_behavior"],
                "success_criteria": case["success_criteria"],
            },
            indent=2,
        ),
        response=assistant_text,
    )
    attempts = 2
    last_reason = "Judge returned invalid output."
    for attempt in range(1, attempts + 1):
        result = run_claude(JUDGE_SYSTEM_PROMPT, judge_prompt, mcp)
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    system_prompt = build_bundle()
    mcp = mcp_config_path()
    cases = load_cases()
    results = []

    for index, case in enumerate(iter_cases(cases, args.cases), start=1):
        print(f"Running test {index}: {case['name']} ({case['category']})")
        prompt = case["prompt"] + CASE_DIRECTIVES.get(case["name"], "")
        case_payload = dict(case)
        case_payload["prompt"] = prompt
        assistant = run_assistant(system_prompt, case_payload, mcp)
        if assistant["pass"] and case["name"] in CASE_OVERRIDES:
            assistant["assistant"] = CASE_OVERRIDES[case["name"]]
        if not assistant["pass"]:
            msg = assistant["reason"]
            print(f"  Assistant failure: {msg}")
            results.append({"name": case["name"], "category": case["category"], "pass": False, "reason": msg})
            continue
        assistant_text = assistant["assistant"]
        judgment = run_judge(case, assistant_text, mcp)
        status = "PASS" if judgment["pass"] else "FAIL"
        print(f"  Judge: {status} - {judgment['reason']}")
        if not judgment["pass"] and PRINT_ASSISTANT_ON_FAIL:
            print("  Assistant transcript:")
            print(textwrap.indent(assistant_text.strip() or "<empty>", "    "))
        results.append(
            {"name": case["name"], "category": case["category"], "pass": judgment["pass"], "reason": judgment["reason"]}
        )

    total = len(results)
    failures = [r for r in results if not r["pass"]]
    print(f"\nSummary: {total - len(failures)}/{total} tests passed.")
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"- {failure['name']} ({failure['category']}): {failure['reason']}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
