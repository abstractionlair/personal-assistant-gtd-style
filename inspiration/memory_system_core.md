# Memory System Core Specification

## Overview

A graph-based memory system that provides typed nodes, first-class connections, and flexible content storage. Designed to support intelligent agents (like Claude) in maintaining structured, queryable memory across conversations while remaining domain-agnostic and extensible.

## Design Principles

1. **Graph semantics at the top**: Typed nodes and connections form a queryable graph
2. **Files at the bottom**: Content storage delegated to pluggable file backend
3. **Clean separation**: System properties in registry, domain content in files
4. **Minimal strict layer**: Only enforce types and topology, everything else is flexible
5. **Primitive operations**: Simple building blocks, intelligence composes them
6. **Backend agnostic**: Works with local files, cloud storage, or Anthropic's tool

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Memory System (Graph Layer)               â”‚
â”‚                                              â”‚
â”‚   - Typed nodes & connections               â”‚
â”‚   - Registry management                     â”‚
â”‚   - Query operations                        â”‚
â”‚   - Ontology validation                     â”‚
â”‚   - Invariant enforcement                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
               â”‚
               â”‚ delegates to
               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   File Storage Backend                       â”‚
â”‚   (See: file_storage_backend_interface.md)  â”‚
â”‚                                              â”‚
â”‚   - create/view/update/delete files         â”‚
â”‚   - No knowledge of graph semantics         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Core Concepts

### Nodes

**Nodes** are typed memory objects that represent entities:
- Projects, Actions, People, Documents, etc.
- Have a unique ID (opaque, system-generated)
- Have a type (from ontology)
- Have system properties (minimal, in registry)
- Have content (arbitrary, in file)

**Structure:**
```typescript
type Node = {
  id: NodeId            // Unique identifier (e.g., "mem_proj_001")
  type: string          // Node type (e.g., "Project", "Action")
  created: Timestamp    // When created
  modified: Timestamp   // Last modified
  properties: object    // System properties (minimal)
  content: {
    path: string        // Path to content file
    format: string      // Content format (markdown, json, pdf, etc.)
    size?: number       // File size in bytes
  }
}
```

**Example:**
```json
{
  "id": "mem_proj_001",
  "type": "Project",
  "created": "2025-10-16T10:00:00Z",
  "modified": "2025-10-16T15:30:00Z",
  "properties": {
    "status": "active"
  },
  "content": {
    "path": "_content/nodes/mem_proj_001.md",
    "format": "markdown",
    "size": 2048
  }
}
```

### Connections

**Connections** are first-class relationships between nodes:
- Have their own unique ID
- Have a type (from ontology)
- Link two nodes (from â†’ to)
- Have properties (for relationship metadata)
- Optionally have content (for relationship notes)

**Structure:**
```typescript
type Connection = {
  id: ConnectionId      // Unique identifier (e.g., "conn_001")
  type: string          // Connection type (e.g., "NextAction", "DependsOn")
  from: NodeId          // Source node
  to: NodeId            // Target node
  created: Timestamp    // When created
  modified: Timestamp   // Last modified
  properties: object    // Connection properties (optional)
  content?: {           // Optional content file
    path: string
    format: string
    size?: number
  }
}
```

**Example:**
```json
{
  "id": "conn_001",
  "type": "NextAction",
  "from": "mem_proj_001",
  "to": "mem_act_001",
  "created": "2025-10-16T10:15:00Z",
  "modified": "2025-10-16T10:15:00Z",
  "properties": {
    "priority": "high",
    "added": "2025-10-16"
  },
  "content": {
    "path": "_content/connections/conn_001.md",
    "format": "markdown",
    "size": 512
  }
}
```

### Registry

The **registry** is the source of truth for graph structure:
- Maps IDs to metadata
- Tracks all nodes and connections
- Stored as JSON via file backend
- Updated atomically with operations

**Structure:**
```typescript
type Registry = {
  nodes: {
    [id: NodeId]: Node
  }
  connections: {
    [id: ConnectionId]: Connection
  }
}
```

**Location:** `_system/registry.json`

### Ontology

The **ontology** defines valid types and their constraints:
- Node types (what kinds of entities exist)
- Connection types (what relationships are allowed)
- Connection topology (which node types can connect)
- Required properties (minimal)

**Structure:**
```yaml
node_types:
  - Project
  - Action
  - Person
  - Context
  - Document
  - Note

connection_types:
  NextAction:
    from: [Project]
    to: [Action]
    description: "This action is next for this project"
  
  DependsOn:
    from: [Action, Project]
    to: [Action, Project]
    description: "Source depends on target completing first"
  
  RequiresContext:
    from: [Action]
    to: [Context]
    description: "Action requires this context (location, tool, etc.)"
  
  WaitingFor:
    from: [Action, Project]
    to: [Person]
    required_properties: [since, follow_up_date]
    description: "Waiting on person to provide/complete something"
```

**Location:** `_system/ontology.yaml`

### Properties vs. Content

**System properties** (in registry):
- Minimal metadata needed for queries
- Examples: status, priority, timestamps
- Stored in registry JSON
- Fast to query

**Content** (in files):
- Rich, domain-specific information
- Examples: descriptions, notes, details
- Stored in content files (markdown, JSON, PDF, etc.)
- Only loaded when needed

**Design principle:** Keep properties minimal. Put everything else in content.

**Example:**

```json
// In registry (system properties)
{
  "id": "mem_act_001",
  "type": "Action",
  "properties": {
    "status": "next",
    "context": "phone"
  },
  "content": {
    "path": "_content/nodes/mem_act_001.md",
    "format": "markdown"
  }
}
```

```markdown
<!-- In _content/nodes/mem_act_001.md (rich content) -->
# Call contractor for kitchen quotes

## Details
Need to get at least 3 quotes for the kitchen renovation. 
Budget is $50k, prefer contractors with farmhouse style experience.

## Contacts
- Anderson Contracting: 555-1234 (neighbor recommendation)
- BuildRight Inc: 555-5678 (good online reviews)
- Smith & Sons: 555-9012 (did our bathroom)

## Notes
- Mention the timeline (need done by Q1 2026)
- Ask about payment terms
- Get references for similar projects

## Time estimate
30-45 minutes for all three calls
```

## Core Operations

### Node Operations

```typescript
// Create a new node
create_node(
  type: string,
  content: string | Buffer,
  format: string,
  properties?: object
) -> NodeId

// Get node metadata
get_node(id: NodeId) -> Node

// Update node properties
update_node(
  id: NodeId,
  properties?: object,
  content?: string | Buffer
) -> void

// Delete node (and its connections)
delete_node(id: NodeId) -> void

// Get node content
get_node_content(id: NodeId) -> string | Buffer

// Set node content
set_node_content(
  id: NodeId,
  content: string | Buffer,
  format?: string
) -> void
```

### Connection Operations

```typescript
// Create a new connection
create_connection(
  type: string,
  from: NodeId,
  to: NodeId,
  properties?: object,
  content?: string
) -> ConnectionId

// Get connection metadata
get_connection(id: ConnectionId) -> Connection

// Update connection properties
update_connection(
  id: ConnectionId,
  properties?: object,
  content?: string
) -> void

// Delete connection
delete_connection(id: ConnectionId) -> void
```

### Query Operations

```typescript
// Query nodes by type and properties
query_nodes(
  type?: string,
  property_filter?: object
) -> NodeId[]

// Example: query_nodes("Action", {status: "next", context: "phone"})

// Query connections
query_connections(
  from?: NodeId,
  to?: NodeId,
  type?: string,
  property_filter?: object
) -> ConnectionId[]

// Example: query_connections(from="mem_proj_001", type="NextAction")

// Get connected nodes (convenience method)
get_connected_nodes(
  from: NodeId,
  connection_type?: string,
  direction?: "out" | "in" | "both"
) -> NodeId[]

// Example: get_connected_nodes("mem_proj_001", "NextAction", "out")
```

### Search Operations

```typescript
// Full-text search across content
search_content(
  query: string,
  node_type?: string,
  limit?: number
) -> NodeId[]

// Example: search_content("kitchen renovation", "Project")

// Semantic search (hybrid keyword + embedding)
recall(
  query: string,
  limit?: number,
  context?: object
) -> NodeId[]

// Example: recall("what was I working on last week?", limit=10)
```

### Metadata Operations

```typescript
// Get ontology
get_ontology() -> Ontology

// Validate connection type
validate_connection(
  type: string,
  from_type: string,
  to_type: string
) -> boolean

// Example: validate_connection("NextAction", "Project", "Action") -> true
```

## Invariants

The system maintains these invariants:

### 1. Unique IDs
- Every node has unique ID
- Every connection has unique ID
- IDs never reused (even after deletion)

### 2. Valid Types
- Node types must exist in ontology
- Connection types must exist in ontology
- No ad-hoc types (unless ontology allows)

### 3. Valid Topology
- Connections only between valid node types
- From/to types must match ontology rules
- Example: NextAction only from Project to Action

### 4. No Dangling References
- Connections always reference existing nodes
- Deleting node deletes its connections
- Moving node updates connections

### 5. Required Properties
- If ontology requires properties, they must be present
- Example: WaitingFor requires 'since' and 'follow_up_date'

### 6. Registry Consistency
- Registry always reflects current state
- Operations are atomic (all succeed or all fail)
- Crashes don't leave partial state

## Implementation Details

### ID Generation

```typescript
function generateId(prefix: string = "mem"): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 9)
  return `${prefix}_${timestamp}_${random}`
}

// Examples:
// "mem_proj_l4k3j2_a7b9c2d"
// "conn_l4k3j3_x3y9z1k"
```

### Path Generation

```typescript
function getNodePath(id: NodeId, format: string): string {
  const extension = getExtension(format)
  return `_content/nodes/${id}.${extension}`
}

function getConnectionPath(id: ConnectionId): string {
  return `_content/connections/${id}.md`
}

function getExtension(format: string): string {
  const extensions = {
    'markdown': 'md',
    'json': 'json',
    'pdf': 'pdf',
    'jpeg': 'jpg',
    'png': 'png',
    // ... etc
  }
  return extensions[format] || 'txt'
}
```

### Registry Operations

```typescript
class Registry {
  private data: RegistryData
  private storage: FileStorage
  private registryPath = '_system/registry.json'
  
  async load(): Promise<void> {
    try {
      const result = await this.storage.view(this.registryPath)
      this.data = JSON.parse(result.content as string)
    } catch (error) {
      // Initialize empty registry
      this.data = { nodes: {}, connections: {} }
    }
  }
  
  async save(): Promise<void> {
    const content = JSON.stringify(this.data, null, 2)
    
    try {
      // Try to read existing
      const existing = await this.storage.view(this.registryPath)
      // Update via str_replace (atomic)
      await this.storage.str_replace(
        this.registryPath,
        existing.content as string,
        content
      )
    } catch {
      // Create new
      await this.storage.create(this.registryPath, content)
    }
  }
  
  addNode(id: NodeId, node: Node): void {
    if (this.data.nodes[id]) {
      throw new Error(`Node ${id} already exists`)
    }
    this.data.nodes[id] = node
  }
  
  getNode(id: NodeId): Node {
    const node = this.data.nodes[id]
    if (!node) {
      throw new Error(`Node ${id} not found`)
    }
    return node
  }
  
  deleteNode(id: NodeId): void {
    if (!this.data.nodes[id]) {
      throw new Error(`Node ${id} not found`)
    }
    delete this.data.nodes[id]
  }
  
  // Similar methods for connections...
}
```

### Graph Operations

```typescript
class MemoryGraph {
  constructor(
    private storage: FileStorage,
    private registry: Registry,
    private ontology: Ontology
  ) {}
  
  async createNode(
    type: string,
    content: string | Buffer,
    format: string,
    properties?: object
  ): Promise<NodeId> {
    // 1. Validate type
    if (!this.ontology.hasNodeType(type)) {
      throw new Error(`Invalid node type: ${type}`)
    }
    
    // 2. Generate ID and path
    const id = generateId("mem")
    const path = getNodePath(id, format)
    
    // 3. Write content via storage backend
    await this.storage.create(path, content)
    
    // 4. Add to registry
    const node: Node = {
      id,
      type,
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      properties: properties || {},
      content: { path, format }
    }
    this.registry.addNode(id, node)
    
    // 5. Save registry
    await this.registry.save()
    
    return id
  }
  
  async createConnection(
    type: string,
    from: NodeId,
    to: NodeId,
    properties?: object,
    content?: string
  ): Promise<ConnectionId> {
    // 1. Validate nodes exist
    const fromNode = this.registry.getNode(from)
    const toNode = this.registry.getNode(to)
    
    // 2. Validate connection type and topology
    if (!this.ontology.hasConnectionType(type)) {
      throw new Error(`Invalid connection type: ${type}`)
    }
    
    if (!this.ontology.canConnect(type, fromNode.type, toNode.type)) {
      throw new Error(
        `Cannot connect ${fromNode.type} -> ${toNode.type} with ${type}`
      )
    }
    
    // 3. Validate required properties
    const required = this.ontology.getRequiredProperties(type)
    for (const prop of required) {
      if (!properties?.[prop]) {
        throw new Error(`Required property missing: ${prop}`)
      }
    }
    
    // 4. Generate ID
    const id = generateId("conn")
    
    // 5. Optionally write content
    let contentInfo = undefined
    if (content) {
      const path = getConnectionPath(id)
      await this.storage.create(path, content)
      contentInfo = { path, format: 'markdown' }
    }
    
    // 6. Add to registry
    const connection: Connection = {
      id,
      type,
      from,
      to,
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      properties: properties || {},
      content: contentInfo
    }
    this.registry.addConnection(id, connection)
    
    // 7. Save registry
    await this.registry.save()
    
    return id
  }
  
  async deleteNode(id: NodeId): Promise<void> {
    // 1. Get node (throws if not found)
    const node = this.registry.getNode(id)
    
    // 2. Find and delete all connected connections
    const connections = this.queryConnections({ from: id })
      .concat(this.queryConnections({ to: id }))
    
    for (const connId of connections) {
      await this.deleteConnection(connId)
    }
    
    // 3. Delete content file
    await this.storage.delete(node.content.path)
    
    // 4. Remove from registry
    this.registry.deleteNode(id)
    
    // 5. Save registry
    await this.registry.save()
  }
  
  queryNodes(
    type?: string,
    propertyFilter?: object
  ): NodeId[] {
    const allNodes = this.registry.getAllNodes()
    
    return allNodes
      .filter(node => {
        // Type filter
        if (type && node.type !== type) return false
        
        // Property filter
        if (propertyFilter) {
          for (const [key, value] of Object.entries(propertyFilter)) {
            if (node.properties[key] !== value) return false
          }
        }
        
        return true
      })
      .map(node => node.id)
  }
  
  queryConnections(params: {
    from?: NodeId,
    to?: NodeId,
    type?: string,
    propertyFilter?: object
  }): ConnectionId[] {
    const allConns = this.registry.getAllConnections()
    
    return allConns
      .filter(conn => {
        if (params.from && conn.from !== params.from) return false
        if (params.to && conn.to !== params.to) return false
        if (params.type && conn.type !== params.type) return false
        
        if (params.propertyFilter) {
          for (const [key, value] of Object.entries(params.propertyFilter)) {
            if (conn.properties[key] !== value) return false
          }
        }
        
        return true
      })
      .map(conn => conn.id)
  }
  
  getConnectedNodes(
    from: NodeId,
    connectionType?: string,
    direction: "out" | "in" | "both" = "out"
  ): NodeId[] {
    const connections: ConnectionId[] = []
    
    if (direction === "out" || direction === "both") {
      connections.push(...this.queryConnections({ 
        from, 
        type: connectionType 
      }))
    }
    
    if (direction === "in" || direction === "both") {
      connections.push(...this.queryConnections({ 
        to: from, 
        type: connectionType 
      }))
    }
    
    return connections.map(connId => {
      const conn = this.registry.getConnection(connId)
      return direction === "out" ? conn.to : conn.from
    })
  }
}
```

## Error Handling

### Error Types

```typescript
class GraphError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: object
  ) {
    super(message)
    this.name = 'GraphError'
  }
}

// Error codes
'NODE_NOT_FOUND'
'CONNECTION_NOT_FOUND'
'INVALID_NODE_TYPE'
'INVALID_CONNECTION_TYPE'
'INVALID_TOPOLOGY'
'REQUIRED_PROPERTY_MISSING'
'NODE_ALREADY_EXISTS'
'CONNECTION_ALREADY_EXISTS'
'DANGLING_REFERENCE'
```

### Transaction Safety

For multi-step operations:

```typescript
class Transaction {
  private operations: Operation[] = []
  private rollbackActions: (() => Promise<void>)[] = []
  
  async execute(graph: MemoryGraph): Promise<void> {
    try {
      for (const op of this.operations) {
        const rollback = await this.executeOp(op, graph)
        this.rollbackActions.push(rollback)
      }
      
      // All succeeded - commit
      await graph.registry.save()
      
    } catch (error) {
      // Rollback in reverse order
      for (const rollback of this.rollbackActions.reverse()) {
        await rollback()
      }
      throw error
    }
  }
}
```

## Directory Structure

```
/memories/
  _system/
    registry.json          # Graph structure (source of truth)
    ontology.yaml          # Type definitions
    
  _content/
    nodes/
      mem_proj_001.md      # Node content files
      mem_act_001.md
      mem_doc_001.pdf
      mem_img_001.jpg
      
    connections/
      conn_001.md          # Connection content (optional)
      conn_002.md
```

## Usage Examples

### Creating a GTD Project

```typescript
// Create project node
const projectId = await graph.createNode(
  'Project',
  '# Renovate Kitchen\n\nBudget: $50k\nTimeline: Q1 2026',
  'markdown',
  { status: 'active' }
)

// Create action node
const actionId = await graph.createNode(
  'Action',
  '# Call contractor\n\nGet quotes from 3 contractors...',
  'markdown',
  { status: 'next', context: 'phone' }
)

// Link them
const connId = await graph.createConnection(
  'NextAction',
  projectId,
  actionId,
  { priority: 'high', added: '2025-10-16' }
)
```

### Querying Next Actions

```typescript
// Find all next actions
const nextActions = graph.queryNodes('Action', { status: 'next' })

// Find next actions for a project
const projectActions = graph.getConnectedNodes(
  projectId,
  'NextAction',
  'out'
)

// Find actions requiring phone
const phoneActions = graph.queryNodes('Action', { 
  status: 'next', 
  context: 'phone' 
})
```

### Complex Queries

```typescript
// Find stuck projects (no next actions)
const allProjects = graph.queryNodes('Project', { status: 'active' })
const stuckProjects = allProjects.filter(projId => {
  const nextActions = graph.getConnectedNodes(projId, 'NextAction')
  return nextActions.length === 0
})

// Find overdue waiting items
const waiting = graph.queryConnections({ type: 'WaitingFor' })
const overdue = waiting.filter(connId => {
  const conn = graph.getConnection(connId)
  const followUp = new Date(conn.properties.follow_up_date)
  return followUp < new Date()
})
```

## Performance Considerations

### Query Optimization

- Registry kept in memory for fast queries
- Content files only loaded when needed
- Indexes can be added for frequent queries

### Scaling

- Registry size is primary concern
- For 10,000 nodes + 20,000 connections:
  - Registry: ~5-10 MB (easily fits in memory)
  - Content: Unlimited (loaded on demand)

### Caching

```typescript
class CachedGraph extends MemoryGraph {
  private contentCache = new LRU<NodeId, string | Buffer>(100)
  
  async getNodeContent(id: NodeId): Promise<string | Buffer> {
    if (this.contentCache.has(id)) {
      return this.contentCache.get(id)!
    }
    
    const content = await super.getNodeContent(id)
    this.contentCache.set(id, content)
    return content
  }
}
```

## Testing

### Unit Tests

```typescript
describe('MemoryGraph', () => {
  let graph: MemoryGraph
  
  beforeEach(async () => {
    const storage = createTestStorage()
    const registry = new Registry(storage)
    const ontology = loadTestOntology()
    graph = new MemoryGraph(storage, registry, ontology)
  })
  
  test('create and get node', async () => {
    const id = await graph.createNode(
      'Project',
      '# Test Project',
      'markdown'
    )
    
    const node = graph.getNode(id)
    expect(node.type).toBe('Project')
    expect(node.id).toBe(id)
  })
  
  test('create connection enforces topology', async () => {
    const proj = await graph.createNode('Project', 'proj', 'markdown')
    const person = await graph.createNode('Person', 'person', 'markdown')
    
    // NextAction: Project -> Action (valid)
    // NextAction: Project -> Person (invalid)
    await expect(
      graph.createConnection('NextAction', proj, person)
    ).rejects.toThrow('Cannot connect')
  })
  
  test('delete node removes connections', async () => {
    const proj = await graph.createNode('Project', 'p', 'markdown')
    const action = await graph.createNode('Action', 'a', 'markdown')
    const conn = await graph.createConnection('NextAction', proj, action)
    
    await graph.deleteNode(proj)
    
    expect(() => graph.getConnection(conn)).toThrow()
  })
})
```

## Extension Points

### Custom Ontologies

Different use cases load different ontologies:

```typescript
// GTD ontology
const gtdOntology = loadOntology('_system/ontology_gtd.yaml')

// Fitness ontology
const fitnessOntology = loadOntology('_system/ontology_fitness.yaml')

// Combined ontology
const combinedOntology = mergeOntologies([gtdOntology, fitnessOntology])
```

### Custom Queries

Build domain-specific queries on primitives:

```typescript
// GTD helper
function getAvailableActions(
  graph: MemoryGraph,
  context: string[],
  timeAvailable: number
): NodeId[] {
  // 1. Get all next actions
  const actions = graph.queryNodes('Action', { status: 'next' })
  
  // 2. Filter by context
  const contextFiltered = actions.filter(id => {
    const node = graph.getNode(id)
    return context.includes(node.properties.context)
  })
  
  // 3. Check dependencies
  const available = contextFiltered.filter(id => {
    const deps = graph.getConnectedNodes(id, 'DependsOn', 'out')
    return deps.every(depId => {
      const dep = graph.getNode(depId)
      return dep.properties.status === 'complete'
    })
  })
  
  return available
}
```

## Summary

The memory system core provides:
- **Graph semantics**: Typed nodes, first-class connections
- **Flexible content**: Any format, stored in files
- **Primitive operations**: Simple building blocks for intelligence
- **Strong invariants**: Type safety, referential integrity
- **Backend agnostic**: Works with any file storage
- **Extensible**: Custom ontologies, custom queries

This foundation supports intelligent agents in maintaining structured, queryable memory while remaining flexible enough for diverse use cases (GTD, fitness coaching, executive assistance, etc.).
