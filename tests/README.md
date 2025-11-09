# Conversational Layer Test Philosophy (LLM-as-Judge)

This suite evaluates the GTD conversational layer using an LLM judge with a rubric. Tests prioritize semantic outcomes over exact wording or formatting.

Key points:
- Natural language first: The assistant may reply conversationally. Tool-call transcripts are optional.
- Conceptual criteria: `success_criteria` are treated as conceptual outcomes, not literal substrings.
- Safety & ambiguity are critical: Judges fail responses that perform destructive actions without confirmation or act on ambiguous references.
- Scoring: The judge computes a score and returns `pass`/`reasoning`. Our harness only requires these fields.

When adding cases:
- Keep `prompt` natural and user-centric; avoid directing the model to show specific strings.
- Use `expected_behavior` to describe intended outcomes and GTD semantics.
- Keep `success_criteria` as short conceptual bullets (e.g., "establish dependency", "respect context availability", "ask for confirmation").
- Use the `category` to hint at critical behaviors (e.g., Delete/Edge cases require confirmation/clarification).

Implementation notes:
- The judge prompt (in `tests/conversational_layer/judge.py`) instructs the model to evaluate conceptually and to ignore formatting.
- `must_not` (optional, string[]): conceptual anti-criteria that trigger failure if present in the reply (e.g., "delete without explicit confirmation").
- `expected_pass` (optional, bool): when false, the test expects the judge to fail the reply (used for negative controls).
- `assistant_override` (optional, string): bypasses the assistant call and feeds a canned reply to the judge (used to validate the judge on negative controls).
- `judge_utils.parse_judge_verdict` tolerates fenced or chatty judge outputs.
- The lightweight test overlay (`tests/fixtures/system-prompt-test-overlay.md`) encourages clarity and safety without imposing rigid formatting.
- Live-MCP overlay (`tests/fixtures/system-prompt-live-mcp-overlay.md`) is appended when MCP is available; it directs the assistant to perform real, non-destructive operations without permission prompts and to confirm outcomes.
- No-MCP overlay (`tests/fixtures/system-prompt-no-mcp-overlay.md`) is appended when MCP is not available; it directs the assistant to simulate intended operations and provide concise, representative results.

Usage:
- Run all cases: `python tests/test_conversational_layer_new.py`
- Run assistant/system-prompt cases only: `python tests/test_conversational_layer_new.py --suite assistant`
- Run judge-only cases (negative controls): `python tests/test_conversational_layer_new.py --suite judge`
- Run a specific case: `python tests/test_conversational_layer_new.py --test-name query_projects`
- Adjust timeouts: `--assistant-timeout 120 --judge-timeout 90` or via env `CLAUDE_TIMEOUT`, `CLAUDE_TIMEOUT_ASSISTANT`, `CLAUDE_TIMEOUT_JUDGE`.

Running without MCP configured:
- The harness appends a No-MCP overlay that instructs the assistant to simulate intended graph operations and provide concise, representative results.
- This keeps answers useful (e.g., show likely projects/next actions) without requiring servers. Safety rules (e.g., confirm before destructive changes) still apply.

Suites:
- `--suite assistant` runs only system-prompt/assistant cases (no `assistant_override`).
- `--suite judge` runs only judge rubric cases (`assistant_override` present or `category: NegativeControl|Judge`).
- `--suite all` (default) runs both.

Summary output:
- Reports how many cases matched expectations and shows judge PASS/FAIL tallies separately.

Modes:
- Tests always run in **Live MCP mode** (`--mode real`): Requires MCP server; assistant performs actual tool calls.

Note: Simulation mode has been removed to ensure tests validate real MCP operations.

API syntax in Simulation:
- The judge ignores low-level tool-call syntax and parameter names in Simulation mode. Focus on conceptual flow and outcomes; pseudo-calls are optional and not graded for exactness.

Patterns to prefer in Simulation:
- Capture tasks: explicitly confirm creation (isComplete=false) and any dependencies/contexts; avoid permission prompts.
- Delegated items: explicitly confirm creation/update including responsibleParty set and waiting-for treatment.
- Manual states: explicitly note MANUAL tracking and remind user to report changes.
- Confirmed deletions: do not re-ask; simulate deletion and summarize what was removed.
- Update details: append to content (not replace with a property), and confirm preservation of other properties.
