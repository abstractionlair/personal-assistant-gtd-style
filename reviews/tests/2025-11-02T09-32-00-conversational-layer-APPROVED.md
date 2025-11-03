# Test Review: Conversational Layer

**Reviewer:** Test Reviewer (Codex CLI)
**Date:** 2025-11-02 09:32:00
**Spec:** specs/todo/conversational-layer.md
**Test Files:** tests/test_conversational_layer.py, tests/test_cases.json
**Status:** APPROVED

## Summary
All critical gaps from the prior review are resolved. The evaluator now locates the spec robustly (doing→todo→done), the missing acceptance criteria are covered with concrete test cases, and the evaluator is trimmed to under 300 lines. The suite cleanly exercises behavior across Capture, Query, Update, Delete, and Edge scenarios and will effectively drive the GREEN phase.

## Clarity & Readability
- ✓ Test names and categories are descriptive
- ✓ Straightforward harness flow and helpers
- ✓ Meaningful variable/function names
- ✓ Self-contained cases without hidden dependencies

## Completeness ⚠ Critical
- ✓ Capture: 9 cases (≥8)
- ✓ Query: 6 cases (≥6)
- ✓ Update: 5 cases (≥4)
- ✓ Delete: 2 cases (≥2)
- ✓ Edge: 6 cases (≥4)
- ✓ AC37 (infer obvious details): tests/test_cases.json:96
- ✓ AC40 (dependency direction clarification): tests/test_cases.json:303
- ✓ AC34 (invalid delete requests): tests/test_cases.json:267
- ✓ AC46 (no automatic parent completion): tests/test_cases.json:231

## Coverage Metrics ⚠ Critical
Behavioral acceptance coverage meets or exceeds minimums. Code coverage targets are not applicable to this prompt-driven feature; the acceptance coverage breadth suffices to constrain implementation.

## Independence
- ✓ Each case runs independently
- ✓ No shared mutable state or order dependency
- ✓ Fixtures not required; CLI invocation model isolates runs

## Quality
- ✓ Behavioral assertions via case-insensitive substrings (not brittle exact text)
- ✓ Clear expected_behavior descriptions provide context
- ✓ Minimal external dependencies (optional MCP config for realism)

## RED Phase Verification
- With skeleton placeholders in src/conversational-layer/system-prompt.md:1, tests are expected to fail behaviorally (RED) until the prompt is completed. Failures should be due to missing behavioral criteria rather than import/signature errors. Local execution requires a working `claude` CLI or `CLAUDE_CMD` alias.

## Notes on Fixes Verified
- Spec path robustness: tests/test_conversational_layer.py:1 now searches `specs/doing`, then `specs/todo`, then `specs/done`.
- Evaluator size: tests/test_conversational_layer.py:1 is 227 lines (<300 per AC42).
- Added tests: see tests/test_cases.json lines 96, 231, 267, 303 for AC37, AC46, AC34, AC40 respectively.

## Positive Notes
- Prompt bundle includes Interface Contract and Data Structures sections to anchor responses.
- Judge prompt is concise and enforces structured JSON outputs.
- Category distribution exceeds minimums (Total cases: 28).

## Decision

APPROVED - Ready for implementer (GREEN phase)

