# Spec Review: singleton-node-support

**Reviewer**: Codex (Spec Reviewer)
**Date**: 2025-11-01
**Spec Version**: specs/todo/singleton-node-support.md
**Status**: APPROVED

## Summary
All blocking items addressed. The tool contract now specifies the selection algorithm using query_nodes + get_node, introduces INVALID_ARGUMENT when creation fields are missing, includes AC for on_multiple="newest", and clarifies tie-break semantics. Dependencies and references point to graph-memory-core tool contracts. Concurrency note is appropriate for Phase 1.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap intent
- [x] Interfaces specified and unambiguous
- [x] Happy/edge/error paths covered (9 ACs total)
- [x] Testability verified (deterministic selection + error cases)
- [x] Dependencies precise (query_nodes, get_node, create_node)

## Notes (Non-Blocking)
- Consider adding an optional on_multiple='error' path in a future revision if callers prefer fail-fast over selection.

## Next Steps
- [x] Move spec to specs/todo/ for implementation and test writing.

