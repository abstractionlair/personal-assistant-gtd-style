# Spec Review: gtd-ontology

**Reviewer**: Codex (Spec Reviewer)
**Date**: 2025-11-01
**Spec Version**: specs/proposed/gtd-ontology.md
**Status**: NEEDS-CHANGES

## Summary
Well-structured, thorough specification that clearly defines the GTD ontology (Task, State, UNSPECIFIED), query patterns (Projects, Next Actions, Waiting For), and documented algorithms for state logic and completion propagation. Acceptance criteria are extensive and cover most behaviors. Primary issues: (1) misalignment with SCOPE.md and VISION.md regarding Context nodes (spec defers them; SCOPE/VISION include them in MVP), (2) missing explicit error-handling acceptance criteria (invalid topology, invalid logic values, UNSPECIFIED as a source), and (3) missing explicit performance acceptance criteria derived from SCOPE (<2s for typical queries at MVP scale). Also suggest minor clarifications to the Interface Contract for the initialization script and singleton behavior.

## Checklist
- [x] Aligns with Roadmap (Feature 3)
- [ ] Aligns with Vision/Scope (Context nodes mismatch)
- [x] Interfaces specified (sufficient for this feature)
- [x] Happy/edge paths covered
- [ ] Error handling specified (see gaps below)
- [x] Integration points clear (depends on graph-memory-core)
- [ ] Testability verified (add error + perf criteria)
- [x] Dependencies identified (incl. ensure_singleton_node)

## Detailed Feedback

1) Alignment with Vision/Scope
- VISION.md and SCOPE.md list Context as part of the MVP GTD ontology (nodes: Task, State, Context). This spec explicitly defers Context nodes to Phase 2. ROADMAP.md agrees with the deferral, so there is a cross‑doc inconsistency.
- Action: Either (A) add a minimal Context node definition (even if only documented and unused) to satisfy MVP alignment, or (B) update SCOPE.md (and optionally VISION.md Technical Requirements section) to note that Context nodes are Phase 2. State preference here and coordinate with platform-lead to update docs if choosing (B).

2) Error Handling Acceptance Criteria (missing)
- Add explicit, testable criteria for invalid operations and boundary conditions. Examples to include:
  - Creating a DependsOn connection with UNSPECIFIED as the source is rejected with a clear validation error.
  - Creating a State with an invalid `logic` value is rejected.
  - Creating a Task without required `isComplete` property is rejected by ontology validation.
  - Attempting to create a second UNSPECIFIED node returns the existing instance (no duplicates) and does not create a new node.
  - Deleting UNSPECIFIED is rejected or no‑op (specify desired behavior) to preserve singleton semantics.

3) Performance Acceptance Criteria (missing)
- SCOPE.md sets performance expectations for typical scale. Add explicit criteria such as:
  - Projects query completes in <2s for ~500 nodes and ~1–2k connections (representative MVP volume).
  - Next Actions query completes in <2s for the same dataset.

4) Interface Contract Clarifications
- Initialization script:
  - Add a short signature/contract block: name (`initialize-gtd-ontology.ts`), inputs (none), returns (`{ ok: boolean, error?: string }`), idempotency details, and exit code mapping (0 on success, non‑zero on failure).
- `ensure_singleton_node` behavior:
  - Document exact semantics for idempotency: returns existing node id if present; otherwise creates and returns new id. Define error conditions (e.g., if an orphan duplicate exists due to manual edits, what happens?).

5) Constraints and Invariants (tighten wording)
- UNSPECIFIED: call out explicitly in Acceptance Criteria that UNSPECIFIED cannot have outgoing DependsOn connections and is always a hard blocker for Next Actions; include corresponding negative tests (attempting to create such a connection fails).

6) Scenario Coverage
- Scenarios are strong. Consider adding at least one explicit error scenario (e.g., attempting to connect UNSPECIFIED → Task should fail with validation error) to map to the new error criteria above.

## Approval Criteria
To approve, please:
1. Resolve the Context node alignment by either including a minimal Context type in this spec or updating SCOPE.md (and VISION.md technical section if desired) to defer Context to Phase 2.
2. Add explicit error‑handling acceptance criteria for invalid topology, invalid property values, and singleton semantics (see list above).
3. Add explicit performance acceptance criteria (<2s) for Projects and Next Actions queries at MVP scale.
4. Clarify the initialization script contract (inputs/outputs/exit codes) and singleton idempotency semantics.

## Next Steps
- [ ] Decide A/B path for Context nodes and update the appropriate doc(s).
- [ ] Add Error Handling section under Acceptance Criteria with the specific tests listed.
- [ ] Add Performance criteria under Acceptance Criteria with concrete dataset sizes and thresholds.
- [ ] Update Interface Contract with initialization script signature and singleton semantics.
- [ ] Re‑request review.

