# Spec Review: gtd-ontology

**Reviewer**: Codex (Spec Reviewer)
**Date**: 2025-11-01
**Spec Version**: specs/todo/gtd-ontology.md
**Status**: APPROVED

## Summary
Substantive issues resolved. The ontology schema now matches graph-memory-core (node_types as strings), node-level required-property enforcement was removed (deferring to Feature 4), Context is included and integrated into Next Actions, performance criteria are explicit, and init script contract is clear with idempotency captured in AC5. Minor editorial nits remain but are non-blocking.

## Checklist
- [x] Aligns with Vision/Scope
- [x] Aligns with Roadmap intent (note: roadmap text still defers Context; see Next Steps)
- [x] Interfaces specified
- [x] Happy/edge paths covered
- [x] Error handling feasible with current deps
- [x] Testability verified (38 ACs, 9 scenarios)

## Notes (Non‑Blocking)
- AC1 still mentions only Task/State/UNSPECIFIED; include Context in that parenthetical for precision.
- Error Handling AC30–31 include “if graph-memory-core enforces topology”; core spec does enforce INVALID_TOPOLOGY, so the conditional can be dropped.
- Keep the dependency note for `ensure_singleton_node` visible; AC33 (non‑deletable singleton) depends on that enhancement (or equivalent guard).

## Next Steps
- [ ] Update ROADMAP.md Feature 3 description to reflect Context inclusion (or add a note about the decision change).
- [ ] Tidy AC1 wording to list Context explicitly; optionally remove the “if enforced” wording in AC30–31.

