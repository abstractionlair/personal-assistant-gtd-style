# Test Review: Graph Memory Core

**Reviewer:** codex (Test Reviewer)
**Date:** 2025-10-31 17:05:00
**Spec:** specs/doing/graph-memory-core.md
**Test Files:**
- src/graph-memory-core/mcp/tests/unit/memoryGraph.node.lifecycle.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.connection.lifecycle.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.query_and_traversal.test.ts
- src/graph-memory-core/mcp/tests/unit/ontology.validation_and_append.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.cascadeDelete.test.ts
- src/graph-memory-core/mcp/tests/integration/mcp.tools.integration.test.ts
- src/graph-memory-core/mcp/tests/transport/mcp.stdio.e2e.test.ts (auto-skip if SDK missing)
**Status:** NEEDS-CHANGES

## Summary
Excellent iteration. The suite now covers nearly all Acceptance Criteria with clear AAA structure, helpful headers, and isolation via FakeStorage. Add two focused tests to fully satisfy AC8 (error message content) and AC19 (deletion atomicity). Minor style nit: a duplicate import in node.lifecycle test.

## Clarity & Readability
- ✓ Test names descriptive with AC references
- ✓ AAA structure clear
- ✓ Variables meaningful
- ✓ Self-contained tests with local fixtures

## Completeness ⚠ Critical
- ✓ Happy paths: nodes, connections, queries, traversal, search
- ✓ Error cases: invalid types, missing endpoints, non-existent IDs
- ✓ Edge cases: empty content/properties, isolated nodes, multiple connections
- ✓ Ontology protection and append-only behavior
- ✓ Persistence across restart for nodes and connections
- ✓ Atomicity on creation failures via FaultyStorage
- ❌ AC8 message content (“Valid targets: [...]”) not asserted
- ❌ AC19 deletion atomicity (no orphaned files on delete) not asserted

## Coverage Metrics
- Conceptual coverage of ACs is strong. Numeric coverage to be verified post-implementation (RED phase prevents meaningful %).

## Independence
- ✓ No shared mutable state
- ✓ Order-independent
- ✓ Fast, isolated storage double

## Quality
- ✓ Behavior-focused assertions
- ✓ Minimal mocking (single storage double)
- ✓ Headers with spec, author/date, and coverage targets present

## RED Phase Verification
- ✓ Source still throws NotImplementedError in core methods → tests should fail correctly in RED
- ✓ No signature/import issues observed (aside from a duplicate import noted below)

## Critical Issues (NEEDS-CHANGES)

### Issue 1: AC8 requires allowed target types in error output
- Location: src/graph-memory-core/mcp/tests/unit/memoryGraph.connection.lifecycle.test.ts (invalid topology case)
- Problem: Test asserts only InvalidTopologyError type; spec requires error message includes allowed types (e.g., “Valid targets: [Action]”).
- Impact: Weakens contract clarity; implementer may omit helpful diagnostics.
- Fix (example):
  ```ts
  await expect(
    graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: person.node_id })
  ).rejects.toThrow(InvalidTopologyError)

  try {
    await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: person.node_id })
  } catch (err: any) {
    expect(String(err.message)).toMatch(/Valid targets?:\s*\[Action\]/)
    // or, if details are exposed: expect(err.details?.allowed_to_types).toContain('Action')
  }
  ```

### Issue 2: AC19 deletion atomicity (registry and file removed together)
- Location: src/graph-memory-core/mcp/tests/unit/memoryGraph.cascadeDelete.test.ts (and/or new test)
- Problem: Tests verify connection cleanup, but do not assert node content file removal.
- Impact: Risk of orphaned content files undetected.
- Fix (example): After creating a node with content, delete it and assert its file is absent:
  ```ts
  const g = await MemoryGraph.initialize(config, storage)
  await g.createOntology({ node_types: ['Doc'], connection_types: [] })
  const n = await g.createNode({ type: 'Doc', content: 'body', encoding: 'utf-8', format: 'txt' })
  await g.deleteNode({ node_id: n.node_id })
  const exists = await storage.pathExists(`_content/nodes/${n.node_id}.txt`)
  expect(exists).toBe(false)
  ```

## Minor Nits
- Duplicate import of FakeStorage in memoryGraph.node.lifecycle.test.ts — remove the redundant line.

## Positive Notes
- Great coverage additions: required_properties (AC9), query_connections (AC3), direction="both" (AC18), empty/minimal data (AC12), search no-matches (AC16), connection persistence across restart (AC2, AC20), and creation atomicity with FaultyStorage (AC19/AC11).
- Helpful file headers align with Workflow/schema-test-code.md.

## Decision

**NEEDS-CHANGES** — Add the two focused tests above (AC8 message content, AC19 deletion atomicity) and fix the duplicate import. After that, I expect to approve for GREEN phase.

