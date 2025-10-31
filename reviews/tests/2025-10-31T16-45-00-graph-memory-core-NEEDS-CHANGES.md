# Test Review: Graph Memory Core

**Reviewer:** codex (Test Reviewer)
**Date:** 2025-10-31 16:45:00
**Spec:** specs/doing/graph-memory-core.md
**Test Files:**
- src/graph-memory-core/mcp/tests/unit/memoryGraph.node.lifecycle.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.connection.lifecycle.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.query_and_traversal.test.ts
- src/graph-memory-core/mcp/tests/unit/ontology.validation_and_append.test.ts
- src/graph-memory-core/mcp/tests/unit/memoryGraph.cascadeDelete.test.ts
- src/graph-memory-core/mcp/tests/integration/mcp.tools.integration.test.ts
**Status:** NEEDS-CHANGES

## Summary
Solid foundation with clear, behavior-focused tests that reference ACs and use an isolated FakeStorage. However, coverage is incomplete against the spec’s 20 Acceptance Criteria (AC1–AC20). Key gaps include error-path coverage, query_connections, required properties, direction="both", empty/minimal cases, multi-connection scenarios, atomicity/consistency, and connection persistence across restart. Add the missing cases below to meet quality and completeness bars before GREEN phase.

## Clarity & Readability
- ✓ Test names descriptive
- ✓ AAA structure clear
- ✓ Variables meaningful
- ✓ Self-contained tests

## Completeness ⚠ Critical
- ✓ Happy path covered (nodes, connections, search, traversal)
- ❌ Edge cases covered (several missing)
- ❌ Error cases covered (several missing)
- ❌ All spec exceptions tested (missing for AC6–AC9)
- n/a Sentinel tests present (no bugs/fixed/ relevant)

## Coverage Metrics ⚠ Critical
- ❌ Line coverage ≥80% (cannot verify numerically here; expected below target due to missing ACs)
- ❌ Branch coverage ≥70% (same)
- ❌ All public methods covered (query_connections, various error paths not covered)
- ❌ All error paths covered
- ❌ Critical business logic covered (atomicity/consistency not exercised)

## Independence
- ✓ No shared state (fresh FakeStorage + config in beforeEach)
- ✓ Tests run in any order
- ✓ Each test has own fixtures

## Quality
- ✓ Tests behavior not implementation
- ✓ Minimal mocking (single FakeStorage double)
- ✓ Specific assertions
- ✓ Spec alignment referenced (AC numbers embedded)

## RED Phase Verification
- ✓ All tests expected to fail in RED due to NotImplementedError stubs present in src (MemoryGraph and adapters)
- ✓ Failing with NotImplementedError (by design, e.g., MemoryGraph.initialize and others throw)
- ✓ No import/signature errors visible on inspection

## Critical Issues (NEEDS-CHANGES)

### Issue 1: Missing AC coverage for error cases (AC6, AC7, AC8)
- Problem: Several required error paths lack tests.
- Impact: Implementer could miss error handling; regressions not caught.
- Fix: Add tests:
  - AC6: update_node with non-existent ID → NodeNotFoundError; delete_node non-existent → NodeNotFoundError.
  - AC7: get_connection with non-existent ID → ConnectionNotFoundError.
  - AC8: create_node with type not in ontology → InvalidNodeTypeError; optionally assert message includes allowed types when topology fails.

### Issue 2: Missing required properties enforcement (AC9)
- Problem: No tests for connection types that require properties.
- Impact: Implementation may not enforce required_properties.
- Fix: In connection lifecycle tests, define a connection type with required_properties and verify:
  - Creation without them fails with RequiredPropertyMissingError (and lists which properties).
  - Creation with all required properties succeeds.

### Issue 3: Query coverage gaps (AC3, AC11)
- Problem: No tests for query_connections and for registry integrity after failures.
- Impact: Query correctness and registry consistency could drift.
- Fix:
  - Add query_connections tests: filter by from/to/type; ensure IDs match expected.
  - Add a registry consistency smoke test: after a failing operation (e.g., invalid type), subsequent valid operations still succeed and previously created entries remain readable.

### Issue 4: Direction handling incomplete (AC18)
- Problem: Only "in" and "out" tested.
- Impact: "both" semantics unverified.
- Fix: Add get_connected_nodes with direction="both" returning union of in/out without duplicates.

### Issue 5: Empty/minimal data not covered (AC12)
- Problem: No tests for empty content, empty properties, optional content.
- Impact: Minimal contract behavior unverified.
- Fix: Add tests to create node with empty string content and {} properties; create connection without optional content; query_nodes with no filters returns all nodes.

### Issue 6: Nodes without connections, multiple connections (AC13, AC14)
- Problem: Isolation and multiplicity semantics not tested.
- Impact: Traversal and deletion logic may break unnoticed.
- Fix:
  - AC13: get_connected_nodes on isolated node returns empty array; deleting standalone node succeeds.
  - AC14: multiple outgoing connections of same type; different types between same pair; deleting one connection doesn’t affect others.

### Issue 7: Property filter edge cases (AC15)
- Problem: Only AND semantics partially covered.
- Impact: Filtering edge cases unverified.
- Fix: Add test for empty properties filter {} matching all nodes of specified type; ensure nodes with extra props still match (already implicitly shown, but add explicit assertion).

### Issue 8: Content search gaps (AC16)
- Problem: "no matches" case not tested.
- Impact: Edge behavior unverified.
- Fix: Add search_content with a query that matches nothing → returns empty array.

### Issue 9: Persistence across restart for connections (AC2, AC20)
- Problem: Integration tests verify node persistence, not connection persistence.
- Impact: Connection registry persistence unverified.
- Fix: Extend integration to create a connection, re-initialize, then get_connection and traversal to confirm persistence.

### Issue 10: Atomicity and consistency (AC19, AC11)
- Problem: No tests simulate partial failures (e.g., file write failure).
- Impact: Risk of orphaned files or corrupt registry.
- Fix: Introduce a FaultyStorage test double that throws on specific operations (e.g., writeText once), then assert operation leaves no partial registry entries or orphaned files.

### Issue 11: File extension mapping (spec rule)
- Problem: No test verifies extension mapping by encoding (utf-8 → .txt, base64 → .bin).
- Impact: Encoding/format separation could drift.
- Fix: Using FakeStorage.listDirectory("_content/nodes") after creating nodes with utf-8 vs base64, assert filenames end with .txt vs .bin respectively and that update_node changing encoding switches extension.

### Issue 12: Missing file header metadata per schema
- Problem: Tests lack file header referencing spec, author/date, and coverage targets.
- Impact: Harder traceability and review.
- Fix: Add header comment blocks as per Workflow/schema-test-code.md to each test file.

## Missing Test Cases
1. test_update_node_nonexistent_id_raises_node_not_found (AC6)
2. test_delete_node_nonexistent_id_raises_node_not_found (AC6)
3. test_get_connection_nonexistent_id_raises_connection_not_found (AC7)
4. test_create_node_with_invalid_type_raises_invalid_node_type (AC8)
5. test_create_connection_missing_required_properties_raises_error (AC9)
6. test_create_connection_with_required_properties_succeeds (AC9)
7. test_query_connections_filters_by_from_to_and_type (AC3)
8. test_get_connected_nodes_direction_both_returns_union (AC18)
9. test_create_node_with_empty_content_and_empty_properties (AC12)
10. test_query_nodes_no_filters_returns_all_nodes (AC12)
11. test_get_connected_nodes_on_isolated_node_returns_empty (AC13)
12. test_multiple_connections_same_type_and_different_types (AC14)
13. test_query_nodes_with_empty_properties_matches_all_of_type (AC15)
14. test_search_content_no_matches_returns_empty (AC16)
15. test_connection_persists_across_restart (AC2, AC20)
16. test_atomicity_node_creation_failure_does_not_write_partial_registry (AC19, AC11)
17. test_encoding_changes_update_file_extension_txt_bin (spec rule)

## Positive Notes
- Good AAA structure, descriptive names, and spec AC references in test names.
- Clean isolation via FakeStorage; no shared state.
- Integration test exercises tool registration and error mapping.
- Useful coverage for query_nodes AND semantics and search basics.

## Decision

**NEEDS-CHANGES** - Address the critical gaps above (especially AC6–AC9, AC12–AC16, AC18–AC20, atomicity/consistency) and add the proposed tests. Once added, we should run with coverage to verify ≥80% line and ≥70% branch coverage before GREEN phase.

