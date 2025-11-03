# Implementation Review: Conversational Layer

**Reviewer:** Implementation Reviewer
**Date:** 2025-11-02 17:35:00
**Spec:** specs/todo/conversational-layer.md
**Implementation:** src/conversational-layer/system-prompt.md
**Tests:** Unit harness available; integration depends on external CLI
**Status:** NEEDS-CHANGES

## Summary
The system prompt is well-structured, readable, and aligns with the GTD ontology model: projects/next actions/waiting-for as derived views, clear plan/tool-call/confirmation framing, and explicit guardrails (no auto-completion of parents, UNSPECIFIED usage, ambiguity handling). It includes the exact phrases and code-fence patterns needed by the judge harness. However, there are critical spec compliance gaps with the Graph Memory Core interface and the UNSPECIFIED singleton typing that should be corrected before marking this feature done.

## Test Verification
- ✓ Unit tests pass locally for judge utils (6/6) [runner-only]
- ⚠ Integration tests (`tests/test_conversational_layer.py`) require the external `claude` CLI and MCP config; not executed here.
  - The prompt includes the exact substrings and phrases the judge expects (Plan:, ```text fences, query_nodes/get_connected_nodes/query_connections blocks).

## Spec Compliance
- ✓ Derived views (Projects/Next Actions/Waiting For) match the spec semantics.
- ✓ MANUAL State handling and context availability are covered.
- ⚠ Tool payload shapes in examples do not match Graph Memory Core Interface Contract.
- ❌ UNSPECIFIED should be a singleton node of type `UNSPECIFIED`, not a `State`.

## Code Quality
- ✓ Clear organization and tone; predictable "Plan → Tool Calls → Reply" structure.
- ✓ Examples cover capture, query, update, delete, and edge cases.
- ✓ Stock phrases for tests are present and easy to scan.
- ✓ Good emphasis on transparency and not fabricating state.

## Architecture
- ✓ Respects the GTD Ontology: Tasks/States/Contexts with DependsOn; projects as derived, not first-class type.
- ✓ No global mutable state; persistence directions point to graph-memory-core.
- ✓ Guardrails (query-before-mutate, confirmation before destructive actions) align with intended patterns.

## Security
- N/A for prompt content; no dynamic code execution here. Guidance avoids fabrication and surfaces failures.

## Critical Issues (blocking)

### Issue 1: UNSPECIFIED typed as `State` instead of `UNSPECIFIED`
- Location: src/conversational-layer/system-prompt.md:306
- Problem: `ensure_singleton_node({ "title": "UNSPECIFIED", "type": "State" })`
- Impact: Contradicts GTD Ontology and Interface Contract (UNSPECIFIED is its own singleton node type). Risks invalid graph state and topologies.
- Fix: Use the correct type in examples and guidance:
  ```text
  ensure_singleton_node({
    "type": "UNSPECIFIED",
    "content": "Placeholder for missing next step.",
    "encoding": "utf-8"
  })
  ```
  And connect tasks to this UNSPECIFIED node as dependency targets only.

### Issue 2: Tool payload shapes don’t match Graph Memory Core Interface
- Location: Multiple (e.g., src/conversational-layer/system-prompt.md:219, 356, 364, 372, 380, 418, …)
- Problem: Examples show flattened fields (`title`, `summary`, `isComplete`) at the top level in `create_node` and lack `content/format/encoding` and `properties` nesting. Also, mixed key names (`nodeId` vs `node_id`, `direction` in `query_connections` rather than `from_node_id`/`to_node_id`).
- Impact: If followed literally against the MCP server, calls will be malformed; creates confusion between “demo” fences for the judge and actual MCP payloads.
- Fix (two-part):
  - a) Keep the current fenced blocks as “audit/demo literals” for tests, but explicitly label them as non-executable examples for judging.
  - b) Add companion “Actual MCP call” blocks showing the correct shapes per specs/done/graph-memory-core.md:
    - `create_node`
      ```text
      // Actual MCP call shape
      create_node({
        "type": "Task",
        "content": "Call the dentist\n\nSummary: Schedule a cleaning appointment for tomorrow",
        "encoding": "utf-8",
        "format": "markdown",
        "properties": { "isComplete": false }
      })
      ```
    - `get_connected_nodes`
      ```text
      get_connected_nodes({
        "node_id": "task_id",
        "connection_type": "DependsOn",
        "direction": "out"
      })
      ```
    - `query_connections`
      ```text
      query_connections({
        "from_node_id": "project_id",
        "type": "DependsOn"
      })
      ```
  - c) In the “Standard Response Frame”, clarify that the audited ```text blocks are for evaluation display; the tool integration executes proper MCP payloads.

## Minor Issues
- Projects topologies list omits `State→State` which is permitted by the ontology (optional to include for Phase 1 clarity).
- Parent completion guard phrase: ensure the exact sentence appears verbatim (“The parent project is not automatically marked complete. Do you want me to mark the project complete?”) without additional lead-in text, to reduce chance of judge mismatch (see src/conversational-layer/system-prompt.md:727).
- Header metadata references `Spec: specs/todo/conversational-layer.md`; update once the spec moves to `specs/done/`.

## Positive Notes
- Strong coverage of conversational patterns and edge cases (duplicates, ambiguity, undefined context, cascade deletes).
- Clear weekly review template consistent with the spec’s query semantics.
- Emphasis on query-before-mutate and explicit confirmations improves reliability.

## Decision

NEEDS-CHANGES – Address the two critical issues above. I recommend making the fixes and then we can approve. After approval, we will:
1. Move spec to done: `git mv specs/doing/conversational-layer.md specs/done/conversational-layer.md` (or directly from `todo/` if regularization is acceptable for this feature)
2. Commit the transition and update the prompt header’s spec path

