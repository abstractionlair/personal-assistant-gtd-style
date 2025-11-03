# Spec Review: conversational-layer

**Reviewer**: OpenAI Codex (Codex CLI)
**Date**: 2025-11-02
**Spec Version**: specs/proposed/conversational-layer.md (v2.0)
**Status**: APPROVED

## Summary
The updated Conversational Layer spec now fully complies with the schema and aligns with the approved GTD Ontology and Graph Memory Core. It specifies clear, testable behaviors, provides a concrete MCP interface contract, precise query semantics for derived views, comprehensive acceptance criteria, and realistic scenarios. The Phase 1 scope decisions (MANUAL-only States and Waiting For via responsibleParty) are explicit and consistent. This spec is implementable and testable.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap
- [x] Interfaces specified (MCP tools, requests/responses)
- [x] Happy/edge paths covered (acceptance criteria and scenarios)
- [x] Error handling specified (delete warnings, ambiguity, duplicates)
- [x] Integration points clear (graph-memory-core, GTD ontology)
- [x] Testability verified (algorithms + criteria + scenarios)
- [x] Dependencies identified (internal/external)

## Evaluation Highlights
- Interface Contract: Lists `graph-memory-core` tools with input/return shapes and property constraints matching specs/done/graph-memory-core.md.
- Ontology Alignment: Uses Task.isComplete, State.isTrue (MANUAL only), Context.isAvailable, UNSPECIFIED singleton; projects are derived (no type flag).
- Derived Views: Projects, Next Actions, Waiting For, and Stuck are defined with precise algorithms and examples.
- Acceptance Criteria: Extensive, specific, and verifiable; cover capture, dependencies, context, updates, delete, edge cases.
- Scenarios: Concrete Given-When-Then flows with tool calls and outcomes.
- Constraints/Dependencies: Clear technical and functional constraints; external/internal deps documented.

## Decision Rationale
The spec is clear, complete, and testable, with no blocking issues. Minor metadata note: document header `status` is "Draft"; approval does not require changing it now, but the author may optionally update to "Approved" in a subsequent edit.

## State Transition
Authorized to move: proposed → todo for `conversational-layer.md`.

## Next Steps
- [x] Move to `specs/todo/conversational-layer.md`
- [ ] Begin skeleton/prompt work per ROADMAP Phase 1
- [ ] Implement eval harness and initial test cases

