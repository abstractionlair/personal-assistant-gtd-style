# Spec Review: graph-memory-core

**Reviewer**: OpenAI Codex (Codex CLI)
**Date**: 2025-10-31
**Spec Version**: specs/proposed/graph-memory-core.md
**Status**: NEEDS-CHANGES

## Summary
Excellent, comprehensive spec that largely meets schema-spec requirements and aligns with VISION, SCOPE, and ROADMAP (Phase 1, Feature 2). Interface coverage is strong (18 tools), with clear preconditions/postconditions and robust acceptance criteria and scenarios. A few ambiguities should be clarified before approval to prevent divergent implementations and to ensure testability.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap
- [x] Interfaces specified
- [x] Happy/edge paths covered
- [x] Error handling specified
- [x] Integration points clear
- [x] Testability verified
- [x] Dependencies identified

## Detailed Feedback

1) Status field vs workflow state
- The header uses Status: "Proposed" while schema-spec lists Draft | Review | Approved | Implemented. Directory state (specs/proposed/) is correct, but consider using "Review" when requesting review to match schema terminology. Not a blocker.

2) MCP server name consistency
- In "MCP Server Configuration" the server name is "graph-memory-core" but the example config key uses "graph-memory". Choose one canonical name and use it consistently (tooling, docs, examples).

3) Content encoding and format/extension mapping
- create_node says content may be "text or base64-encoded binary", but input has no `encoding` field. Since file-storage-backend requires an encoding, the graph server must decide. Please specify:
  - Supported text formats (e.g., markdown, json, txt) → use utf-8
  - All other formats default to base64
  - Explicit format→extension map (e.g., markdown→.md, json→.json)
  - Behavior if unknown format is provided (reject vs default to .bin + base64)

4) ID format and examples
- The spec states IDs are opaque, but examples use typed/sequential IDs (e.g., mem_proj_001, conn_001) and the sample generator returns `mem_<ts>_<rand>`. Please resolve by either:
  - Declaring IDs opaque (tests capture returned IDs, never assume shape), and updating examples to non-sequential opaque forms; or
  - Defining explicit ID format rules (e.g., node IDs: `node_<ts>_<rand>`, connection IDs: `conn_<ts>_<rand>`). Pick one and apply consistently across examples and scenarios.

5) Property data model and matching semantics
- Properties are specified as "object" without constraints. For testable matching in query_nodes/query_connections, please define:
  - Allowed value types: primitives only (string | number | boolean) at top-level; no nested objects/arrays (recommended for MVP)
  - Matching semantics: exact equality on provided keys; strings case-sensitive; numbers compare by value; booleans exact
  - Behavior for unknown property keys (ignored vs mismatch)

6) Property removal semantics on update
- update_node/update_connection merge properties but do not define removal. Add one of:
  - `remove_properties?: string[]` to delete keys, or
  - Treat `{ key: null }` as removal (documented), or
  - State explicitly that removal is not supported in MVP
  - Add an acceptance criterion for chosen behavior.

7) Content format changes on update
- update_node allows changing content but not format. Clarify:
  - Is `format` immutable after creation? If not, add `content_format?: string` to allow changing format and file extension (and describe migration of file path).
  - If immutable, state "content format is fixed at creation" and add a constraint to update_node.
  - Mirror the same rule for connection content.

8) Connection content storage location
- create_connection mentions "stored alongside connection" but path is unspecified. Define a canonical path pattern, e.g., `_content/connections/{id}.{ext}` (parallel to node content) and include in the Connection structure invariants.

9) search_content behavior for binary files
- Spec states it "works on both text and binary (searches raw bytes)", which makes string queries on binary ambiguous. Recommend limiting search to text formats or stating: "Binary content is not searched; only text formats are scanned". Add an acceptance criterion to fix expectations.

10) Error code set and consistency
- Ensure the enumerated error codes are complete and consistent across tools (`ONTOLOGY_NOT_FOUND`, `ONTOLOGY_ALREADY_EXISTS`, `TYPE_ALREADY_EXISTS`, `NODE_NOT_FOUND`, `CONNECTION_NOT_FOUND`, `INVALID_NODE_TYPE`, `INVALID_CONNECTION_TYPE`, `INVALID_TOPOLOGY`, `REQUIRED_PROPERTY_MISSING`, `FILE_CREATION_FAILED`, `CONTENT_READ_FAILED`). Consider adding a simple table in Interface Contract listing each tool’s possible errors.

11) validate_connection diagnostics
- Optional but helpful: return `{ valid: boolean, reason?: string }` to aid callers when invalid.

12) Minor alignment nits
- Acceptance criteria and scenarios sometimes reference specific file paths and ID shapes. That’s fine for tests if those are specified as implementation requirements. If IDs are declared opaque, update those references to use the captured IDs instead of hardcoded examples.

## Approval Criteria
This spec will be approved once it:
1. Clarifies encoding and format→extension decision rules (text vs binary, unknown formats).
2. Resolves ID format vs opacity and makes examples consistent accordingly.
3. Defines property value constraints and matching semantics for queries.
4. Specifies property removal semantics for update operations (or explicitly defers/removes support).
5. Clarifies whether content format can change on update and adjusts interface accordingly.
6. Specifies connection content file path convention.
7. Limits or clarifies binary search behavior in search_content and updates acceptance criteria if needed.
8. Aligns server naming in config and documentation.

## Next Steps
- [ ] Update the spec with the clarifications above
- [ ] Reply here or re-request review
- [ ] On approval: I will move the spec to `specs/todo/` as gatekeeper

