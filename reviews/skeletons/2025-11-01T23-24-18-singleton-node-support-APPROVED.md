# Skeleton Review: singleton-node-support

**Reviewer**: Codex (Skeleton Reviewer)
**Date**: 2025-11-01
**Spec**: specs/todo/singleton-node-support.md
**Status**: APPROVED

## Summary
Skeleton for the new MCP tool `ensure_singleton_node` is complete, testable, and hollow. Types and input schema match the spec; the server registers the tool; and the core method stub raises NotImplementedError with a clear pointer to the spec. This enables test-writer to proceed.

## Contract Compliance
- Tool registration: src/graph-memory-core/mcp/src/server.ts:476 – name, description, inputSchema set; handler calls graph method.
- Input schema: src/graph-memory-core/mcp/src/server.ts:136 – `type`, optional `content`/`encoding`/`format`/`properties`, `on_multiple` enum.
- Types: src/graph-memory-core/mcp/src/types.ts:352 – Request/Result shapes align with spec, includes `on_multiple` and `INVALID_ARGUMENT` in error code union.
- Core stub: src/graph-memory-core/mcp/src/memoryGraph.ts:604 – `ensureSingletonNode` documented with Throws, returns NotImplementedError (hollow).
- Errors: src/graph-memory-core/mcp/src/errors.ts:145 – `InvalidArgumentError` defined per spec.

## Testability & DI
- Shape allows tests to orchestrate `query_nodes`, `get_node`, `create_node` calls via MemoryGraph’s registry/storage adapters.
- No hard-coded external calls in the stub; DI through existing server bootstrap patterns is respected.

## Docstrings & Hollowness
- JSDoc on stub lists purpose and error conditions; body throws NotImplementedError (no business logic present).

## Non-blocking Notes
- Consider adding an output schema for the tool in server.ts (optional; current pattern doesn’t require).
- When implementing, ensure lexicographic tie-break and `INVALID_ARGUMENT` checks map cleanly to tests.

## Next Steps
- Proceed to test writing for this feature.
