# Spec Review: conversational-layer

**Reviewer**: OpenAI Codex (Codex CLI)
**Date**: 2025-11-02
**Spec Version**: specs/proposed/conversational-layer.md
**Status**: NEEDS-CHANGES

## Summary
Strong alignment with Vision/SCOPE/ROADMAP and a solid framing of the GTD interaction model. The spec defines core behaviors and derived views conceptually, but it is missing critical schema-required sections and testable details. Most examples are placeholders, interfaces to MCP tools are not specified at a contract level, and several data model details currently conflict with the approved GTD Ontology. As written, the spec is not yet implementable nor testable.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap
- [ ] Interfaces specified (contract-level, tool calls, parameters)
- [ ] Happy/edge paths covered with concrete examples
- [ ] Error handling specified with expected outcomes
- [ ] Integration points clear (MCP tools mapping, ontology alignment)
- [ ] Testability verified (acceptance criteria + scenarios)
- [ ] Dependencies identified and reconciled with done specs

## Detailed Feedback

### 1) Structure and Metadata (Schema Compliance)
- Missing required fields in header: Created, Author. Also “Status” should use schema values (Draft | Review | Approved | Implemented). Current value is “Proposed” at specs/proposed/conversational-layer.md:4.
- Title should follow schema header convention. Suggest heading: `# Specification: Conversational Layer` instead of `# Feature: Conversational Layer` (specs/proposed/conversational-layer.md:14).
- Missing sections required by schema: Value Delivered, Interface Contract, Acceptance Criteria, Scenarios, Data Structures (consolidated), Dependencies (section-level), Constraints and Limitations, Open Questions, References.

### 2) Alignment with GTD Ontology (Blocking)
The approved GTD Ontology defines canonical properties and semantics that this spec must consume. Current spec introduces conflicting fields and concepts:
- Task properties list includes `type (TASK/PROJECT)` and `completedAt`. Ontology specifies Task.properties.isComplete:boolean and timestamps as optional metadata fields; “Project” is a derived view, not a type flag.
  - Required change: Remove `type (TASK/PROJECT)` and `completedAt` from Task properties. Use `properties.isComplete: boolean` for completion, and rely on derived queries to identify projects (Tasks with outgoing dependencies).
- Context is correctly modeled with `isAvailable`, but ensure names and types match ontology (`Context.properties.isAvailable: boolean`).
- Waiting For relies on manual states, but State creation/management is deferred in this feature while the query definition still depends on State nodes.
  - Required change: Either (A) include minimal conversational State creation for MANUAL logic (Phase 1 scope), or (B) redefine Waiting For for Phase 1 using Task properties only (e.g., a `waitingOn` string and no State-node dependency). Choose and document one approach with acceptance criteria.

References:
- GTD Ontology spec: specs/done/gtd-ontology.md
- GTD Ontology types: src/gtd-ontology/src/types.ts

### 3) Interface Contract to MCP Tools (Blocking)
The spec needs a precise contract mapping conversational intents to MCP tool calls from graph-memory-core. Right now it says “Brief conceptual explanation” and defers signatures to configuration. For test-writer and implementer, list the concrete tools to call and the expected request/response shapes used by this feature.

Required additions under “Interface Contract”:
- Server name used (e.g., `graph-memory-core`).
- Tools invoked and minimal shapes (align with graph-memory-core contract):
  - `create_ontology`/`ensure_singleton_node` (if used by this feature)
  - `query_nodes({ type, properties })`
  - `get_node({ node_id })`, `get_connected_nodes({ node_id, type, direction })`
  - `query_connections({ from_node_id|to_node_id, type, properties })`
  - `update_node({ id, properties|content|format|encoding })`
  - `create_node({ type, properties, content, encoding, format })`
  - `create_connection({ type, from_node_id, to_node_id, properties })`
  - `delete_node({ node_id })` (and expected cascade behavior per graph-memory-core)
- Property constraints that tests can verify (e.g., values are strings/numbers/booleans only; exact/equality match semantics), consistent with specs/done/graph-memory-core.md.

### 4) Derived Views and Query Semantics (Blocking)
Translate conceptual definitions into precise, testable semantics with examples:
- Projects: “Tasks with incomplete dependents” — Define using connection direction: a Task is a Project if it has at least one outgoing DependsOn to an incomplete Task or State. Provide a concrete example with node IDs and properties.
- Next Actions: Define exact criteria using `isComplete` and dependency traversal. Clarify “no incomplete dependents” vs “no dependent tasks that are incomplete” and the meaning of dependents vs dependencies (direction is defined as “from depends on to”).
- Waiting For: If MANUAL States are deferred, redefine for Phase 1 or include minimal State creation (see Section 2 changes).
- Stuck projects: “incomplete for >2 weeks with no recently completed subtasks” — Specify timestamp fields to use, how “recent” is defined (e.g., 14 days), and how to detect “completed subtasks” via connections.

Each definition needs at least one Given-When-Then scenario and acceptance criteria.

### 5) Conversation Patterns and Examples (Blocking)
The spec promises 25–30 examples but currently lists placeholders. Replace with concrete transcripts that demonstrate:
- Capture: single task, with context, with dependency, UNSPECIFIED case, duplicate detection with explicit user confirmation/merge flow.
- Query: next actions, projects, waiting for, context-filtered, stuck projects, weekly review.
- Update: mark complete (and parent update behavior), change details, add dependency, context availability toggle.
- Delete: warn on dependencies, explicit cascade only when user confirms.
- Edge cases: ambiguous references, conflicting updates, empty results.

Each example should include the exact tool calls and property changes (at least narratively) that the assistant will perform.

### 6) Acceptance Criteria (Blocking)
Add a numbered, testable list that maps to scenarios. Suggested baseline:
- Happy Path
  1. Creating a Task via conversation results in a Task node with content stored and `properties.isComplete=false`.
  2. Creating A depends-on B creates a `DependsOn` from A→B and excludes A from Next Actions until B is complete.
  3. Marking a Task complete sets `properties.isComplete=true` and updates any parent Project logic per spec.
  4. Next Actions query returns only unblocked, incomplete Tasks and excludes those with incomplete dependencies.
- Error Handling
  5. Deleting a Task with dependencies warns the user; no deletion occurs without confirmation.
  6. Ambiguous task references prompt for clarification (no write operations executed).
  7. Duplicate capture displays candidate matches; no duplicate is created unless user confirms.
- Edge Cases
  8. Empty query returns an explicit “no results” response without errors.
  9. Context-filtered queries respect `Context.isAvailable=false` by excluding tasks requiring unavailable contexts.
  10. Stuck projects detection uses the defined time window and returns consistent results.

### 7) Scenarios (Blocking)
Include at least 6 Given-When-Then scenarios that align with acceptance criteria. Example starters:
- Basic capture → query next actions.
- Dependency blocking and unblocking.
- Waiting For (per chosen Phase 1 approach).
- Duplicate detection and resolution flow.
- Delete with dependency warning and user-confirmed cascade.
- Context availability change affecting next actions.

### 8) Consistency Rules and Parent Updates (Clarify)
Spec states: “update parent completion when all children complete” (specs/proposed/conversational-layer.md:44). Define whether parent completion is auto-inferred or user-confirmed, and whether “children” are modeled as incoming or outgoing dependencies. Provide the exact traversal used and any exceptions (e.g., parents that still depend on States).

### 9) Weekly Review Format (Clarify)
Add concrete sort orders and limits. For example:
- Completed this week: sorted by modified desc, limit 20.
- Active projects: show open dependency counts.
- Stuck projects: use 14-day rule with last-completion timestamp.
- Next actions available: limit 20, grouped by context availability.

### 10) Performance and Limits (Non-blocking, recommend)
State MVP expectations (e.g., up to 10k nodes consistent with graph-memory-core) and any conversation-time heuristics to keep result sets manageable.

## Approval Criteria
For APPROVED status, update the spec to:
1) Add missing schema-required sections with concrete, testable content: Interface Contract, Acceptance Criteria, Scenarios, Value Delivered, Data Structures, Dependencies, Constraints, Open Questions, References.
2) Align all data fields with the approved GTD Ontology (remove `type (TASK/PROJECT)`, replace `completedAt` with `properties.isComplete`, and ensure Context/State semantics match).
3) Resolve Waiting For for Phase 1: either include minimal MANUAL State creation or redefine Waiting For without State nodes; document chosen path with acceptance criteria and scenarios.
4) Specify precise, verifiable query semantics for Projects/Next Actions/Waiting For/Stuck and include examples.
5) Replace placeholder examples with concrete conversation transcripts and expected tool interactions.

## Next Steps
- [ ] Update header metadata (Created, Author, Status value) and rename heading to “Specification”.
- [ ] Add the Interface Contract mapping conversational intents → MCP calls.
- [ ] Fill Acceptance Criteria and Scenarios with concrete, testable items.
- [ ] Align Task/State/Context properties with GTD Ontology types.
- [ ] Clarify parent completion propagation behavior and weekly review specifics.
- [ ] Decide and document the Phase 1 “Waiting For” approach.

## State Transition
Do NOT move the spec. Remains in `specs/proposed/` until the above blocking issues are addressed and the review is re-run.

