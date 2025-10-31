# Skeleton Review: Graph Memory Core

**Reviewer:** Codex (Skeleton Reviewer)
**Date:** 2025-10-31 19:10:16 UTC
**Spec:** specs/todo/graph-memory-core.md
**Skeleton Files:**
- src/graph-memory-core/mcp/src/server.ts
- src/graph-memory-core/mcp/src/index.ts
- src/graph-memory-core/mcp/src/memoryGraph.ts
- src/graph-memory-core/mcp/src/ontology.ts
- src/graph-memory-core/mcp/src/registry.ts
- src/graph-memory-core/mcp/src/storageGateway.ts
- src/graph-memory-core/mcp/src/idGenerator.ts
- src/graph-memory-core/mcp/src/errors.ts
- src/graph-memory-core/mcp/src/types.ts
- src/graph-memory-core/mcp/src/constants.ts

**Status:** NEEDS-CHANGES

## Summary
The skeleton maps well to the approved spec: all 18 MCP tools are present and registered, domain services are split cleanly (MemoryGraph/Ontology/Registry), and all external dependencies are injected via interfaces. Domain methods are hollow and raise NotImplementedError. However, method-level JSDoc/docstrings are missing across public methods, which is a required documentation standard for skeletons. Add per-method docs (Args/Returns/Throws) before approval.

## Contract Compliance
- ✓ All 18 MCP tools defined and registered (server.ts)
- ✓ Domain methods for each tool exist in MemoryGraph (memoryGraph.ts)
- ✓ Internal types cover Nodes, Connections, Registry, Ontology (types.ts)
- ✓ Error codes/classes align with spec error table (errors.ts)

## Testability Assessment
- ✓ Dependencies are injectable (GraphStorageGateway, config) — no hard-coded backends
- ✓ Interfaces are abstract (no concrete storage in domain)
- ✓ No concrete dependencies wired into services
- ✓ SOLID boundaries respected (separation of concerns by module)

## Completeness
- ❌ Method-level docstrings/JSDoc missing for public methods (see Critical Issue #1)
- ✓ Module-level headers present
- ✓ Types are explicit (no any)
- ✓ Error hierarchy defined and mapped to payloads

## Hollowness Verification
- ✓ Domain methods raise NotImplementedError and contain no business logic
- ✓ No DB/file/network logic present in skeletons
- ⚠ Minor: helper `ensureOntology()` has a small if/throw guard (acceptable, but keep skeletons as hollow as practical) (src/graph-memory-core/mcp/src/memoryGraph.ts:78)

## Quality Checks
- Linter: not run (no config in repo for TypeScript)
- Type checker: not run (no tsconfig/deps present)
- Import validity: structure appears consistent; ESM-style imports with .js extensions are coherent for TS ESM builds

## Critical Issues (blocking)

### Issue 1: Missing Per-Method Docstrings/JSDoc
- File(s):
  - src/graph-memory-core/mcp/src/memoryGraph.ts:85, 91, 97, 103, 109, 115, 121, 127, 133, 139, 145, 151, 157, 163, 169, 175, 181
  - src/graph-memory-core/mcp/src/ontology.ts:33, 42, 51, 60, 69, 78, 87, 96, 105, 114
  - src/graph-memory-core/mcp/src/registry.ts:32, 41, 50, 59, 68, 77, 86, 95, 104, 113, 122, 131, 140, 149, 158
  - src/graph-memory-core/mcp/src/storageGateway.ts:28–75, 96–115
- Problem: Public methods lack the required documentation (Args, Returns, Raises/Throws). The schema mandates explicit contracts to enable test writing.
- Impact: Test writers lack a precise, discoverable contract at call sites; reviewers cannot verify documented error cases per tool.
- Fix: Add JSDoc blocks for each public method with:
  - Purpose (one sentence)
  - Params with names/types and semantics
  - Returns with type and meaning
  - Throws with specific GraphMemoryError types (link to spec tool numbers where relevant)
  Example:
  ```ts
  /**
   * Register a new node.
   * @param request - See Tool 1 input in specs/todo/graph-memory-core.md
   * @returns Node identifier
   * @throws InvalidNodeTypeError | OntologyNotFoundError | FileCreationFailedError
   */
  async createNode(request: CreateNodeRequest): Promise<CreateNodeResult> { ... }
  ```

## Minor Issues (non-blocking)
- Consider typing external payload `GraphMemoryErrorPayload.code` as the union `GraphMemoryErrorCode` for stronger type safety (src/graph-memory-core/mcp/src/types.ts:286).
- Add a minimal tsconfig and package metadata to enable tsc noEmit checks in CI later.

## Testability Score
- Dependency injection: Pass — `GraphStorageGateway` injected; no hard-coding
- Interface abstractions: Pass — Protocol-style interfaces present
- Type completeness: Pass — exhaustive types; no any

## Decision
NEEDS-CHANGES — Please add per-method JSDoc/docstrings for all public methods in MemoryGraph, Ontology, Registry, and StorageGateway. After that, this skeleton is ready for approval and handoff to test-writer.

