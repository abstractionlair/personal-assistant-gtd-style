# Test Review: Conversational Layer

**Reviewer:** Test Reviewer (Codex CLI)
**Date:** 2025-11-02 09:20:00
**Spec:** specs/todo/conversational-layer.md
**Test Files:** tests/test_conversational_layer.py, tests/test_cases.json
**Status:** NEEDS-CHANGES

## Summary
Solid foundation and clear scenario coverage across Capture, Query, Update, Delete, and Edge categories (24 cases total). Harness structure and judging approach align with the spec’s Testing Infrastructure goals. However, several acceptance criteria from the spec are not exercised (notably dependency-direction clarification, invalid delete requests, and explicit “no automatic parent completion”), and the harness has a state-path fragility (hardcoded `specs/todo/`) and exceeds the spec’s <300 line guideline for the single-file evaluator.

## Clarity & Readability
- ✓ Test case names are descriptive and categorized
- ✓ Harness flow is straightforward (bundle → assistant → judge)
- ✓ Variables and functions have meaningful names
- ✓ Tests are self-contained (no external persisted graph state assumed)

## Completeness ⚠ Critical
- ✓ Happy paths covered (capture, queries, updates)
- ✓ Edge cases covered (empty results, ambiguity, undefined context, conflicting updates)
- ❌ Missing: Dependency direction clarification (AC40)
- ❌ Missing: Invalid delete request handling (AC34)
- ❌ Missing: Explicit “No automatic parent completion” check (AC46)
- ➕ Nice-to-have: Explicit inference-of-obvious-details test (AC37)

## Coverage Metrics ⚠ Critical
Behavioral coverage across acceptance criteria is strong but not complete. Code coverage metrics don’t apply here (doc/prompt-driven evaluation). Target: ensure all critical ACs have a corresponding test.

## Independence
- ✓ Each case runs independently with its own prompt context
- ✓ No shared mutable state between cases
- ✓ Order-independent execution (iteration over JSON cases)

## Quality
- ✓ Focus on behavior via substrings rather than exact phrasings
- ✓ Minimal mocking; uses CLI-driven evaluation as intended
- ✓ Assertions specific (success_criteria substrings are concrete)
- ✓ Good spec alignment where covered

## RED Phase Verification
- Expectation: With skeleton placeholders in `src/conversational-layer/system-prompt.md`, most cases should fail (RED) for behavioral gaps rather than import/signature errors.
- Note: Local execution requires `claude` CLI (or `CLAUDE_CMD`) and may fail early in environments without it. This is acceptable operationally but not indicative of RED/GREEN for behavior.

## Critical Issues (must fix)

### Issue 1: Spec path is hardcoded to `specs/todo/`
- **Location:** tests/test_conversational_layer.py:25 (`SPEC_PATH`)
- **Problem:** When the spec moves to `specs/doing/` per workflow, the harness will break.
- **Impact:** Test suite becomes state-fragile across normal transitions.
- **Fix:** Resolve spec path dynamically: prefer `specs/doing/conversational-layer.md` if present, else fall back to `specs/todo/...`.

### Issue 2: Missing acceptance criteria coverage
- **Problem:** AC40 (dependency clarification), AC34 (invalid delete), AC46 (no auto parent completion) lack tests; AC37 (infer obvious details) recommended.
- **Impact:** Implementers won’t be forced by tests to satisfy these behaviors; regressions likely.
- **Fix:** Add the following cases to tests/test_cases.json:

```json
{
  "name": "edge_dependency_direction_clarification",
  "category": "Edge",
  "prompt": "The user says: \"Link research and draft, whichever needs the other.\" The direction is unclear.",
  "expected_behavior": "Ask whether Task A depends on Task B or vice versa; proceed only after clarification.",
  "success_criteria": [
    "Does",
    "depend on",
    "or the other way around",
    "Please confirm the direction"
  ]
},
{
  "name": "edge_invalid_delete_request",
  "category": "Edge",
  "prompt": "The user says: \"Delete the \u2018obsolete feature spec\u2019 task.\" It doesn\u2019t exist.",
  "expected_behavior": "Gracefully report no match and avoid changes; offer to search or create.",
  "success_criteria": [
    "I don't see a task matching",
    "No changes made",
    "Would you like me to search",
    "query_nodes({"
  ]
},
{
  "name": "update_no_automatic_parent_completion",
  "category": "Update",
  "prompt": "All subtasks of \"Prepare investor packet\" are complete. Confirm behavior for the parent task.",
  "expected_behavior": "Do not auto-complete the parent; explicitly ask user if they want to mark it complete.",
  "success_criteria": [
    "not automatically marked complete",
    "Do you want me to mark the project complete",
    "update_node({",
    "isComplete\": true"
  ]
},
{
  "name": "capture_infer_obvious_context",
  "category": "Capture",
  "prompt": "The user says: \"Add a reminder to call the dentist.\" Apply inference guidance.",
  "expected_behavior": "Create a task and infer a phone context requirement unless the user states otherwise.",
  "success_criteria": [
    "create_node({",
    "\"type\": \"Context\"",
    "@phone",
    "DependsOn"
  ]
}
```

### Issue 3: Evaluator file exceeds <300 lines requirement (AC42)
- **Location:** tests/test_conversational_layer.py (353 lines)
- **Problem:** Spec requires single-file evaluator under 300 lines.
- **Impact:** Mismatch with Testing Infrastructure acceptance criteria.
- **Fix options:**
  - Trim comments and helper verbosity; inline small helpers; collapse templates.
  - Move long templates to constants in JSON (still a single file) and compress whitespace.

## Missing Test Cases
- edge_dependency_direction_clarification (AC40)
- edge_invalid_delete_request (AC34)
- update_no_automatic_parent_completion (AC46)
- capture_infer_obvious_context (AC37)

## Minor Issues
- Consider adding a spec-path fallback (`specs/doing/` → `specs/todo/`) and a friendlier error if neither exists.
- Document `CLAUDE_CMD` usage in the repo README for local runs.
- Consider a `--dry-run` mode that skips CLI calls and validates bundle assembly only (developer convenience).

## Positive Notes
- Strong scenario breadth (exactly 24 tests across 5 categories as required).
- Judging approach is pragmatic and behavior-focused (substring criteria, not exact wording).
- Prompt bundle includes key spec sections (Interface Contract, Data Structures) to anchor behavior.

## Decision

NEEDS-CHANGES - Please address the 3 critical issues (spec-path robustness, add 3–4 missing AC tests, reduce evaluator to <300 lines) and resubmit. Once added, I expect this suite to be an excellent driver for the GREEN phase.

