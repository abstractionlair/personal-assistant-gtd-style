# Specification: Singleton Node Support

**Feature ID:** feature_graph_singleton_node
**Version:** 0.1.0
**Status:** Draft
**Created:** 2025-11-01
**Author:** spec-writer

## Overview

Provide a minimal, deterministic way to get-or-create a single node instance for a given node type without changing the ontology or storage schema. This enables system-wide configuration and other unique resources (e.g., “WorkspaceConfig”, “UserProfile”) to exist as a single authoritative node while remaining compatible with the current binary-edge graph model.

## Feature Scope

### Included
- New MCP tool ensure_singleton_node to return the one canonical node for a type, creating it if absent.
- Deterministic selection when multiple nodes of the type already exist (choose oldest by created timestamp).
- No updates to existing node if one already exists (read-only in that case).

### Excluded (Not in This Feature)
- Ontology changes (no singleton flags in types).
- Hard prevention of duplicates or migration to remove existing duplicates.
- Content/property updates of an existing singleton via this tool.

### Deferred (Maybe in This Feature)
- Optional on_multiple='error' mode and corresponding error code.
- Helper to “repair” duplicates (merge or mark deprecated) if encountered.

## User/System Perspective

- Callers can reliably fetch a singleton node for a type in one step, with idempotent behavior: create if missing; otherwise return the same id on subsequent calls.
- If historical duplicates exist, the system consistently returns the earliest-created node to avoid churn.

## Value Delivered

- Simplifies patterns that need a unique, canonical record (configuration, profile, catalog root) without introducing a new schema or breaking changes.
- Avoids premature ontology complexity while unblocking immediate needs.

## Interface Contract

### Tool: ensure_singleton_node(request) -> { node_id: string, created: boolean }

**Purpose:** Return the canonical node id for the given node type, creating it if none exist.

**Parameters:**
- type (string): Node type name (must exist in ontology).
- content (string): Initial content for creation (used only if node is created).
  - Constraints: Required for creation; ignored if node already exists.
- encoding ("utf-8" | "base64"): Encoding of content for creation; required if creating.
- format (string): Logical content format (e.g., "markdown", "json"); required if creating.
- properties (Record<string, string|number|boolean>, optional): Initial properties for creation; ignored if node already exists.
- on_multiple ("oldest" | "newest", optional): Selection strategy when multiple nodes of the type exist; default "oldest" (by created timestamp).

**Returns:**
- { node_id: string, created: boolean }
  - node_id: The canonical node identifier.
  - created: True if a new node was created; false if an existing node was returned.

**Raises:**
- ONTOLOGY_NOT_FOUND: Ontology not initialized.
- INVALID_NODE_TYPE: Provided type is not defined in ontology.
 - INVALID_ARGUMENT: When no node exists and any of content/encoding/format is missing for creation.

**Preconditions:**
- Ontology exists and defines the provided node type.
 - If no node of the type exists, caller must supply content, encoding, and format.

**Postconditions:**
- If no node of the type exists, exactly one node is created with the provided content/encoding/format/properties.
- If one or more exist, no write occurs; the selected existing node id is returned.
 - Selection semantics when multiple exist:
   - Default `on_multiple = "oldest"`: choose the minimal `created` timestamp.
   - If `on_multiple = "newest"`: choose the maximal `created` timestamp.
   - Tie-breaker when `created` timestamps are equal: choose lexicographically smallest `node_id` (stable across runs).

**Example Usage:**
```json
{
  "type": "WorkspaceConfig",
  "content": "{\n  \"inbox\": \"inbox.md\"\n}",
  "encoding": "utf-8",
  "format": "json",
  "properties": { "version": 1 },
  "on_multiple": "oldest"
}
```

**Selection Algorithm:**
1. Call `query_nodes({ type })` to obtain candidate `node_ids`.
2. For each candidate id, call `get_node({ node_id })` to read `created` timestamps.
3. Select according to `on_multiple` (default: minimal `created`; if `newest`: maximal `created`); apply tie-breaker by lexicographic `node_id` when timestamps equal.
4. If no candidates exist:
   - Validate that `content`, `encoding`, and `format` are provided; otherwise raise `INVALID_ARGUMENT`.
   - Call `create_node({ type, content, encoding, format, properties })` and return the new `node_id` with `created: true`.
5. If one or more candidates exist: return the selected `node_id` with `created: false`.

## Acceptance Criteria

### Happy Path
1. ✓ When no nodes of the given type exist, the tool creates one and returns { created: true } with a valid node_id.
2. ✓ When exactly one node exists, the tool returns its id and { created: false } without modifying content or properties.
3. ✓ When multiple nodes exist, the tool returns the deterministically selected node (default: oldest by created timestamp) and { created: false }.
3a. ✓ When multiple nodes exist and `on_multiple` is set to `"newest"`, the tool returns the node with the maximal `created` timestamp (tie-break: smallest node_id) and { created: false }.

### Error Handling
4. ✓ If the ontology is missing, the tool fails with ONTOLOGY_NOT_FOUND.
5. ✓ If the node type is not defined, the tool fails with INVALID_NODE_TYPE.
6. ✓ If no node exists and any of content/encoding/format is missing, the tool fails with INVALID_ARGUMENT (no node is created).

### Edge Cases
7. ✓ If content/encoding/format are provided but a node already exists, inputs are ignored and no write occurs.
8. ✓ If multiple nodes share the same created timestamp, selection is stable by secondary key (lexicographic id ascending).

## Scenarios

### Scenario 1: Create Absent Singleton
**Given:** Ontology exists with node type "WorkspaceConfig" and no such nodes present
**When:** ensure_singleton_node({ type: "WorkspaceConfig", content: "{}", encoding: "utf-8", format: "json" })
**Then:** Returns a new node_id; created == true; exactly one node of type exists

### Scenario 2: Return Existing Singleton
**Given:** Ontology exists; exactly one node of type "WorkspaceConfig" exists (id: mem_001)
**When:** ensure_singleton_node({ type: "WorkspaceConfig", content: "{}", encoding: "utf-8", format: "json" })
**Then:** Returns node_id == "mem_001"; created == false; no writes performed

### Scenario 3: Multiple Existing Nodes (Deterministic Selection)
**Given:** Ontology exists; two nodes of type "WorkspaceConfig" exist (mem_001 created earlier, mem_002 later)
**When:** ensure_singleton_node({ type: "WorkspaceConfig", content: "{}", encoding: "utf-8", format: "json" })
**Then:** Returns node_id == "mem_001"; created == false; no writes performed

### Scenario 3b: Multiple Existing Nodes (Newest Selection)
**Given:** Ontology exists; two nodes of type "WorkspaceConfig" exist (mem_001 created earlier, mem_002 later)
**When:** ensure_singleton_node({ type: "WorkspaceConfig", on_multiple: "newest", content: "{}", encoding: "utf-8", format: "json" })
**Then:** Returns node_id == "mem_002"; created == false; no writes performed

### Scenario 4: Invalid Node Type
**Given:** Ontology exists without node type "Foo"
**When:** ensure_singleton_node({ type: "Foo", content: "-", encoding: "utf-8", format: "text" })
**Then:** Fails with INVALID_NODE_TYPE

### Scenario 5: Ontology Missing
**Given:** Ontology has not been created
**When:** ensure_singleton_node({ type: "WorkspaceConfig", content: "{}", encoding: "utf-8", format: "json" })
**Then:** Fails with ONTOLOGY_NOT_FOUND

## Dependencies
- Graph Memory Core MCP server (existing): uses `query_nodes` to list candidates, `get_node` to read `created` timestamps for selection, and `create_node` for creation when absent.
- No changes to ontology or registry schemas.

## References
- specs/done/graph-memory-core.md — Tool contracts for `create_node`, `get_node`, and `query_nodes`.

## Notes
- Concurrency: This tool does not introduce cross-process locking; under rare races, two creates may occur and multiple callers may observe `created: true`. Subsequent calls deterministically return the selected node (per `on_multiple`) with `created: false`. If stronger guarantees are later needed, consider an ontology-level singleton flag plus storage-level atomic claim mechanics.
