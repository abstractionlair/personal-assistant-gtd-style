# Specification: Graph Memory Core

**Feature ID:** phase1-feature2
**Version:** 1.1
**Status:** Review
**Created:** 2025-10-31
**Updated:** 2025-10-31 (addressing review feedback)
**Author:** spec-writing-helper (collaborative)

---

## Overview

The Graph Memory Core is a generic, ontology-driven graph-based memory system that provides the foundation for structured knowledge storage across domains. It exposes MCP tools for creating typed nodes, establishing typed connections between them, and querying the resulting graph structure. The system validates all operations against a configurable ontology that defines valid node types, connection types, and topology rules.

This feature delivers the reusable memory infrastructure required by the GTD layer (Feature 3) and enables future domain extensions (fitness, finance, learning) by supporting arbitrary ontologies. Built on the file-storage-backend (Feature 1), it maintains graph metadata in a registry while storing rich content in files, balancing query performance with flexible content storage.

---

## Feature Scope

### Included

- **Node lifecycle operations** - create, read, update, delete typed nodes with content and properties
- **Connection lifecycle operations** - create, read, update, delete typed connections with properties
- **Ontology management** - create, append-only extension, retrieval, and validation
- **Graph queries** - query nodes by type/properties, query connections by from/to/type/properties, traverse connections
- **Content search** - keyword/substring search across node content files
- **Registry persistence** - atomic save/load of graph metadata to `_system/registry.json`
- **Cascade delete** - deleting nodes automatically removes all connected connections
- **MCP server exposure** - 18 MCP tools for all graph operations
- **File-storage integration** - uses Feature 1 for all file operations
- **Atomic operations** - operations succeed completely or fail cleanly

### Excluded (Not in This Feature)

- **Semantic search / embeddings** - no `recall()` with vector similarity, only keyword `search_content()`
- **Multi-operation transactions** - no rollback across multiple tool calls (individual operations are atomic)
- **Caching layer** - direct registry/file operations on each request
- **User preferences/context memory** - that's Anthropic Memory Server (separate system)
- **GTD-specific logic** - graph layer remains domain-agnostic
- **Query optimization** - linear scans acceptable for MVP scale (~10k nodes)
- **Batch operations** - one operation per MCP tool call

### Deferred (Maybe in This Feature)

If timeline becomes tight, these can be simplified or deferred to Phase 2:
- **Complex ontology validation** - circular connection detection, advanced topology rules
- **Transaction rollback safety** - multi-step rollback on partial failures
- **Advanced error handling** - detailed error recovery strategies

---

## User/System Perspective

**From Claude's perspective (via MCP tools):**
- Can create typed nodes (e.g., Projects, Actions) with rich markdown content and queryable properties
- Can establish typed connections (e.g., NextAction, DependsOn) between nodes with validation against ontology rules
- Can query the graph structure ("find all Actions with status='next' and context='phone'")
- Can traverse connections ("get all nodes connected via NextAction from this Project")
- Can search content ("find nodes mentioning 'kitchen renovation'")
- Memory persists across conversation restarts (registry and files survive server restart)

**From GTD Ontology Layer's perspective (Feature 3):**
- Defines GTD ontology (Project, Action, NextAction, DependsOn types)
- Uses graph operations to store and query GTD structures
- Relies on topology validation (e.g., NextAction only from Project to Action)
- No need to understand files, registry, or storage internals

**From Developer's perspective:**
- MCP server registered in Claude Code configuration
- Files appear in configured base directory (`_system/`, `_content/nodes/`, etc.)
- Can inspect registry JSON and content files manually if needed
- Server starts/stops with Claude Code

---

## Value Delivered

This feature solves the foundational problem of structured, queryable memory for intelligent agents. Without a graph-based system, relationships between entities (Projects depend on Actions, Actions block other Actions) would be implicit and fragile, requiring the conversational layer to maintain consistency manually.

By providing ontology-driven validation, the system prevents invalid graph states (e.g., creating connections between incompatible node types). By separating minimal properties (in registry) from rich content (in files), it enables fast queries while supporting arbitrarily detailed information.

This delivers the "graph memory as cognitive architecture" foundation described in VISION.md, enabling the assistant to reason about structured relationships rather than just retrieving flat task lists. The generic, ontology-driven design enables future domain extensions beyond GTD.

---

## Interface Contract

### MCP Server Configuration

**Server Name:** `graph-memory-core`

**Configuration Schema:**
```typescript
{
  basePath: string  // Absolute path to memory storage directory
}
```

**Example Configuration (Claude Code):**
```json
{
  "mcpServers": {
    "graph-memory-core": {
      "command": "node",
      "args": ["/path/to/graph-memory-core/dist/index.js"],
      "env": {
        "BASE_PATH": "/Users/username/gtd-memory"
      }
    }
  }
}
```

---

### Key Design Clarifications

#### Property Value Constraints

Properties on nodes and connections support the following value types:
- **string** - Text values (case-sensitive matching)
- **number** - Numeric values (compared by value)
- **boolean** - True/false values (exact matching)

**Not supported in MVP:**
- Nested objects or arrays as property values
- Null values (use absence of key instead)

**Query Matching Semantics:**
- `query_nodes` and `query_connections` match ALL specified properties (AND logic)
- String matching is case-sensitive and requires exact equality
- Number matching compares by value
- Nodes/connections with additional properties beyond those queried still match

**Examples:**
```typescript
// Valid properties
{ status: "active", priority: 1, urgent: true }

// Invalid (arrays not supported)
{ tags: ["important", "urgent"] }  // ❌

// Invalid (nested objects not supported)
{ metadata: { created_by: "user" } }  // ❌
```

#### Property Removal

**Property removal is not supported in MVP.** The `update_node` and `update_connection` operations merge provided properties with existing ones but cannot remove properties.

**Workarounds:**
- To remove a property, delete and recreate the node/connection
- Or, set a sentinel value like `{ status: "none" }` and filter in queries

This may be added in a future version if needed.

#### Content Format and Encoding

**Format vs Encoding:**
- **`encoding`** parameter ("utf-8" | "base64") determines how content is stored - this is passed to file-storage-backend
- **`format`** parameter (string) is opaque client metadata - the graph memory system stores it but doesn't interpret it

Clients use `format` to track content types (e.g., "markdown", "pdf", "meeting-notes") for their own purposes. The system uses format only to determine file extensions.

**Format Mutability:**
- Format can be changed via `update_node` - it's just metadata
- Encoding can also be changed if content is re-provided in different encoding

#### Connection Content Storage

When connections have optional content, it is stored at:
```
_content/connections/{connection_id}.md
```

This is an implementation detail - clients don't need to know the path, they use `get_connection` and related tools.

#### Error Codes Reference

| Error Code | Triggered By | Meaning |
|---|---|---|
| `ONTOLOGY_NOT_FOUND` | Most operations | Ontology must be created before using graph operations |
| `ONTOLOGY_ALREADY_EXISTS` | `create_ontology` | Cannot create ontology twice |
| `TYPE_ALREADY_EXISTS` | `add_node_type`, `add_connection_type` | Type name already defined in ontology |
| `INVALID_NODE_TYPE` | `create_node` | Node type doesn't exist in ontology |
| `INVALID_CONNECTION_TYPE` | `create_connection` | Connection type doesn't exist in ontology |
| `INVALID_TOPOLOGY` | `create_connection` | Source/target node types incompatible with connection type |
| `REQUIRED_PROPERTY_MISSING` | `create_connection` | Connection type requires properties that weren't provided |
| `NODE_NOT_FOUND` | Node operations | Node ID doesn't exist in registry |
| `CONNECTION_NOT_FOUND` | Connection operations | Connection ID doesn't exist in registry |
| `FILE_CREATION_FAILED` | `create_node`, `create_connection` | Could not create content file |
| `CONTENT_READ_FAILED` | `get_node_content` | Could not read content file |

---

### Tool 1: create_node

**Purpose:** Create a new typed node with content

**Input Schema:**
```typescript
{
  type: string,              // Node type from ontology
  content: string,           // Node content (utf-8 text or base64-encoded binary)
  encoding: "utf-8" | "base64",  // Content encoding
  format: string,            // Content format (opaque client metadata, e.g., "markdown", "pdf")
  properties?: object        // Optional key-value properties for queries
}
```

**Parameters:**
- `type` (string): Node type from ontology
  - Constraints: Must exist in ontology
  - Example: "Project", "Action", "Context"
- `content` (string): Node content
  - Example: "# Kitchen Renovation\n\nBudget: $50k"
- `encoding` ("utf-8" | "base64"): Content encoding
  - "utf-8": Text content (used for markdown, json, txt, yaml, etc.)
  - "base64": Base64-encoded binary content (used for pdf, images, etc.)
  - Note: System passes encoding to file-storage-backend for proper handling
- `format` (string): Content format metadata
  - Examples: "markdown", "json", "pdf", "png"
  - **Important:** Format is opaque client metadata - the graph memory system stores it but doesn't interpret it. Clients use format to track content type for their own purposes.
  - The system uses format to determine file extension (e.g., "markdown" → .md, "pdf" → .pdf)
- `properties` (object, optional): Key-value properties for queries
  - Example: `{ status: "active", priority: 1 }`
  - Constraints: Values must be string, number, or boolean (no nested objects/arrays in MVP)
  - See "Property Value Constraints" section below for details

**Returns:**
- `node_id` (string): Unique node identifier (opaque string)
  - Example: "mem_k4j9x2_p8n3q1" (format is implementation detail, do not depend on structure)

**Raises:**
- `INVALID_NODE_TYPE`: Node type doesn't exist in ontology
- `ONTOLOGY_NOT_FOUND`: Ontology hasn't been created yet
- `FILE_CREATION_FAILED`: Could not create content file

**Preconditions:**
- Ontology must exist with the specified node type
- Properties (if provided) must be valid JSON object
- Base directory must be writable

**Postconditions:**
- Node entry added to `_system/registry.json` with generated ID
- Content file created at `_content/nodes/{id}.{extension}`
- Node is immediately queryable via `query_nodes()`
- Subsequent `get_node(id)` returns the node metadata
- `modified` and `created` timestamps set to current time

**Example Usage:**
```typescript
create_node({
  type: "Project",
  content: "# Kitchen Renovation\n\nBudget: $50k\nTimeline: Q1 2026",
  encoding: "utf-8",
  format: "markdown",
  properties: { status: "active" }
})
// → { node_id: "mem_k4j9x2_p8n3q1" }
```

---

### Tool 2: get_node

**Purpose:** Retrieve node metadata (not content)

**Input Schema:**
```typescript
{
  node_id: string
}
```

**Parameters:**
- `node_id` (string): Node identifier
  - Example: "mem_k4j9x2_p8n3q1"

**Returns:**
```typescript
{
  id: string,
  type: string,
  created: string,      // ISO 8601 timestamp
  modified: string,     // ISO 8601 timestamp
  properties: object,   // Key-value properties
  content_format: string
}
```

**Raises:**
- `NODE_NOT_FOUND`: Node ID doesn't exist in registry

**Preconditions:**
- Node must exist in registry

**Postconditions:**
- No state changes (read-only operation)

**Example Usage:**
```typescript
get_node({ node_id: "mem_k4j9x2_p8n3q1" })
// → {
//   id: "mem_k4j9x2_p8n3q1",
//   type: "Project",
//   created: "2025-10-31T10:00:00Z",
//   modified: "2025-10-31T15:30:00Z",
//   properties: { status: "active" },
//   content_format: "markdown"
// }
```

---

### Tool 3: get_node_content

**Purpose:** Retrieve node content file

**Input Schema:**
```typescript
{
  node_id: string
}
```

**Parameters:**
- `node_id` (string): Node identifier

**Returns:**
- `content` (string): Node content

**Raises:**
- `NODE_NOT_FOUND`: Node ID doesn't exist
- `CONTENT_READ_FAILED`: Could not read content file

**Preconditions:**
- Node must exist with content file

**Postconditions:**
- No state changes (read-only operation)

**Example Usage:**
```typescript
get_node_content({ node_id: "mem_k4j9x2_p8n3q1" })
// → "# Kitchen Renovation\n\nBudget: $50k\nTimeline: Q1 2026"
```

---

### Tool 4: update_node

**Purpose:** Update node properties and/or content

**Input Schema:**
```typescript
{
  node_id: string,
  properties?: object,   // Optional: updated properties (merged)
  content?: string,      // Optional: new content (replaces existing)
  encoding?: "utf-8" | "base64",  // Optional: content encoding (required if content provided)
  format?: string        // Optional: update format metadata
}
```

**Parameters:**
- `node_id` (string): Node identifier
- `properties` (object, optional): Updated properties
  - Behavior: Merged with existing (new keys added, existing keys updated, unspecified keys unchanged)
  - Note: Property removal not supported - see "Property Removal" section
  - Constraints: Values must be string, number, or boolean
- `content` (string, optional): New content
  - Behavior: Replaces existing content file completely
  - If provided, `encoding` must also be provided
- `encoding` ("utf-8" | "base64", optional): Content encoding
  - Required if `content` is provided
  - Can change encoding when updating content
- `format` (string, optional): Update format metadata
  - Format can be changed independently of content
  - System uses format to determine file extension if content changes

**Returns:**
- void (success) or error

**Raises:**
- `NODE_NOT_FOUND`: Node ID doesn't exist
- `INVALID_ENCODING`: encoding not provided when content is provided

**Preconditions:**
- Node must exist
- At least one of `properties`, `content`, or `format` must be provided
- If `content` provided, `encoding` must also be provided

**Postconditions:**
- `modified` timestamp updated to current time
- If properties provided: Properties merged into existing (no removal)
- If content provided: Content file replaced with new encoding
- If format provided: Format metadata updated
- Changes persisted to registry immediately

**Example Usage:**
```typescript
update_node({
  node_id: "mem_k4j9x2_p8n3q1",
  properties: { status: "completed" },
  content: "# Kitchen Renovation\n\n**COMPLETED Q1 2026**\n\nFinal cost: $48k"
})
```

---

### Tool 5: delete_node

**Purpose:** Delete node and all its connections

**Input Schema:**
```typescript
{
  node_id: string
}
```

**Parameters:**
- `node_id` (string): Node identifier

**Returns:**
- void (success) or error

**Raises:**
- `NODE_NOT_FOUND`: Node ID doesn't exist

**Preconditions:**
- Node must exist

**Postconditions:**
- Node removed from registry
- Content file deleted from `_content/nodes/`
- **All connections to/from this node deleted** (cascade delete)
- Subsequent `get_node(id)` throws `NODE_NOT_FOUND`
- Connected nodes remain (only connections removed, not target nodes)

**Example Usage:**
```typescript
delete_node({ node_id: "mem_k4j9x2_p8n3q1" })
```

---

### Tool 6: create_connection

**Purpose:** Create typed connection between two nodes

**Input Schema:**
```typescript
{
  type: string,              // Connection type from ontology
  from_node_id: string,      // Source node ID
  to_node_id: string,        // Target node ID
  properties?: object,       // Optional key-value properties
  content?: string           // Optional relationship notes/details
}
```

**Parameters:**
- `type` (string): Connection type from ontology
  - Example: "NextAction", "DependsOn", "RequiresContext"
- `from_node_id` (string): Source node ID
- `to_node_id` (string): Target node ID
- `properties` (object, optional): Connection properties
  - Example: `{ priority: "high", added: "2025-10-31" }`
- `content` (string, optional): Relationship notes
  - Example: "High priority because deadline approaching"

**Returns:**
- `connection_id` (string): Unique connection identifier
  - Example: "conn_x7y2z9_k5m8n3"

**Raises:**
- `INVALID_CONNECTION_TYPE`: Connection type doesn't exist in ontology
- `NODE_NOT_FOUND`: Either from_node_id or to_node_id doesn't exist
- `INVALID_TOPOLOGY`: Node types cannot be connected with this connection type
  - Example: Can't create NextAction from Action to Project (only Project to Action)
- `REQUIRED_PROPERTY_MISSING`: Ontology requires properties that weren't provided
  - Example: WaitingFor requires "since" and "follow_up_date"

**Preconditions:**
- Both nodes must exist
- Connection type must exist in ontology
- Node types must satisfy ontology topology rules
- All required properties must be provided

**Postconditions:**
- Connection entry added to registry with generated ID
- If content provided, stored alongside connection
- Connection queryable via `query_connections()`
- `created` and `modified` timestamps set to current time

**Example Usage:**
```typescript
create_connection({
  type: "NextAction",
  from_node_id: "mem_k4j9x2_p8n3q1",
  to_node_id: "mem_m3n7k1_q9r4t2",
  properties: { priority: "high", added: "2025-10-31" }
})
// → { connection_id: "conn_x7y2z9_k5m8n3" }
```

---

### Tool 7: get_connection

**Purpose:** Retrieve connection metadata

**Input Schema:**
```typescript
{
  connection_id: string
}
```

**Parameters:**
- `connection_id` (string): Connection identifier

**Returns:**
```typescript
{
  id: string,
  type: string,
  from_node_id: string,
  to_node_id: string,
  created: string,
  modified: string,
  properties: object,
  has_content: boolean
}
```

**Raises:**
- `CONNECTION_NOT_FOUND`: Connection ID doesn't exist

**Example Usage:**
```typescript
get_connection({ connection_id: "conn_x7y2z9_k5m8n3" })
// → {
//   id: "conn_x7y2z9_k5m8n3",
//   type: "NextAction",
//   from_node_id: "mem_k4j9x2_p8n3q1",
//   to_node_id: "mem_m3n7k1_q9r4t2",
//   created: "2025-10-31T10:15:00Z",
//   modified: "2025-10-31T10:15:00Z",
//   properties: { priority: "high" },
//   has_content: false
// }
```

---

### Tool 8: update_connection

**Purpose:** Update connection properties and/or content

**Input Schema:**
```typescript
{
  connection_id: string,
  properties?: object,
  content?: string
}
```

**Parameters:**
- `connection_id` (string): Connection identifier
- `properties` (object, optional): Updated properties (merged)
- `content` (string, optional): New content (replaces existing)

**Returns:**
- void (success) or error

**Raises:**
- `CONNECTION_NOT_FOUND`: Connection ID doesn't exist

**Postconditions:**
- `modified` timestamp updated to current time
- Properties merged if provided
- Content replaced if provided

**Example Usage:**
```typescript
update_connection({
  connection_id: "conn_x7y2z9_k5m8n3",
  properties: { priority: "medium" }
})
```

---

### Tool 9: delete_connection

**Purpose:** Delete connection (nodes remain)

**Input Schema:**
```typescript
{
  connection_id: string
}
```

**Parameters:**
- `connection_id` (string): Connection identifier

**Returns:**
- void (success) or error

**Raises:**
- `CONNECTION_NOT_FOUND`: Connection ID doesn't exist

**Postconditions:**
- Connection removed from registry
- Connected nodes remain unchanged (only relationship removed)

**Example Usage:**
```typescript
delete_connection({ connection_id: "conn_x7y2z9_k5m8n3" })
```

---

### Tool 10: query_nodes

**Purpose:** Find nodes by type and/or properties

**Input Schema:**
```typescript
{
  type?: string,        // Optional: filter by node type
  properties?: object   // Optional: filter by properties (AND logic)
}
```

**Parameters:**
- `type` (string, optional): Filter by node type
  - Example: "Action"
- `properties` (object, optional): Filter by properties (exact match on ALL specified keys)
  - Example: `{ status: "next", context: "phone" }`
  - Behavior: Returns nodes where ALL specified properties match
  - Nodes with extra properties still match

**Returns:**
- `node_ids` (array of strings): Matching node IDs
  - Empty array if no matches

**Raises:**
- None (empty result if no matches)

**Preconditions:**
- If type specified, must exist in ontology (otherwise returns empty)

**Postconditions:**
- No state changes (read-only operation)

**Example Usage:**
```typescript
// Find all next actions
query_nodes({ type: "Action", properties: { status: "next" } })
// → ["mem_m3n7k1_q9r4t2", "mem_b5c9d2_f7g3h8", "mem_j4k8l1_n6p2r9"]

// Find all projects
query_nodes({ type: "Project" })
// → ["mem_k4j9x2_p8n3q1", "mem_p2q8r4_s6t3u1"]

// Find all next actions requiring phone
query_nodes({
  type: "Action",
  properties: { status: "next", context: "phone" }
})
// → ["mem_m3n7k1_q9r4t2", "mem_v3w7x2_y5z9a4"]
```

---

### Tool 11: query_connections

**Purpose:** Find connections by from/to/type/properties

**Input Schema:**
```typescript
{
  from_node_id?: string,  // Optional: filter by source node
  to_node_id?: string,    // Optional: filter by target node
  type?: string,          // Optional: filter by connection type
  properties?: object     // Optional: filter by properties
}
```

**Parameters:**
- `from_node_id` (string, optional): Filter by source node
- `to_node_id` (string, optional): Filter by target node
- `type` (string, optional): Filter by connection type
- `properties` (object, optional): Filter by properties (AND logic)

**Returns:**
- `connection_ids` (array of strings): Matching connection IDs

**Raises:**
- None (empty result if no matches)

**Example Usage:**
```typescript
// Find all NextAction connections from a project
query_connections({
  from_node_id: "mem_k4j9x2_p8n3q1",
  type: "NextAction"
})
// → ["conn_x7y2z9_k5m8n3", "conn_r8s3t7_u2v6w1"]

// Find all connections to a specific action
query_connections({ to_node_id: "mem_m3n7k1_q9r4t2" })
// → ["conn_x7y2z9_k5m8n3", "conn_q9r2s6_t8u1v5"]
```

---

### Tool 12: get_connected_nodes

**Purpose:** Traverse connections to find connected nodes

**Input Schema:**
```typescript
{
  node_id: string,
  connection_type?: string,    // Optional: filter by connection type
  direction: "out" | "in" | "both"
}
```

**Parameters:**
- `node_id` (string): Starting node
- `connection_type` (string, optional): Filter by connection type
  - If omitted, follows all connection types
- `direction` (string): Traversal direction
  - "out": Follow connections FROM this node (from_node_id = node_id)
  - "in": Follow connections TO this node (to_node_id = node_id)
  - "both": Follow connections in both directions

**Returns:**
- `node_ids` (array of strings): Connected node IDs

**Raises:**
- `NODE_NOT_FOUND`: Starting node doesn't exist

**Example Usage:**
```typescript
// Get all next actions for a project
get_connected_nodes({
  node_id: "mem_k4j9x2_p8n3q1",
  connection_type: "NextAction",
  direction: "out"
})
// → ["mem_m3n7k1_q9r4t2", "mem_b5c9d2_f7g3h8"]

// Get all projects that have this action as next action
get_connected_nodes({
  node_id: "mem_m3n7k1_q9r4t2",
  connection_type: "NextAction",
  direction: "in"
})
// → ["mem_k4j9x2_p8n3q1"]
```

---

### Tool 13: search_content

**Purpose:** Keyword search across node content files

**Input Schema:**
```typescript
{
  query: string,         // Search string
  node_type?: string,    // Optional: limit to specific node type
  limit?: number         // Optional: max results
}
```

**Parameters:**
- `query` (string): Search string
  - Behavior: Substring match, case-insensitive
  - Example: "kitchen" matches "Kitchen Renovation" and "kitchen remodel"
- `node_type` (string, optional): Limit search to specific node type
- `limit` (number, optional): Maximum results to return
  - Default: unlimited

**Returns:**
- `node_ids` (array of strings): Nodes with matching content

**Raises:**
- None (empty result if no matches)

**Notes:**
- Simple substring matching in content
- **Text content only** - binary content (encoding="base64") is not searched
- For nodes with binary content, search will not find matches
- No semantic understanding or embeddings

**Example Usage:**
```typescript
// Find all nodes mentioning "farmhouse"
search_content({ query: "farmhouse" })
// → ["mem_k4j9x2_p8n3q1", "mem_p2q8r4_s6t3u1", "mem_m3n7k1_q9r4t2"]

// Find Project nodes mentioning "farmhouse"
search_content({ query: "farmhouse", node_type: "Project" })
// → ["mem_k4j9x2_p8n3q1", "mem_p2q8r4_s6t3u1"]

// Find first 5 nodes mentioning "contractor"
search_content({ query: "contractor", limit: 5 })
// → ["mem_m3n7k1_q9r4t2", "mem_j4k8l1_n6p2r9", "mem_k4j9x2_p8n3q1"]
```

---

### Tool 14: validate_connection

**Purpose:** Check if connection type is valid between node types

**Input Schema:**
```typescript
{
  connection_type: string,
  from_node_type: string,
  to_node_type: string
}
```

**Parameters:**
- `connection_type` (string): Connection type to validate
- `from_node_type` (string): Source node type
- `to_node_type` (string): Target node type

**Returns:**
```typescript
{
  valid: boolean
}
```

**Raises:**
- `ONTOLOGY_NOT_FOUND`: Ontology hasn't been created

**Example Usage:**
```typescript
validate_connection({
  connection_type: "NextAction",
  from_node_type: "Project",
  to_node_type: "Action"
})
// → { valid: true }

validate_connection({
  connection_type: "NextAction",
  from_node_type: "Action",
  to_node_type: "Project"
})
// → { valid: false }
```

---

### Tool 15: create_ontology

**Purpose:** Initialize ontology with node types and connection types

**Input Schema:**
```typescript
{
  node_types: string[],
  connection_types: Array<{
    name: string,
    from_types: string[],
    to_types: string[],
    required_properties?: string[]
  }>
}
```

**Parameters:**
- `node_types` (array of strings): Valid node type names
  - Example: ["Project", "Action", "Context", "Person"]
- `connection_types` (array of objects): Connection type definitions
  - `name`: Connection type name
  - `from_types`: Which node types can be source
  - `to_types`: Which node types can be target
  - `required_properties` (optional): Property keys that must be present

**Returns:**
- void (success) or error

**Raises:**
- `ONTOLOGY_ALREADY_EXISTS`: Can't create if ontology already exists

**Preconditions:**
- Ontology must not already exist
- Base directory must be writable

**Postconditions:**
- Ontology stored at `_system/ontology.yaml`
- All subsequent node/connection operations validate against this ontology

**Example Usage:**
```typescript
create_ontology({
  node_types: ["Project", "Action", "Context", "Person"],
  connection_types: [
    {
      name: "NextAction",
      from_types: ["Project"],
      to_types: ["Action"]
    },
    {
      name: "RequiresContext",
      from_types: ["Action"],
      to_types: ["Context"]
    },
    {
      name: "WaitingFor",
      from_types: ["Action", "Project"],
      to_types: ["Person"],
      required_properties: ["since", "follow_up_date"]
    }
  ]
})
```

---

### Tool 16: add_node_type

**Purpose:** Add new node type to existing ontology (append-only)

**Input Schema:**
```typescript
{
  type_name: string
}
```

**Parameters:**
- `type_name` (string): New node type to add

**Returns:**
- void (success) or error

**Raises:**
- `ONTOLOGY_NOT_FOUND`: Must create ontology first
- `TYPE_ALREADY_EXISTS`: Type already defined in ontology

**Preconditions:**
- Ontology must exist

**Postconditions:**
- Node type appended to ontology YAML
- Existing types unchanged (immutable append-only)

**Example Usage:**
```typescript
add_node_type({ type_name: "Document" })
```

---

### Tool 17: add_connection_type

**Purpose:** Add new connection type to existing ontology (append-only)

**Input Schema:**
```typescript
{
  type_name: string,
  from_types: string[],
  to_types: string[],
  required_properties?: string[]
}
```

**Parameters:**
- `type_name` (string): Connection type name
- `from_types` (array of strings): Valid source node types
- `to_types` (array of strings): Valid target node types
- `required_properties` (array of strings, optional): Required property keys

**Returns:**
- void (success) or error

**Raises:**
- `ONTOLOGY_NOT_FOUND`: Must create ontology first
- `TYPE_ALREADY_EXISTS`: Type already defined

**Postconditions:**
- Connection type appended to ontology YAML
- Existing types unchanged

**Example Usage:**
```typescript
add_connection_type({
  type_name: "RelatedTo",
  from_types: ["Project", "Action"],
  to_types: ["Project", "Action", "Document"]
})
```

---

### Tool 18: get_ontology

**Purpose:** Retrieve current ontology definition

**Input Schema:** (none)

**Returns:**
```typescript
{
  node_types: string[],
  connection_types: Array<{
    name: string,
    from_types: string[],
    to_types: string[],
    required_properties?: string[]
  }>
}
```

**Raises:**
- `ONTOLOGY_NOT_FOUND`: Ontology hasn't been created yet

**Preconditions:**
- Ontology must exist

**Postconditions:**
- No state changes (read-only operation)

**Example Usage:**
```typescript
get_ontology()
// → {
//   node_types: ["Project", "Action", "Context", "Person"],
//   connection_types: [
//     {
//       name: "NextAction",
//       from_types: ["Project"],
//       to_types: ["Action"]
//     },
//     ...
//   ]
// }
```

---

## Acceptance Criteria

### Happy Path (5 criteria)

**AC1: Node Lifecycle Works**
- ✓ Can create node with type, content, format, and properties
- ✓ Created node returns unique ID
- ✓ get_node(id) returns correct metadata with all fields
- ✓ get_node_content(id) returns original content unchanged
- ✓ Node persists across server restart (load registry, node still exists)

**AC2: Connection Lifecycle Works**
- ✓ Can create connection between two existing nodes
- ✓ Created connection returns unique ID
- ✓ get_connection(id) returns from/to/type/properties correctly
- ✓ Connection persists across server restart

**AC3: Graph Queries Work**
- ✓ query_nodes by type returns all matching nodes
- ✓ query_nodes by properties returns nodes matching ALL specified properties
- ✓ query_connections by from/to/type returns matching connections
- ✓ get_connected_nodes follows connections in specified direction

**AC4: Ontology Validation Works**
- ✓ create_ontology defines valid types and topology rules
- ✓ Creating node with invalid type fails with INVALID_NODE_TYPE
- ✓ Creating connection with invalid topology fails with INVALID_TOPOLOGY
- ✓ validate_connection returns correct boolean based on ontology

**AC5: Cascade Delete Works**
- ✓ Deleting node with connections deletes all connected connections
- ✓ Connections to/from deleted node are removed from registry
- ✓ query_connections no longer returns deleted connections
- ✓ Target nodes of deleted connections remain (only connections removed)

---

### Error Handling (6 criteria)

**AC6: Invalid Node Operations Fail Gracefully**
- ✓ get_node with non-existent ID throws NODE_NOT_FOUND
- ✓ update_node with non-existent ID throws NODE_NOT_FOUND
- ✓ delete_node with non-existent ID throws NODE_NOT_FOUND
- ✓ Error messages are descriptive

**AC7: Invalid Connection Operations Fail Gracefully**
- ✓ create_connection with non-existent node throws NODE_NOT_FOUND
- ✓ create_connection with invalid type throws INVALID_CONNECTION_TYPE
- ✓ get_connection with non-existent ID throws CONNECTION_NOT_FOUND
- ✓ Error messages specify which node or type is invalid

**AC8: Ontology Violations Caught**
- ✓ Creating node with type not in ontology fails with INVALID_NODE_TYPE
- ✓ Creating connection between incompatible node types fails with INVALID_TOPOLOGY
- ✓ Error message includes what types are allowed (e.g., "Valid targets: [Action]")

**AC9: Required Properties Enforced**
- ✓ Connection type with required_properties rejects creation without them
- ✓ Error message specifies which properties are missing
- ✓ Connection with all required properties succeeds

**AC10: Ontology Protection**
- ✓ create_ontology when ontology exists throws ONTOLOGY_ALREADY_EXISTS
- ✓ add_node_type with existing type throws TYPE_ALREADY_EXISTS
- ✓ Operations before ontology created throw ONTOLOGY_NOT_FOUND

**AC11: Registry Consistency**
- ✓ Failed operations don't corrupt registry (remains valid JSON)
- ✓ Partial failures rollback (node creation fails → no registry entry)
- ✓ Registry remains loadable after any operation sequence

---

### Edge Cases (7 criteria)

**AC12: Empty/Minimal Data**
- ✓ Can create node with empty content string
- ✓ Can create node without properties (empty object `{}`)
- ✓ Can create connection without optional content
- ✓ query_nodes with no filters returns all nodes

**AC13: Nodes Without Connections**
- ✓ Standalone nodes (no connections) are valid
- ✓ Deleting standalone node works correctly
- ✓ get_connected_nodes on isolated node returns empty array

**AC14: Multiple Connections**
- ✓ Same node can have multiple outgoing connections of same type
- ✓ Same node pair can have connections of different types
- ✓ Deleting one connection doesn't affect others

**AC15: Property Filtering**
- ✓ query_nodes matches ALL specified properties (AND logic)
- ✓ Nodes with extra properties still match if specified ones match
- ✓ Empty properties filter `{}` matches all nodes of specified type

**AC16: Content Search**
- ✓ search_content finds substring in node content (case-insensitive)
- ✓ search_content with node_type filters to that type only
- ✓ search_content with limit returns max N results
- ✓ search_content with no matches returns empty array

**AC17: Ontology Append-Only**
- ✓ add_node_type adds new type without affecting existing types
- ✓ add_connection_type adds new connection without affecting existing
- ✓ get_ontology returns updated ontology with appended types

**AC18: Direction Handling**
- ✓ get_connected_nodes with direction="out" follows from→to
- ✓ get_connected_nodes with direction="in" follows to→from
- ✓ get_connected_nodes with direction="both" returns nodes from both directions

---

### Atomicity/Consistency (2 criteria)

**AC19: Operations Are Atomic**
- ✓ Node creation: if content file creation fails, no registry entry created
- ✓ Node deletion: registry and file deleted together, no orphaned files
- ✓ Connection creation: if validation fails, no registry entry
- ✓ No partial state after operation failure

**AC20: Registry Persistence**
- ✓ Changes to registry saved immediately after each operation
- ✓ Server restart loads existing registry correctly
- ✓ Registry reflects current state after any operation
- ✓ Concurrent operations don't corrupt registry (sequential processing assumed)

---

## Scenarios

### Scenario 1: Create GTD Project with Next Action

**Given:**
- Server started with empty base directory
- No ontology exists

**When:**
1. Call `create_ontology({ node_types: ["Project", "Action"], connection_types: [{ name: "NextAction", from_types: ["Project"], to_types: ["Action"] }] })`
2. Call `create_node({ type: "Project", content: "# Kitchen Renovation\n\nBudget: $50k", format: "markdown", properties: { status: "active" } })`
   - Returns: `{ node_id: "mem_k4j9x2_p8n3q1" }`
3. Call `create_node({ type: "Action", content: "# Call contractor\n\nGet 3 quotes", format: "markdown", properties: { status: "next" } })`
   - Returns: `{ node_id: "mem_m3n7k1_q9r4t2" }`
4. Call `create_connection({ type: "NextAction", from_node_id: "mem_k4j9x2_p8n3q1", to_node_id: "mem_m3n7k1_q9r4t2", properties: { priority: "high" } })`
   - Returns: `{ connection_id: "conn_x7y2z9_k5m8n3" }`

**Then:**
- Registry contains 2 nodes and 1 connection
- Content files exist at `_content/nodes/mem_k4j9x2_p8n3q1.md` and `_content/nodes/mem_m3n7k1_q9r4t2.md`
- `get_node("mem_k4j9x2_p8n3q1")` returns metadata with type="Project", properties={ status: "active" }
- `get_connected_nodes({ node_id: "mem_k4j9x2_p8n3q1", connection_type: "NextAction", direction: "out" })` returns `["mem_m3n7k1_q9r4t2"]`
- Restarting server and calling `get_node("mem_k4j9x2_p8n3q1")` still works (data persists)

---

### Scenario 2: Invalid Connection Topology Rejected

**Given:**
- Ontology exists with node types: ["Project", "Action", "Person"]
- Ontology has connection type "NextAction" from ["Project"] to ["Action"] only
- Node "mem_k4j9x2_p8n3q1" exists with type="Project"
- Node "mem_c6d2e8_g4h9j1" exists with type="Person"

**When:**
- Call `create_connection({ type: "NextAction", from_node_id: "mem_k4j9x2_p8n3q1", to_node_id: "mem_c6d2e8_g4h9j1" })`

**Then:**
- Operation fails with error code `INVALID_TOPOLOGY`
- Error message: "Cannot connect Project to Person with NextAction. Valid targets: [Action]"
- No connection created in registry
- `query_connections({ from_node_id: "mem_k4j9x2_p8n3q1" })` returns empty array
- Registry remains unchanged (no partial state)

---

### Scenario 3: Cascade Delete Removes Connections

**Given:**
- Node "mem_k4j9x2_p8n3q1" (type="Project") exists
- Nodes "mem_m3n7k1_q9r4t2", "mem_b5c9d2_f7g3h8", "mem_j4k8l1_n6p2r9" (type="Action") exist
- Connections exist:
  - "conn_x7y2z9_k5m8n3": mem_k4j9x2_p8n3q1 → mem_m3n7k1_q9r4t2 (NextAction)
  - "conn_r8s3t7_u2v6w1": mem_k4j9x2_p8n3q1 → mem_b5c9d2_f7g3h8 (NextAction)
  - "conn_h3j7k1_l9m4n8": mem_b5c9d2_f7g3h8 → mem_j4k8l1_n6p2r9 (DependsOn)

**When:**
- Call `delete_node({ node_id: "mem_k4j9x2_p8n3q1" })`

**Then:**
- Node "mem_k4j9x2_p8n3q1" removed from registry
- Content file `_content/nodes/mem_k4j9x2_p8n3q1.md` deleted
- Connections "conn_x7y2z9_k5m8n3" and "conn_r8s3t7_u2v6w1" deleted (connected to deleted node)
- Connection "conn_h3j7k1_l9m4n8" still exists (not connected to deleted node)
- Nodes "mem_m3n7k1_q9r4t2", "mem_b5c9d2_f7g3h8", "mem_j4k8l1_n6p2r9" still exist (targets not deleted)
- `get_node("mem_k4j9x2_p8n3q1")` throws `NODE_NOT_FOUND`
- `get_connection("conn_x7y2z9_k5m8n3")` throws `CONNECTION_NOT_FOUND`
- `get_connection("conn_h3j7k1_l9m4n8")` returns connection metadata (still exists)

---

### Scenario 4: Query Nodes by Properties

**Given:**
- Ontology exists with node type "Action"
- Nodes exist:
  - "mem_m3n7k1_q9r4t2": { type: "Action", properties: { status: "next", context: "phone" } }
  - "mem_b5c9d2_f7g3h8": { type: "Action", properties: { status: "next", context: "computer" } }
  - "mem_j4k8l1_n6p2r9": { type: "Action", properties: { status: "waiting", context: "phone" } }
  - "mem_v3w7x2_y5z9a4": { type: "Action", properties: { status: "next", context: "phone", priority: "high" } }

**When:**
- Call `query_nodes({ type: "Action", properties: { status: "next", context: "phone" } })`

**Then:**
- Returns: `["mem_m3n7k1_q9r4t2", "mem_v3w7x2_y5z9a4"]`
- Does NOT return "mem_b5c9d2_f7g3h8" (context doesn't match)
- Does NOT return "mem_j4k8l1_n6p2r9" (status doesn't match)
- DOES return "mem_v3w7x2_y5z9a4" even though it has extra property "priority" (extra properties OK)
- Order of results: unspecified (can be any order)

---

### Scenario 5: Required Connection Properties Enforced

**Given:**
- Ontology exists with connection type:
  ```typescript
  {
    name: "WaitingFor",
    from_types: ["Action"],
    to_types: ["Person"],
    required_properties: ["since", "follow_up_date"]
  }
  ```
- Node "mem_m3n7k1_q9r4t2" (type="Action") exists
- Node "mem_c6d2e8_g4h9j1" (type="Person") exists

**When:**
- Call `create_connection({ type: "WaitingFor", from_node_id: "mem_m3n7k1_q9r4t2", to_node_id: "mem_c6d2e8_g4h9j1", properties: { since: "2025-10-15" } })`
  - (Missing required property "follow_up_date")

**Then:**
- Operation fails with error code `REQUIRED_PROPERTY_MISSING`
- Error message: "Connection type WaitingFor requires properties: [since, follow_up_date]. Missing: [follow_up_date]"
- No connection created in registry
- `query_connections({ type: "WaitingFor" })` returns empty array

---

### Scenario 6: Search Content Finds Matching Nodes

**Given:**
- Nodes exist:
  - "mem_k4j9x2_p8n3q1" (type="Project"): content="# Kitchen Renovation\n\nModern farmhouse style"
  - "mem_p2q8r4_s6t3u1" (type="Project"): content="# Bathroom Remodel\n\nFarmhouse sink and fixtures"
  - "mem_m3n7k1_q9r4t2" (type="Action"): content="# Research farmhouse sinks\n\nFind suppliers"
  - "mem_b5c9d2_f7g3h8" (type="Action"): content="# Call plumber\n\nSchedule bathroom work"

**When:**
- Call `search_content({ query: "farmhouse", limit: 10 })`

**Then:**
- Returns: `["mem_k4j9x2_p8n3q1", "mem_p2q8r4_s6t3u1", "mem_m3n7k1_q9r4t2"]` (order unspecified)
- All nodes containing "farmhouse" (case-insensitive) returned
- Does NOT return "mem_b5c9d2_f7g3h8" (no match)

**When:**
- Call `search_content({ query: "farmhouse", node_type: "Project", limit: 10 })`

**Then:**
- Returns: `["mem_k4j9x2_p8n3q1", "mem_p2q8r4_s6t3u1"]`
- Only Project nodes returned (mem_m3n7k1_q9r4t2 filtered out by node_type)

**When:**
- Call `search_content({ query: "farmhouse", limit: 2 })`

**Then:**
- Returns: 2 node IDs (which 2 is unspecified)
- Limit honored (max 2 results even though 3 match)

---

## Data Structures

### Node

**Type:** TypeScript Type / JSON Object

**Structure:**
```typescript
{
  id: string,              // Unique identifier (opaque)
  type: string,            // Node type from ontology
  created: string,         // ISO 8601 timestamp
  modified: string,        // ISO 8601 timestamp
  properties: object,      // Key-value properties (minimal)
  content: {
    path: string,          // Relative path to content file
    format: string         // Content format (markdown, json, etc.)
  }
}
```

**Invariants:**
- `id` is unique across all nodes
- `type` must exist in ontology
- `created` <= `modified`
- `properties` is valid JSON object
- `content.path` points to existing file

**Example:**
```typescript
{
  id: "mem_k4j9x2_p8n3q1",
  type: "Project",
  created: "2025-10-31T10:00:00Z",
  modified: "2025-10-31T15:30:00Z",
  properties: { status: "active" },
  content: {
    path: "_content/nodes/mem_k4j9x2_p8n3q1.md",
    format: "markdown"
  }
}
```

---

### Connection

**Type:** TypeScript Type / JSON Object

**Structure:**
```typescript
{
  id: string,              // Unique identifier (opaque)
  type: string,            // Connection type from ontology
  from: string,            // Source node ID
  to: string,              // Target node ID
  created: string,         // ISO 8601 timestamp
  modified: string,        // ISO 8601 timestamp
  properties: object,      // Key-value properties
  content?: {              // Optional content file
    path: string,
    format: string
  }
}
```

**Invariants:**
- `id` is unique across all connections
- `type` must exist in ontology
- `from` and `to` must reference existing nodes
- Connection topology must satisfy ontology rules
- `created` <= `modified`
- If ontology specifies required_properties, all must be present

**Example:**
```typescript
{
  id: "conn_x7y2z9_k5m8n3",
  type: "NextAction",
  from: "mem_k4j9x2_p8n3q1",
  to: "mem_m3n7k1_q9r4t2",
  created: "2025-10-31T10:15:00Z",
  modified: "2025-10-31T10:15:00Z",
  properties: { priority: "high", added: "2025-10-31" }
}
```

---

### Registry

**Type:** JSON Object (persisted to `_system/registry.json`)

**Structure:**
```typescript
{
  nodes: {
    [id: string]: Node
  },
  connections: {
    [id: string]: Connection
  }
}
```

**Invariants:**
- Valid JSON
- All connection `from` and `to` IDs reference existing nodes in `nodes`
- No dangling references

**Location:** `_system/registry.json`

**Example:**
```json
{
  "nodes": {
    "mem_k4j9x2_p8n3q1": {
      "id": "mem_k4j9x2_p8n3q1",
      "type": "Project",
      "created": "2025-10-31T10:00:00Z",
      "modified": "2025-10-31T15:30:00Z",
      "properties": { "status": "active" },
      "content": {
        "path": "_content/nodes/mem_k4j9x2_p8n3q1.md",
        "format": "markdown"
      }
    }
  },
  "connections": {
    "conn_x7y2z9_k5m8n3": {
      "id": "conn_x7y2z9_k5m8n3",
      "type": "NextAction",
      "from": "mem_k4j9x2_p8n3q1",
      "to": "mem_m3n7k1_q9r4t2",
      "created": "2025-10-31T10:15:00Z",
      "modified": "2025-10-31T10:15:00Z",
      "properties": { "priority": "high" }
    }
  }
}
```

---

### Ontology

**Type:** YAML (persisted to `_system/ontology.yaml`)

**Structure:**
```yaml
node_types:
  - Project
  - Action
  - Context
  - Person

connection_types:
  - name: NextAction
    from_types:
      - Project
    to_types:
      - Action

  - name: RequiresContext
    from_types:
      - Action
    to_types:
      - Context

  - name: WaitingFor
    from_types:
      - Action
      - Project
    to_types:
      - Person
    required_properties:
      - since
      - follow_up_date
```

**Invariants:**
- Valid YAML
- `node_types` is array of strings
- `connection_types` is array of objects with required fields (name, from_types, to_types)
- Append-only (types can be added but not modified or removed)

**Location:** `_system/ontology.yaml`

---

## Dependencies

### External Dependencies

**Required:**
- **@modelcontextprotocol/sdk** (latest) - MCP SDK for TypeScript server implementation
- **Node.js v18+** - Runtime environment
- **TypeScript** - Development and compilation
- **js-yaml** - For parsing/writing ontology YAML files
- **file-storage-backend** (Feature 1) ✅ Complete - Provides 6 file operations

**Development/Testing:**
- **Vitest** - Testing framework

### Internal Dependencies

**Depends on:**
- ✅ **Feature 1: File-Storage-Backend Integration** - Complete and approved
  - Provides: view, create, str_replace, insert, delete, rename operations
  - Used for: Registry persistence, ontology storage, node/connection content files

**Enables:**
- **Feature 3: GTD Ontology** - Will define GTD-specific ontology and use graph operations
- **Feature 4: Conversational Layer** - Will interact with GTD layer built on this

### Platform Requirements

- **Claude Code MCP Integration:** Standard MCP protocol, stdio transport
- **Filesystem Access:** Read/write permissions to configured base directory
- **Operating System:** Cross-platform (macOS, Linux, Windows via Node.js)

### Assumptions

1. **Single user, single instance:** No concurrent access from multiple clients, sequential operations
2. **Ontology planned upfront:** GTD layer defines complete ontology before use
3. **Registry size manageable:** <10,000 nodes for MVP, fits in memory
4. **Content files primarily UTF-8 text:** Markdown for most nodes, binary support exists but uncommon
5. **File-storage-backend reliability:** Atomic operations work as specified, errors propagate correctly

---

## Constraints and Limitations

### Technical Constraints

1. **File-based storage:**
   - No database required
   - Registry must fit in memory (acceptable for MVP: ~5-10 MB for 10k nodes + 20k connections)
   - Content files loaded on demand

2. **Single process:**
   - No multi-process coordination
   - Single MCP server instance
   - Sequential operations (no concurrent writes)

3. **Node.js limitations:**
   - Practical file size limit ~100MB per content file
   - JSON registry size limited by V8 heap

4. **Ontology immutability:**
   - Append-only (can add types, cannot modify/delete)
   - Requires careful planning

### Performance Requirements

From SCOPE.md:
- Graph queries return <2 seconds for typical usage (50-100 projects, 200-500 actions)
- Registry queries are fast (in-memory)
- Content files only loaded when needed

### Timeline Constraint

- 2 days total (1 day implementation, 1 day tests/debug)
- Can defer if needed: complex ontology validation, transaction safety, advanced error handling

### Known Limitations

**Not included in MVP:**
- No versioning - No history of node/connection changes
- No undo - Deleted nodes cannot be recovered
- No caching - Direct registry/file operations each time
- No indexing - Linear scan for property queries (acceptable for ~10k nodes)
- No query optimization - Full registry load each query
- No batch operations - One operation per MCP tool call
- No file watching - Changes only via explicit operations
- No backup/export - Manual file copy only

**Deferred (if timeline tight):**
- Complex ontology validation (circular connection detection)
- Transaction rollback for multi-step operations
- Advanced error recovery
- Performance optimization

---

## Implementation Notes

### Suggested Approach

**MCP Server Setup:**
1. Use @modelcontextprotocol/sdk to create MCP server
2. Define 18 tools with schemas matching Interface Contract
3. Implement tool handlers that delegate to MemoryGraph class
4. Handle MCP error responses with descriptive messages

**Core Classes:**

**Registry Class:**
- Load/save to `_system/registry.json` via file-storage-backend
- Add/get/delete nodes and connections
- Query by type/properties
- Maintain invariants (no dangling references)

**Ontology Class:**
- Load/save to `_system/ontology.yaml` via file-storage-backend
- Parse YAML to internal structure
- Validate node types, connection topology, required properties
- Support append-only additions

**MemoryGraph Class:**
- Orchestrate registry, ontology, and file-storage
- Implement all 18 MCP tool operations
- Enforce atomicity (operations succeed or fail cleanly)
- Handle cascade delete (deleting node removes connections)

**ID Generation:**
```typescript
function generateId(prefix: string = "mem"): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 9)
  return `${prefix}_${timestamp}_${random}`
}
```

**Atomicity Pattern:**
For operations that modify both registry and files:
1. Perform file operation first (create/delete content)
2. Update registry in memory
3. Save registry to disk
4. If any step fails, rollback (delete created files, restore old registry)

### Error Handling Strategy

**Error Categories:**
1. **Validation errors** (INVALID_NODE_TYPE, INVALID_TOPOLOGY, REQUIRED_PROPERTY_MISSING)
   - Validate before any state changes
   - Return descriptive error immediately
2. **Not found errors** (NODE_NOT_FOUND, CONNECTION_NOT_FOUND)
   - Check registry before operation
3. **System errors** (FILE_CREATION_FAILED, CONTENT_READ_FAILED)
   - Propagate from file-storage-backend
   - Ensure no partial state

**MCP Error Format:**
```typescript
{
  code: 'NODE_NOT_FOUND' | 'INVALID_TOPOLOGY' | ...,
  message: 'Human-readable description',
  details?: object  // Additional context if helpful
}
```

### Testing Strategy

**Unit Tests (Vitest):**
- Registry: Add/get/delete, query, save/load
- Ontology: Load YAML, validate types, check topology
- MemoryGraph: All CRUD operations, queries, cascade delete

**Integration Tests:**
- Start actual MCP server
- Send tool requests via MCP protocol
- Verify filesystem state
- Test server restart persistence

**Test Coverage:**
- All 20 acceptance criteria
- Each scenario implemented as test
- Mock file-storage-backend for unit tests
- Use real file-storage-backend for integration tests

---

## Open Questions

None - all clarified during spec-writing-helper conversation.

---

## References

- **VISION.md** - Section "Technical Approach" explains memory architecture foundation
- **SCOPE.md** - Section "Technical Requirements" → "Memory Architecture (Two-Layer)" shows graph memory layer
- **ROADMAP.md** - Phase 1, Feature 2: Graph Memory Core
- **Feature 1 Spec** - specs/done/file-storage-backend.md - File operations interface
- **memory_system_core.md** (inspiration/) - Original design document for graph memory architecture
- **CLARIFICATION-graph-memory-vs-preferences.md** (inspiration/) - Clarifies graph memory scope vs Anthropic Memory Server

---

## Document Control

**Version 1.0 (2025-10-31)**
- Initial specification created via spec-writing-helper collaborative conversation
- Key decisions:
  - 18 MCP tools covering full graph lifecycle
  - Ontology-driven validation with append-only extension
  - Cascade delete for node removal
  - Keyword search only (no semantic/embedding search)
  - Properties in registry, content in files
  - Atomic operations (succeed or fail cleanly)
  - 2-day implementation target with deferral options
- Derived from: ROADMAP.md Feature 2, memory_system_core.md, spec-writing-helper conversation

**Version 1.1 (2025-10-31) - Review Feedback Addressed**
- **Status changed** from "Proposed" to "Review"
- **Server naming**: Fixed consistency - using "graph-memory-core" everywhere (was "graph-memory" in config example)
- **Content encoding**: Added separate `encoding` parameter ("utf-8" | "base64") to distinguish from opaque `format` metadata
- **Format semantics**: Clarified that `format` is opaque client metadata; system only uses it for file extensions
- **Format mutability**: Explicitly stated format can change on update (just metadata)
- **ID examples**: Changed all examples from sequential/typed (mem_proj_001) to opaque random-looking IDs (mem_k4j9x2_p8n3q1)
- **Property constraints**: Added section defining allowed types (string, number, boolean only; no arrays/objects)
- **Property matching**: Specified exact equality, case-sensitive strings, AND logic for multiple properties
- **Property removal**: Explicitly stated not supported in MVP; documented workarounds
- **Connection content path**: Specified `_content/connections/{id}.md` as implementation detail
- **Binary search**: Clarified search_content is text-only; binary content not searched
- **Error codes**: Added comprehensive error code reference table
- Addresses review: reviews/specs/2025-10-31T18-12-13-graph-memory-core-NEEDS-CHANGES.md (all 8 approval criteria met)
