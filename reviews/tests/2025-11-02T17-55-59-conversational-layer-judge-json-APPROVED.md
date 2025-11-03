# Test Review: Conversational Layer – Judge JSON Robustness

**Reviewer:** Test Reviewer
**Date:** 2025-11-02 17:55:59 UTC
**Spec:** specs/doing/conversational-layer.md (context for harness behavior)
**Test Files:** tests/unit/test_judge_utils.py, tests/test_conversational_layer.py
**Status:** APPROVED

## Summary
The test-writer implemented a tolerant JSON verdict parser and tightened the judge prompt. Unit tests validate key scenarios (bare JSON, fenced JSON, surrounding text). The harness now retries and accepts fenced outputs, addressing the implementer’s failures. The approach is sound and unblocks implementation; a few minor robustness tests are suggested.

## Clarity & Readability
- ✓ Test names descriptive and specific
- ✓ AAA structure simple and clear for parser cases
- ✓ Variables meaningful; minimal setup
- ✓ Tests self-contained and independent

## Completeness
- ✓ Happy path: bare JSON parsed
- ✓ Edge cases: fenced JSON; surrounding text; leading text before JSON
- ✓ Error case: invalid JSON returns None
- ⚠ Additional parser edge cases worth adding (see Missing Test Cases)

## Coverage Metrics
- Not measured (coverage plugin not configured locally). Given scope, tests likely cover primary branches of the parser. Recommend adding coverage in CI to verify ≥80% line, ≥70% branch for this module.

## Independence
- ✓ No shared state
- ✓ Order-independent
- ✓ No external dependencies

## Quality
- ✓ Tests assert observable behavior (parsed dict or None)
- ✓ Minimal fixtures/mocks required
- ✓ Assertions are specific
- ✓ Implementation-agnostic beyond public function behavior

## RED Phase Verification
- Not applicable; this is infrastructure test for a parsing helper rather than a feature under TDD. Unit tests pass locally (6 passed).

## Critical Issues
None. The fix implements the agreed option (tolerant parsing) and also tightens the judge prompt, reducing recurrence.

## Missing Test Cases
To harden against additional judge formatting quirks:
1. tests/unit/test_judge_utils.py: add fence without language tag (` ``` { ... } ``` `)
2. tests/unit/test_judge_utils.py: add uppercase/variant tag (```JSON ...```), currently handled, but explicit test improves confidence
3. tests/unit/test_judge_utils.py: add non-json language tag (```jsonc``` or ```json5```) with valid JSON body – verify fallback still succeeds
4. tests/unit/test_judge_utils.py: add triple-tilde fences (~~~) with valid JSON body – verify fallback still succeeds
5. tests/unit/test_judge_utils.py: trailing text after JSON object (e.g., `{"pass":true,...}\nExplanation:`) – ensure raw_decode path is exercised

## Minor Issues
- judge_utils.py:5 – Fence regex only matches ``` or ```json; it’s fine given downstream fallbacks, but consider supporting any fenced block, then attempting JSON parse, to reduce reliance on the first-brace heuristic in non-`json` fences.
- judge_utils.py:27 – Only the first "{" candidate is tried. For rare inputs with stray braces before the actual JSON object and no matching fence, consider iterating over multiple brace positions with raw_decode until one parses.
- tests/test_conversational_layer.py:35–39 – The tightened judge system prompt is good. You could explicitly add “Output must be a bare JSON object on the first character” to discourage preface whitespace as well.
- tests/test_conversational_layer.py:167 – `attempts = 2` is sensible; consider jitter/backoff or a third attempt if judge variance persists, but optional.

## Positive Notes
- Good separation: parser extracted to judge_utils.py with focused unit tests
- Practical heuristics: fence stripping and raw_decode cover real-world model behavior
- Guardrails in prompt: judge prompt explicitly forbids Markdown and adds key requirements
- Harness error messages are actionable and include assistant transcript on failure when enabled

## Decision
APPROVED – Tests and harness changes are sufficient to proceed. Suggested extra tests can be added opportunistically to further harden parsing but are non-blocking.

