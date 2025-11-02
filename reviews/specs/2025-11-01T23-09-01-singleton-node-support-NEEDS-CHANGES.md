# Spec Review: singleton-node-support

**Reviewer**: Codex (Spec Reviewer)
**Date**: 2025-11-01
**Spec Version**: specs/proposed/singleton-node-support.md
**Status**: NEEDS-CHANGES

## Summary
Good, focused enhancement that fills the gap GTD Ontology called out. Interface is lean, behavior is deterministic, and scenarios are clear. A few clarifications are needed to align with the current graph-memory-core contract and to make tests fully specific: (1) explicitly include `get_node` in dependencies/algorithm (since `query_nodes` returns IDs only), (2) add error handling for missing creation fields when no node exists, (3) add an AC for `on_multiple: "newest"` behavior, and (4) make selection/tie-break semantics explicit in the contract. Concurrency note is fine for Phase 1; suggest a brief note about `created` under races.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap intent
- [x] Interfaces specified (tool shape is clear)
- [x] Happy/edge paths covered
- [ ] Error handling fully specified (missing-field case)
- [ ] Testability complete (no AC for `on_multiple: "newest"`)
- [ ] Dependencies precise (needs `get_node` for timestamps)

## Detailed Feedback

1) Dependencies/Algorithm Clarity (Required)
- Issue: Spec says it uses `query_nodes` and `create_node`. `query_nodes` returns only IDs (per graph-memory-core Tool 10). To select by `created` timestamp, the tool must call `get_node` for each candidate.
- Action: In Dependencies, add `get_node` and in Interface/Process, state the selection algorithm: fetch candidates via `query_nodes({ type })`, then `get_node` for `created` and select by `created` (ISO string) with tie-breaker.

2) Error Handling for Missing Creation Fields (Required)
- Case: If no node exists and caller omits one of `content`, `encoding`, or `format`, what happens?
- Action: Add to Raises: `INVALID_ARGUMENT` (or `MISSING_REQUIRED_FIELD`) when creation is required but any of `content`/`encoding`/`format` is missing.
- Add AC: "If no node exists and required creation fields are missing, tool fails with INVALID_ARGUMENT" (or chosen code).
- Add Preconditions: "If no node exists, `content`, `encoding`, and `format` must be provided".

3) AC for `on_multiple: "newest"` (Required)
- Add an acceptance criterion mirroring AC3 that verifies selection of the max `created` when `on_multiple` is set to `"newest"`.
- Optionally, add a scenario for this path.

4) Selection and Tie-break Semantics (Clarify)
- In Interface Contract, under Parameters/Returns or Postconditions, state explicitly:
  - Default selection: `on_multiple = "oldest"` → minimal `created` timestamp.
  - `on_multiple = "newest"` → maximal `created` timestamp.
  - Tie-breaker when `created` equal: lexicographic ascending by node_id (stable across runs).

5) Concurrency Note (Optional but helpful)
- Add one line to Interface Contract or Notes: "Under rare races, multiple nodes may be created; multiple callers may observe `created: true`. Subsequent calls deterministically return the selected node with `created: false`."

6) Minor
- In Scenarios, Scenario 1 example uses `{}` JSON content; consider a tiny non-empty example showing format/encoding alignment (but not required).
- Add References section with link to specs/done/graph-memory-core.md for the tool contracts used.

## Approval Criteria
Please make the following edits for approval:
1. Add `get_node` to Dependencies and describe its use in the selection algorithm.
2. Add error handling for missing creation fields (choose `INVALID_ARGUMENT` or `MISSING_REQUIRED_FIELD`) and an AC for that behavior.
3. Add an AC covering `on_multiple: "newest"` selection (max `created`).
4. Clarify selection semantics and tie-breaker in the Interface Contract.

## Next Steps
- [ ] Update spec with the four required items above.
- [ ] Optional: add a scenario for `on_multiple: "newest"`.
- [ ] Re-request review; I’ll approve and move to todo.

