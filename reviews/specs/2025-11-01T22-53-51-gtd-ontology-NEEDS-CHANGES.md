# Spec Review: gtd-ontology

**Reviewer**: Codex (Spec Reviewer)
**Date**: 2025-11-01
**Spec Version**: specs/proposed/gtd-ontology.md
**Status**: NEEDS-CHANGES

## Summary
Great iteration. You added Context nodes, explicit error and performance criteria, init script signature, singleton semantics, and error scenarios. Most prior concerns are addressed. One blocking mismatch remains with graph-memory-core: the create_ontology input shape and node-level required property validation. Minor editorial items also need tightening.

## Checklist
- [x] Aligns with Vision/Scope (Context now included)
- [ ] Aligns with Roadmap (Roadmap still defers Context)
- [x] Interfaces specified (init script clarified)
- [x] Happy/edge paths covered (incl. invalid topology)
- [ ] Error handling feasible with current deps (see node property validation)
- [x] Performance criteria added
- [x] Dependencies identified (ensure_singleton_node)

## Detailed Feedback

1) create_ontology Schema Mismatch (Blocking)
- Location: specs/proposed/gtd-ontology.md:118
- Issue: Spec passes `node_types` as objects with `required_properties`/`optional_properties`. Graph Memory Core (specs/done/graph-memory-core.md) defines `create_ontology` with `node_types: string[]` only; only connection types support `required_properties`.
- Impact: The init script, as specified, won’t work against current graph-memory-core.
- Fix: Update the "Ontology Schema" section to pass `node_types: ["Task", "State", "Context", "UNSPECIFIED"]` (strings). Keep property expectations documented separately (as you already do) and not part of the input payload.

2) Node Required Property Validation (Blocking)
- Location: specs/proposed/gtd-ontology.md:420 (AC33–AC35)
- Issue: AC33–AC35 require rejecting node creation when required properties are missing. Graph Memory Core currently does not enforce node-level required properties (it only enforces connection `required_properties`). Your own Assumptions section says property types are not enforced.
- Options:
  - A) Remove/relax AC33–AC35 to documentation-only expectations (no rejection). Tests should cover presence for happy path creation but must not assert enforcement errors.
  - B) Declare a dependency to enhance graph-memory-core with node-level required property validation (and update timelines accordingly). If choosing B, update the ontology input contract to reflect how required node properties are declared and validated by the core.
- Recommendation: Choose A for Phase 1 to avoid expanding Feature 2 scope; keep enforcement in the conversational layer.

3) Postconditions Omission (Minor)
- Location: specs/proposed/gtd-ontology.md:173
- Issue: Postconditions list omits Context. It says "Can create nodes of type Task, State, UNSPECIFIED".
- Fix: Change to "Task, State, Context, UNSPECIFIED".

4) Coverage Goals Count (Minor)
- Location: specs/proposed/gtd-ontology.md:974-975
- Issue: Still says "All 29 acceptance criteria"; spec now lists 42 (AC1–AC42).
- Fix: Update count accordingly.

5) Roadmap Alignment (Minor doc follow-up)
- Location: ROADMAP.md:91
- Issue: Roadmap says Context nodes deferred to Phase 2. Spec now includes Context in Feature 3.
- Fix: Update Roadmap Feature 3 description to include Context (or explicitly note the change) to keep documents consistent.

## Approval Criteria
To approve:
1. Update the create_ontology payload shape to use `node_types: string[]` and keep node property expectations out of the payload (documentation-only).
2. Resolve AC33–AC35: either remove/relax them (no rejection expected) or add a dependency to enhance graph-memory-core to enforce node required properties and adjust the contract accordingly.
3. Fix minor edits (Postconditions include Context; coverage goals count).
4. Optionally, update Roadmap to reflect Context in Feature 3.

## Next Steps
- [ ] Adjust "Ontology Schema" to align with graph-memory-core input contract.
- [ ] Decide and implement path A or B for node required property validation; update ACs.
- [ ] Correct the Postconditions and Coverage Goals text.
- [ ] Update Roadmap (or file a platform-lead task) to keep planning docs consistent.

