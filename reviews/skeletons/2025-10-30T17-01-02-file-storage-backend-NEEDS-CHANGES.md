# Skeleton Review: File Storage Backend MCP Server

**Reviewer:** Skeleton Reviewer (Codex)
**Date:** 2025-10-30 17:01:02
**Spec:** specs/todo/file-storage-backend.md
**Skeleton Files:**
- src/file-storage-backend/mcp/src/types.ts
- src/file-storage-backend/mcp/src/fileStorage.ts
- src/file-storage-backend/mcp/src/errors.ts
- src/file-storage-backend/mcp/src/localFileStorage.ts
- src/file-storage-backend/mcp/src/server.ts
- src/file-storage-backend/mcp/src/index.ts
**Status:** NEEDS-CHANGES

## Summary
Solid, hollow TypeScript skeleton with clear module headers, explicit error types, and proper dependency injection via LocalFileStorage and FileStorageMcpServer. However, the FileStorage interface method signatures and return type name/shape diverge from the spec’s TypeScript interface. This mismatch will force adapters in tests/implementation and weakens the contract. Recommend aligning signatures exactly and strengthening the file view result typing to match the spec’s invariants.

## Contract Compliance
- ❌ Signatures match spec exactly
- ✓ All functions from spec present
- ✓ All exceptions defined (matching error codes/messages)
- ✓ Data type for file/directory view defined (but name/shape diverge; see issues)

## Testability Assessment ⚠ Critical
- ✓ Dependencies injectable; no hard-coded dependencies in constructors
- ✓ Interfaces abstract and separated from implementation
- ✓ No concrete runtime dependencies baked into signatures
- ✓ SOLID generally respected

## Completeness
- ✓ All methods/classes typed
- ✓ Module headers present with purpose and spec link
- ✓ Methods are hollow (throw NotImplementedError)
- ✓ Error hierarchy covers all codes in spec

## Hollowness Verification
- ✓ No business logic present
- ✓ All public methods throw NotImplementedError
- ✓ No file/db/network work in constructors

## Quality Checks
- Linter: Not run (tooling not configured here)
- Type checker: Not run (no tsconfig or build wiring in repo root)
- Imports: Valid intra-module references; organization consistent
- GUIDELINES.md: Minimal; no conflicts observed

## Critical Issues (NEEDS-CHANGES)

### Issue 1: Interface Signatures Diverge From Spec
- File: src/file-storage-backend/mcp/src/fileStorage.ts:34
- Problem: `view(request: ViewRequest): Promise<FileViewResult>`
  - Spec requires: `view(path: string): Promise<FileContent>`
- Also affects:
  - create at 46 (object param vs `create(path: string, content: string, encoding: 'utf-8' | 'base64')`)
  - str_replace at 58 (object param vs `(path: string, old_str: string, new_str: string)`)
  - insert at 69 (object param vs `(path: string, insert_line: number, new_str: string)`)
  - delete at 80 (object param vs `(path: string)`)
  - rename at 91 (object param vs `(old_path: string, new_path: string)`)
- Impact: Tests and implementation written to the spec will not compile against this interface; introduces avoidable adapters and ambiguity about the canonical contract.
- Fix:
  - Change `FileStorage` to mirror the spec exactly (positional parameters, return `FileContent`).
  - Keep the MCP tool request types for the server layer only; map tool input to interface params inside handlers.

### Issue 2: Return Type Name/Shape Divergence From Spec
- File: src/file-storage-backend/mcp/src/types.ts:51
- Problem: Type named `FileViewResult` with optional fields; spec calls it `FileContent` with strict invariants.
- Impact: Optional fields allow invalid states (e.g., `type: 'file'` without `encoding`/`content`). Tests cannot rely on discriminated union behavior.
- Fix:
  - Rename to `FileContent`.
  - Use a discriminated union to encode invariants:
    - `{ type: 'file'; content: string; encoding: 'utf-8' | 'base64'; size: number }`
    - `{ type: 'directory'; entries: string[] }`

### Issue 3: Server Layer Should Map Tool Input To Spec Interface
- File: src/file-storage-backend/mcp/src/server.ts:82, 88, 94, 100, 106, 112
- Problem: After Issue 1 fix, tool handlers must call `storage.view(input.path)`, etc. Current placeholders assume request-object signatures.
- Impact: Without alignment, the server and storage layers will drift, complicating tests.
- Fix: Adjust handler implementations to extract primitives from tool input and call the updated `FileStorage` signatures.

## Minor Issues
- Types: After renaming/union, ensure all imports in fileStorage.ts reference `FileContent` not `FileViewResult`.
- Strengthen `StorageErrorPayload` doc to note stable messages per spec; current messages already match.
- Consider adding a minimal tsconfig.json and npm scripts so type checks can run in CI later.
- Python skeleton under src/file-storage-backend/src/storage/ appears out-of-scope for this TypeScript MCP server feature and diverges from the spec (e.g., missing `encoding` in create). Recommend deferring or clearly scoping it to a separate feature/spec.

## Testability Score
- Dependency injection: Pass — constructor takes config; server depends on `FileStorage` abstraction.
- Interface abstractions: Pass — interfaces defined; will be better once signatures align with spec.
- Type completeness: Partial — good coverage, but return type should be a discriminated union as per spec invariants.

## Decision

NEEDS-CHANGES — Please address the three critical issues:
1) Align `FileStorage` method signatures and return type name with spec.
2) Update `FileContent` to a discriminated union per invariants.
3) Adjust server tool handlers to map tool input to the updated signatures.

Once updated, I will re-review and expect to approve quickly.

