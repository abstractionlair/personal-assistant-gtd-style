# Test Review: singleton-node-support

**Reviewer**: Codex (Test Reviewer)
**Date**: 2025-11-01
**Spec**: specs/todo/singleton-node-support.md
**Status**: APPROVED

## Summary
Comprehensive, clear tests that map directly to the spec’s acceptance criteria. Unit tests cover tool registration and the `MemoryGraph.ensureSingletonNode` behavior for happy paths, error cases, and edge cases including deterministic selection and tie-breaks. Tests are isolated (FakeStorage), use AAA style, and are framework-consistent (Vitest). Good RED baseline for TDD.

## Coverage vs. Spec
- AC1: Create when absent → unit/memoryGraph.singleton_node.test.ts:40
- AC2: Return existing, no modification → unit/memoryGraph.singleton_node.test.ts:62
- AC3: Default oldest selection → unit/memoryGraph.singleton_node.test.ts:96
- AC3a: `on_multiple = newest` → unit/memoryGraph.singleton_node.test.ts:118
- AC4: ONTOLOGY_NOT_FOUND → unit/memoryGraph.singleton_node.test.ts:177
- AC5: INVALID_NODE_TYPE → unit/memoryGraph.singleton_node.test.ts:155
- AC6: INVALID_ARGUMENT on missing creation fields → unit/memoryGraph.singleton_node.test.ts:140
- AC7: Ignore inputs when node exists (no write) → unit/memoryGraph.singleton_node.test.ts:62
- AC8: Tie-break by lexicographic node_id → unit/memoryGraph.singleton_node.test.ts:140
- Tool registration/delegation → unit/server.ensure_singleton_node.test.ts:26

## Quality & Maintainability
- Descriptive names include AC references; readable Arrange-Act-Assert structure.
- Isolated via FakeStorage; no shared mutable state across tests; timers mocked deterministically.
- Behavior-focused; not coupled to internals beyond documented API surface.

## Notes (Non-Blocking)
- Header comments in two test files reference `specs/doing/singleton-node-support.md`. The spec currently lives at `specs/todo/…`. Either update the header path to `specs/todo/…` or move the spec to `doing/` per workflow before implementation begins.

## Next Steps
- Proceed to GREEN (implementation) for `ensureSingletonNode` per spec.
- Optional: add an integration test round-trip via MCP server once implementation lands (nice-to-have).
