# MCP Tools Guide

Detailed reference for graph-memory-core MCP server tools. Consult when uncertain about tool parameters, return values, or usage patterns.

## Tool Invocation Names

In Claude Code with MCP, tools use fully-qualified names:
- `mcp__gtd-graph-memory__create_node`
- `mcp__gtd-graph-memory__get_node`
- `mcp__gtd-graph-memory__update_node`
- etc.

The prefix `mcp__gtd-graph-memory__` is required for all tool calls.

## Node Operations

### create_node

Create a new node in the graph.

**Parameters:**
```typescript
{
  type: string,              // "Task" | "State" | "Context" | "UNSPECIFIED"
  content: string,           // UTF-8 text description
  encoding: "utf-8",         // Always "utf-8"
  format: string,            // "markdown" typical
  properties?: {             // Type-specific properties
    // For Task:
    isComplete?: boolean,    // Required (default false)
    responsibleParty?: string // Optional, "me" or external party

    // For State:
    isTrue?: boolean,        // Required
    logic?: "MANUAL",        // Only MANUAL in Phase 1

    // For Context:
    isAvailable?: boolean    // Required
  }
}
```

**Returns:**
```typescript
{ node_id: string }
```

**Usage notes:**
- Always provide explicit `isComplete`, `isTrue`, or `isAvailable` defaults
- `content` is stored separately from properties
- Use markdown format for rich text descriptions
- Property values must be string, number, or boolean (no nested objects)

**Example:**
```javascript
create_node({
  "type": "Task",
  "content": "Call the dentist to schedule cleaning",
  "encoding": "utf-8",
  "format": "markdown",
  "properties": {
    "isComplete": false
  }
})
// Returns: { "node_id": "mem_abc123_xyz789" }
```

---

### get_node

Retrieve node metadata and properties (not content).

**Parameters:**
```typescript
{ node_id: string }
```

**Returns:**
```typescript
{
  id: string,
  type: string,
  created: string,           // ISO 8601 timestamp
  modified: string,          // ISO 8601 timestamp
  properties: object,        // Type-specific properties
  content_format: string     // e.g., "markdown"
}
```

**Usage notes:**
- Does NOT return content text (use `get_node_content` for that)
- Use this to check properties before updates
- Timestamps are in ISO 8601 format

**Example:**
```javascript
get_node({ "node_id": "mem_abc123_xyz789" })
// Returns:
{
  "id": "mem_abc123_xyz789",
  "type": "Task",
  "created": "2025-11-05T10:00:00Z",
  "modified": "2025-11-05T10:00:00Z",
  "properties": {
    "isComplete": false
  },
  "content_format": "markdown"
}
```

---

### get_node_content

Retrieve the content text of a node.

**Parameters:**
```typescript
{ node_id: string }
```

**Returns:**
```typescript
{
  content: string,           // UTF-8 text
  format: string,            // e.g., "markdown"
  encoding: string           // e.g., "utf-8"
}
```

**Usage notes:**
- Separate call from `get_node` for efficiency
- Use when you need the full description text
- Essential before updating content (to preserve existing)

**Example:**
```javascript
get_node_content({ "node_id": "mem_abc123_xyz789" })
// Returns:
{
  "content": "Call the dentist to schedule cleaning",
  "format": "markdown",
  "encoding": "utf-8"
}
```

---

### update_node

Update node properties or content.

**Parameters:**
```typescript
{
  node_id: string,
  properties?: object,       // Merge with existing (can't remove)
  content?: string,          // Replace content
  encoding?: "utf-8",
  format?: string
}
```

**Returns:** `void` (no return value)

**Usage notes:**
- Properties are merged (can't delete properties)
- Content is replaced entirely (fetch existing first to append)
- Update only what needs changing
- No return value means success (error otherwise)

**Example:**
```javascript
update_node({
  "node_id": "mem_abc123_xyz789",
  "properties": {
    "isComplete": true
  }
})
```

**Append pattern:**
```javascript
// 1. Get existing content
get_node_content({ "node_id": "mem_abc123_xyz789" })
// Returns: "Call the dentist"

// 2. Append to it
update_node({
  "node_id": "mem_abc123_xyz789",
  "content": "Call the dentist\n\nNote: Prefer morning appointments."
})
```

---

### delete_node

Delete a node and cascade delete its connections.

**Parameters:**
```typescript
{ node_id: string }
```

**Returns:** `void`

**Postcondition:** All connections involving this node are automatically deleted (cascade)

**Usage notes:**
- Irreversible operation
- Auto-deletes connections, but NOT dependent nodes
- Check for dependents before deleting (use `get_connected_nodes`)
- Always confirm with user first

**Example:**
```javascript
// Check dependencies first
get_connected_nodes({
  "node_id": "mem_abc123_xyz789",
  "direction": "in"
})
// If dependents exist, warn user

// After confirmation:
delete_node({ "node_id": "mem_abc123_xyz789" })
```

---

### query_nodes

Find nodes by type and properties.

**Parameters:**
```typescript
{
  type?: string,             // Filter by node type
  properties?: {             // Filter by properties (AND semantics)
    [key: string]: any       // Property name and expected value
  }
}
```

**Returns:**
```typescript
{ node_ids: string[] }
```

**Usage notes:**
- All property filters use AND semantics (must match all)
- Case-sensitive, exact matching for property values
- Returns empty array if no matches
- Does NOT return node data (call `get_node` for each ID)

**Example:**
```javascript
query_nodes({
  "type": "Task",
  "properties": {
    "isComplete": false
  }
})
// Returns: { "node_ids": ["mem_abc123_xyz789", "mem_def456_uvw012"] }
```

---

### search_content

Search node content for substring matches (case-insensitive).

**Parameters:**
```typescript
{
  query: string,             // Search term
  node_type?: string,        // Limit to specific type
  limit?: number             // Max results
}
```

**Returns:**
```typescript
{ node_ids: string[] }
```

**Usage notes:**
- Case-insensitive substring matching
- Use for text-based searches ("dentist", "report", etc.)
- Combine with semantic similarity for duplicate detection
- Limit results to avoid performance issues

**Example:**
```javascript
search_content({
  "query": "dentist",
  "node_type": "Task",
  "limit": 10
})
// Returns: { "node_ids": ["mem_abc123_xyz789"] }
```

---

### ensure_singleton_node

Get or create a singleton node (currently only UNSPECIFIED).

**Parameters:**
```typescript
{
  type: "UNSPECIFIED",
  content?: string,
  encoding?: "utf-8",
  format?: string,
  properties?: object,
  on_multiple?: "oldest" | "newest"
}
```

**Returns:**
```typescript
{
  node_id: string,
  created: boolean           // true if created, false if existed
}
```

**Idempotency:** Returns existing UNSPECIFIED singleton on subsequent calls

**Usage notes:**
- Only one UNSPECIFIED node exists system-wide
- Use this instead of creating UNSPECIFIED manually
- First call creates, subsequent calls return existing

**Example:**
```javascript
ensure_singleton_node({
  "type": "UNSPECIFIED",
  "content": "Placeholder for missing next step.",
  "encoding": "utf-8",
  "format": "markdown"
})
// First call returns: { "node_id": "mem_unspec_001", "created": true }
// Subsequent calls: { "node_id": "mem_unspec_001", "created": false }
```

---

## Connection Operations

### create_connection

Create a directed connection between nodes.

**Parameters:**
```typescript
{
  type: "DependsOn",
  from_node_id: string,      // Source (dependent)
  to_node_id: string,        // Target (dependency)
  properties?: object        // Optional metadata
}
```

**Returns:**
```typescript
{ connection_id: string }
```

**Usage notes:**
- Direction matters: "from depends on to"
- Both nodes must exist before creating connection
- Topology validated by MCP server (allowed: Task→Task, Task→State, Task→Context, etc.)
- Cannot create invalid connections (e.g., Context→Task)

**Example:**
```javascript
create_connection({
  "type": "DependsOn",
  "from_node_id": "mem_task_001",  // "Write report"
  "to_node_id": "mem_task_002"     // "Gather data"
})
// "Write report" depends on "Gather data"
// Returns: { "connection_id": "conn_abc123" }
```

---

### get_connection

Retrieve connection metadata.

**Parameters:**
```typescript
{ connection_id: string }
```

**Returns:**
```typescript
{
  id: string,
  type: string,
  from_node_id: string,
  to_node_id: string,
  properties?: object,
  created: string,           // ISO 8601
  modified: string           // ISO 8601
}
```

**Usage notes:**
- Use when you need connection details
- Rare in typical workflows (traversal is more common)

---

### update_connection

Update connection properties.

**Parameters:**
```typescript
{
  connection_id: string,
  properties?: object,       // Merge with existing
  content?: string,          // Optional connection content
  format?: string
}
```

**Returns:** `void`

**Usage notes:**
- Rarely used in GTD workflows
- Properties are merged (can't delete)

---

### delete_connection

Remove a connection without affecting nodes.

**Parameters:**
```typescript
{ connection_id: string }
```

**Returns:** `void`

**Usage notes:**
- Removes dependency relationship
- Nodes remain intact
- Use when removing a dependency that's no longer relevant

**Example:**
```javascript
delete_connection({ "connection_id": "conn_abc123" })
```

---

### query_connections

Find connections by endpoints, type, and properties.

**Parameters:**
```typescript
{
  from_node_id?: string,     // Find connections from this node
  to_node_id?: string,       // Find connections to this node
  type?: "DependsOn",
  properties?: object
}
```

**Returns:**
```typescript
{ connection_ids: string[] }
```

**Usage notes:**
- Use to find projects (connections from a task)
- Use to find dependents (connections to a task)
- Combine with `get_connected_nodes` for traversal

**Example:**
```javascript
// Find all connections FROM a task (its dependencies)
query_connections({
  "from_node_id": "mem_task_001",
  "type": "DependsOn"
})
// Returns: { "connection_ids": ["conn_abc123", "conn_def456"] }

// Find all connections TO a task (its dependents)
query_connections({
  "to_node_id": "mem_task_002",
  "type": "DependsOn"
})
// Returns: { "connection_ids": ["conn_abc123"] }
```

---

### get_connected_nodes

Traverse connections to retrieve adjacent node IDs.

**Parameters:**
```typescript
{
  node_id: string,
  connection_type?: "DependsOn",
  direction: "out" | "in" | "both"  // Outgoing, incoming, or both
}
```

**Returns:**
```typescript
{ node_ids: string[] }
```

**Usage notes:**
- Most common traversal tool
- "out" = dependencies (what this node depends on)
- "in" = dependents (what depends on this node)
- "both" = all connected nodes

**Example:**
```javascript
// Get dependencies (what task depends on)
get_connected_nodes({
  "node_id": "mem_task_001",
  "direction": "out",
  "connection_type": "DependsOn"
})
// Returns: { "node_ids": ["mem_task_002", "mem_context_001"] }

// Get dependents (what depends on this task)
get_connected_nodes({
  "node_id": "mem_task_002",
  "direction": "in",
  "connection_type": "DependsOn"
})
// Returns: { "node_ids": ["mem_task_001", "mem_task_003"] }
```

---

## Common Patterns

### Pattern 1: Create Task with Context

```javascript
// 1. Ensure context exists
create_node({
  "type": "Context",
  "content": "@office",
  "encoding": "utf-8",
  "format": "markdown",
  "properties": { "isAvailable": true }
})
// Returns: { "node_id": "mem_ctx_001" }

// 2. Create task
create_node({
  "type": "Task",
  "content": "Print quarterly packets",
  "encoding": "utf-8",
  "format": "markdown",
  "properties": { "isComplete": false }
})
// Returns: { "node_id": "mem_task_001" }

// 3. Connect task to context
create_connection({
  "type": "DependsOn",
  "from_node_id": "mem_task_001",
  "to_node_id": "mem_ctx_001"
})
```

### Pattern 2: Mark Task Complete and Check Dependents

```javascript
// 1. Mark complete
update_node({
  "node_id": "mem_task_002",
  "properties": { "isComplete": true }
})

// 2. Check what depends on this task
get_connected_nodes({
  "node_id": "mem_task_002",
  "direction": "in"
})
// Returns: { "node_ids": ["mem_task_001"] }

// 3. Check if dependent is now actionable
get_node({ "node_id": "mem_task_001" })
get_connected_nodes({
  "node_id": "mem_task_001",
  "direction": "out"
})
// Evaluate if all dependencies satisfied
```

### Pattern 3: Find Projects

```javascript
// 1. Get all incomplete tasks
query_nodes({
  "type": "Task",
  "properties": { "isComplete": false }
})
// Returns: { "node_ids": [...] }

// 2. For each task, check if it has outgoing dependencies
for (const taskId of taskIds) {
  query_connections({
    "from_node_id": taskId,
    "type": "DependsOn"
  })
  // If returns connections, task is a project
}
```

### Pattern 4: Compute Next Actions

```javascript
// 1. Get all incomplete tasks
query_nodes({
  "type": "Task",
  "properties": { "isComplete": false }
})

// 2. For each task, check dependencies
for (const taskId of taskIds) {
  get_connected_nodes({
    "node_id": taskId,
    "direction": "out"
  })

  // 3. For each dependency, check satisfaction
  for (const depId of depIds) {
    const depNode = get_node({ "node_id": depId })

    if (depNode.type === "Task") {
      if (!depNode.properties.isComplete) {
        // Blocked
      }
    } else if (depNode.type === "State") {
      if (!depNode.properties.isTrue) {
        // Blocked
      }
    } else if (depNode.type === "Context") {
      if (!depNode.properties.isAvailable) {
        // Blocked
      }
    } else if (depNode.type === "UNSPECIFIED") {
      // Always blocked
    }
  }

  // If all satisfied, task is actionable
}
```

### Pattern 5: Delete with Dependency Check

```javascript
// 1. Check for dependents
get_connected_nodes({
  "node_id": "mem_task_002",
  "direction": "in"
})
// Returns: { "node_ids": ["mem_task_001"] }

// 2. If dependents exist, warn user
// User confirms...

// 3. Delete
delete_node({ "node_id": "mem_task_002" })
// Connections auto-deleted, but dependent nodes remain
```

## Property Constraints

- Property values must be string, number, or boolean (no nested objects/arrays)
- String matching is case-sensitive and exact
- Query matching uses AND semantics (all specified properties must match)
- Cannot remove properties via update (workaround: delete and recreate node)

## Topology Rules

Enforced by graph-memory-core:
- DependsOn connections: Task→Task, Task→State, Task→Context, State→Task, State→State
- UNSPECIFIED can only be target (dependency), never source
- Context can only be target, never source
- Invalid topologies will error on `create_connection`

## Error Handling

- Tool calls return errors for:
  - Non-existent node IDs
  - Invalid property types
  - Topology violations
  - Missing required parameters

- Handle errors gracefully:
  - Search before assuming existence
  - Validate inputs before tool calls
  - Surface errors to user with context
