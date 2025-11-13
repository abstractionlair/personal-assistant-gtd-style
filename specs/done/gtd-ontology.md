# Specification: GTD Ontology

**Feature ID:** feature_003
**Version:** 1.3
**Status:** Approved
**Created:** 2025-11-01
**Last Updated:** 2025-11-01
**Author:** spec-writing-helper

## Overview

The GTD Ontology feature defines and implements GTD-specific structures on top of the generic graph-memory-core system. It establishes the data model that enables conversational GTD coaching by creating node types (Task, State, Context, UNSPECIFIED), connection types (DependsOn), and query-based derived views (Projects, Next Actions, Waiting For).

This feature provides the semantic foundation for the GTD system, transforming the generic graph memory layer into a structured representation of tasks, dependencies, world conditions, and contexts. By using State nodes with ANY/ALL/MANUAL/IMMUTABLE logic, Context nodes for location/tool availability tracking, and a flexible DependsOn connection model, the ontology supports sophisticated dependency management while keeping the core model simple and extensible.

## Feature Scope

### Included

- **Ontology Definition**: Task, State, and Context node types with their required and optional properties
- **Singleton Node Type**: UNSPECIFIED singleton type for marking tasks needing dependency decomposition
- **Connection Type**: DependsOn connection with topology rules supporting Task↔Task, Task↔State, Task→Context, State↔Task, State↔State, and [Task|State]→UNSPECIFIED
- **Setup Script**: One-time initialization script calling `create_ontology` and `ensure_singleton_node`
- **Property Schemas**: Documented property types and constraints (isComplete, isTrue, logic, isTrue, responsibleParty, timestamps)
- **State Logic Types**: Support for ANY, ALL, MANUAL, and IMMUTABLE logic on State nodes
- **Context Availability Tracking**: Context nodes with isTrue property set manually by AI based on user reports
- **Query Pattern Documentation**: How to derive Projects, Next Actions, and Waiting For using graph-memory-core primitives
- **State Update Algorithm**: Documented algorithm for ANY/ALL logic evaluation (for Feature 4 implementation)
- **Completion Propagation Pattern**: Documented forward traversal pattern when marking items complete (for Feature 4 implementation)
- **Integration Tests**: Tests validating ontology structure, query patterns, error conditions, performance, and all scenarios

### Excluded (Not in This Feature)

- **Person nodes**: Deferred to Phase 2 per SCOPE.md
- **New MCP helper tools**: No `get_projects()`, `get_next_actions()` tools; conversational layer (Feature 4) composes primitives
- **Conversational layer**: System prompts and conversation patterns are Feature 4
- **Actual GTD usage**: Creating and managing real Tasks/States in production is Feature 4
- **State update logic implementation**: Feature 3 documents the algorithm; Feature 4 implements it
- **Completion propagation implementation**: Feature 3 documents the pattern; Feature 4 implements it
- **Weekly review logic**: Surfacing UNSPECIFIED dependencies in reviews is future work
- **Validation enforcement**: graph-memory-core should handle topology validation (may require enhancement if not supported)

### Deferred (Maybe in This Feature)

None - scope is minimal and well-defined.

## User/System Perspective

After Feature 3 is complete, the GTD ontology is loaded into the graph-memory-core system. Developers and Feature 4 (conversational layer) can:

- Create Task nodes representing actions with completion tracking and optional responsibility assignment
- Create State nodes representing world conditions with configurable dependency logic (ANY/ALL/MANUAL/IMMUTABLE)
- Create Context nodes representing locations or tool availability (e.g., atHome, hasComputer) with manual availability tracking
- Create DependsOn connections modeling dependencies between Tasks, States, and Contexts
- Query the UNSPECIFIED singleton to mark tasks needing decomposition
- Execute query patterns to derive Projects (Tasks with dependencies), Next Actions (actionable Tasks), and Waiting For (externally-responsible Tasks)
- Reference documented algorithms for state update logic and completion propagation

The system maintains these structures persistently across server restarts, providing a stable foundation for the conversational GTD coaching layer.

## Value Delivered

This feature delivers the semantic foundation that transforms generic graph memory into a GTD system. It resolves the core data modeling challenge: how to represent tasks, dependencies, and world conditions in a flexible graph structure that supports both simple standalone actions and complex multi-dependency projects.

By establishing this ontology now (Feature 3), the conversational layer (Feature 4) can focus purely on interaction patterns without solving data modeling problems. The derived-view approach (Projects/Next Actions as queries rather than separate node types) provides flexibility while maintaining data model simplicity.

Derisks: GTD model completeness; validates that the ontology design supports all MVP use cases including state-based dependencies and flexible querying.

## Interface Contract

### Setup Script: `initialize-gtd-ontology.ts`

**Purpose:** One-time initialization that loads GTD ontology into graph-memory-core

**Signature:**
```typescript
function initializeGTDOntology(): { ok: boolean, error?: string }
```

**Inputs:** None

**Returns:**
- `{ ok: true }` on success
- `{ ok: false, error: "<error message>" }` on failure

**Exit Codes:**
- 0: Success
- 1: Ontology creation failed
- 2: UNSPECIFIED singleton creation failed

**Operations:**
1. Call `create_ontology` with GTD schema
2. Call `ensure_singleton_node` to create UNSPECIFIED singleton
3. Return success/failure status with error details if applicable

**Idempotency:** Running multiple times should not fail or create duplicates (ensure_singleton_node returns existing instance if already created)

**Error Handling:**
- Logs detailed error messages on failure
- Returns error string in result object
- Exits with appropriate non-zero code on failure

---

### Ontology Schema: Input to `create_ontology`

**Purpose:** Define GTD node types and connection types

**Schema Structure:**

```typescript
{
  node_types: ["Task", "State", "Context", "UNSPECIFIED"],
  connection_types: [
    {
      name: "DependsOn",
      from_types: ["Task", "State"],
      to_types: ["Task", "State", "Context", "UNSPECIFIED"]
    }
  ]
}
```

**Note:** graph-memory-core accepts node types as simple strings. Required/optional properties are documented expectations (below) but not part of the ontology schema payload.

**Property Type Expectations (documented, not enforced by graph-memory-core):**

**Task properties:**
- `isComplete`: boolean - Whether the task is complete
- `responsibleParty`: string (optional) - Who is responsible. Value "me" indicates current user; other values indicate external party
- `created`, `modified`: timestamps (automatic, provided by graph-memory-core)

**State properties:**
- `isTrue`: boolean - Whether this world condition is currently true
- `logic`: string enum - How this State determines its truth value:
  - `"ANY"`: isTrue when at least one incoming DependsOn dependency is satisfied
  - `"ALL"`: isTrue when all incoming DependsOn dependencies are satisfied
  - `"MANUAL"`: isTrue set explicitly by user/AI (not computed from dependencies)
  - `"IMMUTABLE"`: isTrue never changes (like UNSPECIFIED)
- `created`, `modified`: timestamps (automatic)

**Context properties:**
- `isTrue`: boolean - Whether this context (location/tool) is currently available to work in
- `created`, `modified`: timestamps (automatic)
- Note: Set manually by AI when user reports location or tool availability (similar to MANUAL States)

**UNSPECIFIED singleton:**
- No additional properties required
- Singleton semantics enforced by `ensure_singleton_node`

**Returns:** Success/failure from graph-memory-core

**Postconditions:**
- Ontology persisted in graph-memory-core
- Can create nodes of type Task, State, Context, UNSPECIFIED
- Can create connections of type DependsOn with specified topology rules

---

### Singleton Creation: Input to `ensure_singleton_node`

**Purpose:** Create the UNSPECIFIED singleton node marking "dependencies yet to be specified"

**Input:**

```typescript
{
  type: "UNSPECIFIED",
  content: "This is a placeholder indicating that dependencies are yet to be specified. Tasks or States depending on UNSPECIFIED cannot be marked complete until concrete dependencies are defined.",
  encoding: "utf-8"
}
```

**Returns:** Node ID of the UNSPECIFIED singleton

**Idempotency Semantics:**
- First call: Creates new UNSPECIFIED node and returns its ID
- Subsequent calls: Returns existing node ID (no new node created)
- If orphan duplicate exists due to manual edits: Implementation-defined behavior (may return first found, or error - graph-memory-core decides)

**Singleton Behavior:**
- Only one instance can exist
- Used as dependency target for Tasks/States needing decomposition
- Tasks depending on UNSPECIFIED are never actionable
- No outgoing dependencies from UNSPECIFIED (singleton types cannot have outgoing DependsOn connections)
- Cannot be deleted (deletion is rejected or no-op to preserve singleton semantics)

**Postconditions:**
- UNSPECIFIED node exists and is queryable via `query_nodes({type: "UNSPECIFIED"})`
- Subsequent calls return existing instance (no duplicates)

---

### Query Pattern: Projects

**Purpose:** Find all Tasks that have outgoing DependsOn connections (Tasks with dependencies = Projects)

**Algorithm:**

```typescript
// Step 1: Get all Tasks
const allTasks = query_nodes({type: "Task"})

// Step 2: For each Task, check if it has outgoing DependsOn connections
const projects = []
for (const task of allTasks) {
  const dependencies = query_connections({
    from_node_id: task.id,
    type: "DependsOn"
  })

  if (dependencies.length > 0) {
    projects.push(task)
  }
}
```

**Returns:** Array of Task nodes that are "Projects" (have dependencies)

**Note:** This is a derived view - Projects are not a separate node type

---

### Query Pattern: Next Actions

**Purpose:** Find actionable Tasks (not complete, all dependencies satisfied)

**Algorithm:**

```typescript
// Step 1: Get all incomplete Tasks
const incompleteTasks = query_nodes({
  type: "Task",
  properties: {isComplete: false}
})

// Step 2: Filter to those whose immediate dependencies are satisfied
const nextActions = []
for (const task of incompleteTasks) {
  const dependencies = get_connected_nodes({
    node_id: task.id,
    connection_type: "DependsOn",
    direction: "outgoing"
  })

  if (allDependenciesSatisfied(dependencies)) {
    nextActions.push(task)
  }
}

function allDependenciesSatisfied(depNodes) {
  // Check each immediate dependency
  for (const dep of depNodes) {
    if (dep.type === "Task") {
      if (!dep.properties.isComplete) return false
    } else if (dep.type === "State") {
      if (!dep.properties.isTrue) return false
    } else if (dep.type === "Context") {
      if (!dep.properties.isTrue) return false
    } else if (dep.type === "UNSPECIFIED") {
      return false // UNSPECIFIED always blocks
    }
  }
  return true
}
```

**Returns:** Array of Task nodes that are actionable (Next Actions)

**Note:**
- Only checks immediate dependencies (no recursion)
- Depends on State.isTrue being up-to-date (Feature 4 maintains this)
- Tasks depending on UNSPECIFIED are never returned

---

### Query Pattern: Waiting For

**Purpose:** Find Tasks where responsibility is external (waiting on someone else)

**Algorithm:**

```typescript
// Get all incomplete Tasks with external responsibility
const incompleteTasks = query_nodes({
  type: "Task",
  properties: {isComplete: false}
})

const waitingFor = incompleteTasks.filter(task =>
  task.properties.responsibleParty &&
  task.properties.responsibleParty !== "me"
)
```

**Returns:** Array of Tasks waiting on external parties

**Note:** "me" is special value indicating current user; all other values indicate external responsibility

---

### Algorithm Documentation: State Update Logic (for Feature 4)

**Purpose:** Update State.isTrue based on logic type when dependencies change

**Algorithm:**

```typescript
function updateStateBasedOnLogic(state) {
  // Only update if logic is ANY or ALL
  if (state.properties.logic === "MANUAL" || state.properties.logic === "IMMUTABLE") {
    return // No automatic updates
  }

  // Get all dependencies of this State
  const dependencies = get_connected_nodes({
    node_id: state.id,
    connection_type: "DependsOn",
    direction: "outgoing"
  })

  if (state.properties.logic === "ALL") {
    // ALL: State is true if all dependencies are satisfied
    const allSatisfied = dependencies.every(dep => {
      if (dep.type === "Task") return dep.properties.isComplete
      if (dep.type === "State") return dep.properties.isTrue
      if (dep.type === "UNSPECIFIED") return false
      return false
    })

    update_node({
      id: state.id,
      properties: {isTrue: allSatisfied}
    })
  }
  else if (state.properties.logic === "ANY") {
    // ANY: State is true if at least one dependency is satisfied
    const anySatisfied = dependencies.some(dep => {
      if (dep.type === "Task") return dep.properties.isComplete
      if (dep.type === "State") return dep.properties.isTrue
      // UNSPECIFIED never satisfies
      return false
    })

    update_node({
      id: state.id,
      properties: {isTrue: anySatisfied}
    })
  }
}
```

**Usage (Feature 4):** Call this function when marking a Task complete or a State true, for all States that depend on the updated node

**Note:** This algorithm is **documented** in Feature 3 but **implemented** by Feature 4 (conversational layer)

---

### Pattern Documentation: Completion Propagation (for Feature 4)

**Purpose:** When marking Task/State complete, propagate effects forward to dependent nodes

**Algorithm:**

```typescript
function markComplete(nodeId) {
  const node = get_node(nodeId)

  // Step 1: Mark the node complete/true
  if (node.type === "Task") {
    update_node({id: nodeId, properties: {isComplete: true}})
  } else if (node.type === "State" && node.properties.logic === "MANUAL") {
    update_node({id: nodeId, properties: {isTrue: true}})
  }

  // Step 2: Find all nodes that depend on this one
  const dependents = query_connections({
    to_node_id: nodeId,
    type: "DependsOn"
  })

  // Step 3: For each dependent State, check if it should update
  for (const conn of dependents) {
    const dependent = get_node(conn.from_node_id)

    if (dependent.type === "State" &&
        dependent.properties.logic !== "MANUAL" &&
        dependent.properties.logic !== "IMMUTABLE") {

      updateStateBasedOnLogic(dependent)

      // If State became true, recursively propagate
      if (dependent.properties.isTrue) {
        markComplete(dependent.id)
      }
    }
  }
}
```

**Usage (Feature 4):** Call this function when user completes a Task or reports a MANUAL State as true

**Note:** This pattern is **documented** in Feature 3 but **implemented** by Feature 4 (conversational layer)

**Rationale:** Forward propagation when updating (not backward traversal when querying) keeps State.isTrue as cached source of truth

## Acceptance Criteria

### Ontology Initialization
- [ ] AC1: Setup script successfully calls `create_ontology` with GTD schema (Task, State, Context, UNSPECIFIED node types; DependsOn connection type)
- [ ] AC2: Ontology is persisted in graph-memory-core and survives server restarts
- [ ] AC3: UNSPECIFIED singleton is created with type="UNSPECIFIED"
- [ ] AC4: UNSPECIFIED singleton is queryable via `query_nodes({type: "UNSPECIFIED"})`
- [ ] AC5: Running setup script multiple times does not fail or create duplicate UNSPECIFIED nodes

### Node Type Validation
- [ ] AC6: Can create Task nodes with required property `isComplete` (boolean)
- [ ] AC7: Can create Task nodes with optional property `responsibleParty` (string)
- [ ] AC8: Can create State nodes with required properties `isTrue` (boolean) and `logic` ("ANY"|"ALL"|"IMMUTABLE"|"MANUAL")
- [ ] AC9: Can create Context nodes with required property `isTrue` (boolean)
- [ ] AC10: Created/modified timestamps are automatically added by graph-memory-core to all nodes

### Connection Topology Validation
- [ ] AC11: Can create DependsOn connection from Task to Task
- [ ] AC12: Can create DependsOn connection from Task to State
- [ ] AC13: Can create DependsOn connection from Task to Context
- [ ] AC14: Can create DependsOn connection from State to Task
- [ ] AC15: Can create DependsOn connection from State to State
- [ ] AC16: Can create DependsOn connection from Task to UNSPECIFIED
- [ ] AC17: Can create DependsOn connection from State to UNSPECIFIED

### Query Pattern - Projects
- [ ] AC18: Can query all Tasks with outgoing DependsOn connections (Projects)
- [ ] AC19: Tasks with no outgoing dependencies are excluded from Projects query
- [ ] AC20: Query correctly identifies Tasks with 1+ outgoing DependsOn connections

### Query Pattern - Next Actions
- [ ] AC21: Can query incomplete Tasks where all immediate dependencies are satisfied
- [ ] AC22: Tasks with isComplete=true are excluded from Next Actions query
- [ ] AC23: Tasks depending on incomplete Tasks are excluded from Next Actions query
- [ ] AC24: Tasks depending on States with isTrue=false are excluded from Next Actions query
- [ ] AC25: Tasks depending on Contexts with isTrue=false are excluded from Next Actions query
- [ ] AC26: Tasks depending on UNSPECIFIED are excluded from Next Actions query (UNSPECIFIED always blocks)

### Query Pattern - Waiting For
- [ ] AC27: Can query incomplete Tasks where responsibleParty is set and not "me"
- [ ] AC28: Tasks with responsibleParty="me" are excluded from Waiting For query
- [ ] AC29: Tasks with no responsibleParty are excluded from Waiting For query

### Error Handling
- [ ] AC30: Attempting to create DependsOn connection with UNSPECIFIED as source (from_node_id) is rejected with validation error
- [ ] AC31: Attempting to create DependsOn connection with Context as source (from_node_id) is rejected with validation error
- [ ] AC32: Calling `ensure_singleton_node` for UNSPECIFIED multiple times returns existing instance (no duplicates created)
- [ ] AC33: Attempting to delete UNSPECIFIED singleton is rejected or is a no-op (singleton preserved)

**Note:** graph-memory-core does not currently enforce node-level required properties. Feature 4 (conversational layer) is responsible for creating nodes with correct properties. Tests should verify happy-path property usage but not expect validation errors for missing properties.

### Performance
- [ ] AC34: Projects query completes in <2 seconds for dataset of 100 Tasks, 50 Projects, 500 connections (representative MVP scale)
- [ ] AC35: Next Actions query completes in <2 seconds for dataset of 100 Tasks, 50 States, 20 Contexts, 500 connections (representative MVP scale)

### Documentation
- [ ] AC36: State update algorithm (ANY/ALL logic) is documented for Feature 4 reference
- [ ] AC37: Completion propagation pattern is documented for Feature 4 reference
- [ ] AC38: All query patterns have example code demonstrating usage

## Scenarios

### Scenario 1: Simple Standalone Task

**Description:** A one-off task with no dependencies

**Given:**
- GTD ontology is loaded

**When:**
- Create Task with `isComplete=false`, `responsibleParty="me"`, content="Buy birthday card for spouse"

**Then:**
- Next Actions query returns this Task (no dependencies, isComplete=false)
- Projects query does NOT return this Task (no outgoing dependencies)
- Waiting For query does NOT return this Task (responsibleParty="me")

**After marking complete:**
- Update Task with `isComplete=true`
- Next Actions query does NOT return this Task (isComplete=true)

---

### Scenario 2: Project with Sequential Tasks

**Description:** "Launch website" project with multiple dependent tasks

**Given:**
- GTD ontology is loaded
- Task1 "Design website" with isComplete=false (no dependencies)
- Task2 "Build website" with isComplete=false, DependsOn Task1
- Task3 "Deploy website" with isComplete=false, DependsOn Task2

**When:**
- Query Projects, Next Actions, Waiting For

**Then:**
- **Projects:** Returns Task2 and Task3 (both have outgoing dependencies)
- **Next Actions:** Returns ONLY Task1 (others blocked by dependencies)
- **Waiting For:** Returns nothing (all responsibleParty="me")

**When:**
- Mark Task1 complete (isComplete=true)

**Then:**
- **Next Actions:** Returns Task2 (Task1 dependency satisfied), NOT Task3 (still blocked by Task2)

**When:**
- Mark Task2 complete (isComplete=true)

**Then:**
- **Next Actions:** Returns Task3 (Task2 dependency satisfied)

---

### Scenario 3: Task with State Precondition (ALL logic)

**Description:** Task blocked until multiple conditions are met

**Given:**
- State "Budget approved" with isTrue=false, logic="ALL"
- Task "Finance approval" with isComplete=false, DependsOn nothing
- Task "Leadership approval" with isComplete=false, DependsOn nothing
- State "Budget approved" DependsOn both approval tasks
- Task "Hire contractor" with isComplete=false, DependsOn "Budget approved" State

**When:**
- Query Next Actions initially

**Then:**
- Returns "Finance approval" and "Leadership approval" (no dependencies)
- Does NOT return "Hire contractor" (Budget State isTrue=false)

**When:**
- Mark "Finance approval" complete
- Call updateStateBasedOnLogic("Budget approved")

**Then:**
- Budget State remains isTrue=false (ALL logic, not all dependencies satisfied)
- Next Actions still does NOT return "Hire contractor"

**When:**
- Mark "Leadership approval" complete
- Call updateStateBasedOnLogic("Budget approved")

**Then:**
- Budget State updates to isTrue=true (ALL dependencies satisfied)
- Next Actions NOW returns "Hire contractor" (dependency satisfied)

---

### Scenario 4: Waiting For (External Responsibility)

**Description:** Task blocked on external party

**Given:**
- Task "Waiting for logo designs" with isComplete=false, responsibleParty="Jane (designer)"

**When:**
- Query Next Actions and Waiting For

**Then:**
- **Next Actions:** Does NOT return this Task (responsibleParty not "me")
- **Waiting For:** Returns this Task (responsibleParty set and not "me")

**When:**
- Mark Task complete (isComplete=true)

**Then:**
- **Waiting For:** Does NOT return this Task (isComplete=true)

---

### Scenario 5: UNSPECIFIED Dependencies

**Description:** Task created but dependencies not yet determined

**Given:**
- Task "Improve performance of risk engine" with isComplete=false
- DependsOn connection from Task to UNSPECIFIED singleton

**When:**
- Query Projects and Next Actions

**Then:**
- **Next Actions:** Does NOT return Task (depends on UNSPECIFIED which always blocks)
- **Projects:** Returns Task (has outgoing dependency)

**When:**
- Delete UNSPECIFIED connection
- Add concrete dependencies (e.g., profile task, optimize task, test task)

**Then:**
- **Next Actions:** May return Task if new dependencies are satisfied

---

### Scenario 6: State with ANY Logic

**Description:** Task becomes actionable when ANY of multiple conditions are met (alternative paths)

**Given:**
- State "Can start construction" with isTrue=false, logic="ANY"
- Task "Get permits" with isComplete=false
- Task "Get emergency waiver" with isComplete=false, responsibleParty="city council"
- State DependsOn both tasks
- Task "Begin construction" with isComplete=false, DependsOn State

**When:**
- Query Next Actions initially

**Then:**
- Returns "Get permits" (no dependencies)
- Does NOT return "Begin construction" (State isTrue=false)
- Waiting For returns "Get emergency waiver" (external responsibility)

**When:**
- Mark "Get permits" complete
- Call updateStateBasedOnLogic("Can start construction")

**Then:**
- State updates to isTrue=true (ANY logic - at least one satisfied)
- Next Actions NOW returns "Begin construction" (State satisfied)
- Note: "Get emergency waiver" still incomplete, but that's OK with ANY logic

---

### Scenario 7: State with MANUAL Logic

**Description:** State that doesn't derive from dependencies - must be manually reported/set

**Given:**
- State "Weather is good" with isTrue=false, logic="MANUAL", content="Weather suitable for outdoor painting (no rain, temp above 50°F)"
- Task "Paint exterior of house" with isComplete=false, DependsOn State

**When:**
- Query Next Actions initially

**Then:**
- Does NOT return "Paint exterior" (State isTrue=false)

**When:**
- User reports "weather is good today"
- Feature 4 updates State with isTrue=true

**Then:**
- Next Actions returns "Paint exterior" (State satisfied)

**When:**
- User reports "it's raining now"
- Feature 4 updates State with isTrue=false

**Then:**
- Next Actions does NOT return "Paint exterior" (State false again)

**Note:** MANUAL states don't auto-update from dependencies - they reflect real-world conditions user observes and reports

---

### Scenario 8: Context-Based Filtering

**Description:** Task can only be done in specific context (location or tool availability)

**Given:**
- Context "atHome" with isTrue=false
- Context "hasComputer" with isTrue=true
- Task "Write blog post" with isComplete=false, DependsOn hasComputer
- Task "Mow lawn" with isComplete=false, DependsOn atHome

**When:**
- Query Next Actions initially

**Then:**
- Returns "Write blog post" (hasComputer is available)
- Does NOT return "Mow lawn" (atHome is not available)

**When:**
- User reports "I'm home now"
- Feature 4 updates atHome Context with isTrue=true
- User reports "Computer is off"
- Feature 4 updates hasComputer Context with isTrue=false

**Then:**
- Next Actions returns "Mow lawn" (atHome now available)
- Next Actions does NOT return "Write blog post" (hasComputer not available)

**Note:** Context availability is set manually by AI based on user reports (similar to MANUAL States)

---

### Scenario 9: Invalid Topology Error

**Description:** Attempting to create invalid DependsOn connections is rejected

**Given:**
- UNSPECIFIED singleton exists
- Task "Some task" exists
- Context "atHome" exists

**When:**
- Attempt to create DependsOn from UNSPECIFIED to Task (invalid: singleton cannot be source)

**Then:**
- Operation is rejected with validation error
- Error message indicates invalid topology: "UNSPECIFIED cannot have outgoing dependencies"
- No connection is created

**When:**
- Attempt to create DependsOn from Context to Task (invalid: Context cannot be source)

**Then:**
- Operation is rejected with validation error
- Error message indicates invalid topology: "Context nodes cannot be dependency sources"
- No connection is created

## Data Structures

### Task Node Properties

**Type:** Node properties object (stored in graph-memory-core registry)

**Structure:**
```typescript
{
  isComplete: boolean,
  responsibleParty?: string,
  created: timestamp, // automatic
  modified: timestamp // automatic
}
```

**Invariants:**
- `isComplete` is required (no default)
- `responsibleParty` is optional; value "me" indicates current user
- Timestamps managed by graph-memory-core

**Example:**
```typescript
{
  isComplete: false,
  responsibleParty: "me",
  created: "2025-11-01T10:00:00Z",
  modified: "2025-11-01T10:00:00Z"
}
```

---

### State Node Properties

**Type:** Node properties object (stored in graph-memory-core registry)

**Structure:**
```typescript
{
  isTrue: boolean,
  logic: "ANY" | "ALL" | "MANUAL" | "IMMUTABLE",
  created: timestamp, // automatic
  modified: timestamp // automatic
}
```

**Invariants:**
- Both `isTrue` and `logic` are required (no defaults)
- `logic` values:
  - "ANY": isTrue when at least one dependency satisfied
  - "ALL": isTrue when all dependencies satisfied
  - "MANUAL": isTrue set explicitly (not computed)
  - "IMMUTABLE": isTrue never changes
- Timestamps managed by graph-memory-core

**Example:**
```typescript
{
  isTrue: false,
  logic: "ALL",
  created: "2025-11-01T10:00:00Z",
  modified: "2025-11-01T10:00:00Z"
}
```

---

### Context Node Properties

**Type:** Node properties object (stored in graph-memory-core registry)

**Structure:**
```typescript
{
  isTrue: boolean,
  created: timestamp, // automatic
  modified: timestamp // automatic
}
```

**Invariants:**
- `isTrue` is required (no default)
- Set manually by Feature 4 when user reports location or tool availability
- Contexts are dependency targets only (never sources)

**Example:**
```typescript
{
  isTrue: true,
  created: "2025-11-01T10:00:00Z",
  modified: "2025-11-01T10:00:00Z"
}
```

**Common Context Examples:**
- `atHome` - At home location
- `@work` - At work location
- `hasComputer` - Computer is available
- `hasPhone` - Phone is available
- `@errands` - Out running errands

---

### UNSPECIFIED Singleton

**Type:** Singleton node (only one instance)

**Properties:**
```typescript
{
  // No additional properties required
  created: timestamp, // automatic
  modified: timestamp // automatic
}
```

**Content:**
```
"This is a placeholder indicating that dependencies are yet to be specified. Tasks or States depending on UNSPECIFIED cannot be marked complete until concrete dependencies are defined."
```

**Semantics:**
- Special singleton type (not a State with special properties)
- Can be dependency target (Task/State → UNSPECIFIED)
- Cannot have outgoing dependencies (singleton types don't participate as dependency sources)
- Always blocks actionability (Next Actions never returns anything depending on UNSPECIFIED)

**Access:**
```typescript
const unspecified = query_nodes({type: "UNSPECIFIED"})[0]
```

## Dependencies

### External Dependencies

- **graph-memory-core MCP server** (Feature 2) - ✅ Complete
  - Provides: `create_ontology`, `create_node`, `update_node`, `query_nodes`, `query_connections`, `get_connected_nodes`, `delete_connection`
  - Version: As implemented in specs/done/graph-memory-core.md
- **graph-memory-core enhancement**: `ensure_singleton_node` tool
  - Status: ⚠️ Needs implementation (trivial, a few minutes)
  - Provides safe singleton creation (no duplicates)
  - Details: As discussed with Codex GPT-5 - singletons become new node types with enforced single-instance semantics

### Internal Dependencies

- **File-Storage-Backend** (Feature 1) - ✅ Complete
  - Provides persistent storage layer for graph-memory-core
- **TypeScript/Node.js runtime**
  - For setup script execution
- **Jest testing framework**
  - For integration tests (per GUIDELINES.md)

### Assumptions

- **graph-memory-core validates topology rules** automatically based on ontology definition (Task/State → Task/State/UNSPECIFIED for DependsOn)
  - Validation: Test during integration tests; may require enhancement if not supported
- **Singleton semantics enforced by graph-memory-core** via `ensure_singleton_node` tool
  - Validation: Test that multiple calls return same instance
- **Query patterns performant at MVP scale** (<500 nodes per SCOPE.md estimate: 50-100 projects, 200-500 actions)
  - Validation: Performance tests with realistic data volumes
- **Property type expectations documented, not enforced** - graph-memory-core does not validate property types
  - Impact: Feature 4 (conversational layer) responsible for using correct types

## Constraints and Limitations

### Technical Constraints

- **Node types limited to Task, State, Context, UNSPECIFIED**: Person nodes deferred to Phase 2
- **Single connection type (DependsOn)**: All dependency relationships use same connection type; Projects/Next Actions/Waiting For are derived views
- **No property type enforcement**: graph-memory-core doesn't validate types; documented expectations only
- **Query pattern performance**: O(n) for Projects, O(n*m) for Next Actions where n=tasks, m=avg dependencies
  - Acceptable for MVP scale (<500 nodes)
  - Could add dedicated MCP tools later if needed

### Platform Constraints

- **File-based storage**: Inherited from graph-memory-core
  - Registry: `_system/registry.json`
  - Content: `_content/nodes/{id}.txt` or `.bin`
- **Timestamp handling**: Created/modified timestamps automatic (cannot customize)
- **MCP server architecture**: Setup script and tests require graph-memory-core MCP server running

### Known Limitations

- **No property immutability enforcement**: UNSPECIFIED singleton should never change, but this is convention (Feature 4 responsibility)
- **No automatic validation**: Property types are documented expectations; incorrect types won't be caught by graph-memory-core
- **No built-in query helpers**: Projects/Next Actions/Waiting For require multi-step query composition
- **One-time initialization**: Setup script not idempotent for ontology loading (but UNSPECIFIED creation is idempotent via ensure_singleton_node)

### Out of Scope

- **Person nodes**: Phase 2
- **Helper MCP tools**: Could add later if query composition proves difficult
- **State update logic**: Documented in Feature 3, implemented in Feature 4
- **Completion propagation**: Documented in Feature 3, implemented in Feature 4
- **Weekly review logic**: Future work
- **Validation enforcement**: May require graph-memory-core enhancement

## Implementation Notes

### Suggested Approach

**Setup Script Structure:**
1. Import graph-memory-core MCP client
2. Define ontology schema as object
3. Call `create_ontology` with schema
4. Call `ensure_singleton_node` for UNSPECIFIED
5. Log success/failure
6. Exit with appropriate status code

**Test Organization:**
- Group by category (setup, nodes, connections, queries, scenarios)
- Use fixtures for common test data (sample Tasks, States, connections)
- Clean graph-memory-core state between tests
- Use realistic data volumes for performance tests

### Testing Strategy

**Integration Tests Only:**
- No unit tests (setup script is straightforward initialization)
- All tests require graph-memory-core MCP server running
- Tests verify actual behavior against real system

**Test Fixtures:**
- Helper functions to create common patterns (standalone task, sequential tasks, state preconditions)
- Cleanup utilities to reset graph state
- Sample data sets for performance testing

**Coverage Goals:**
- All 38 acceptance criteria have corresponding tests
- All 9 scenarios have dedicated integration tests
- All topology combinations tested
- Performance test with realistic data volume (50 projects, 200 tasks, 500 connections)

### Performance Considerations

- Query patterns are O(n) to O(n*m) - acceptable for MVP scale
- No caching in Feature 3 (stateless query functions)
- Feature 4 could cache query results if needed
- Performance tests validate <2 second target from SCOPE.md

## Open Questions

None - all design decisions resolved during spec-writing-helper collaboration.

## References

- **ROADMAP.md** - Feature 3: GTD Ontology (Phase 1, Week 1-2)
- **VISION.md** - Technical Requirements section (lines 140-147): Task/State architecture, derived views
- **SCOPE.md** - General Graph Memory System section (lines 31, 77-83): Ontology loading, query patterns
- **specs/done/graph-memory-core.md** - Feature 2: Provides all MCP tools used by Feature 3
- **inspiration/beyond_GTD/GTD-GRAPH-Multi-Conversation.md** - Architectural evolution documenting Task/State/DependsOn design
- **GUIDELINES.md** - Testing standards (Jest framework)

---

**Document Control:**

**Version History:**
- v1.3 (2025-11-01): Addressed reviewer's minor nits (APPROVED)
  - Updated AC1 to explicitly list Context node type
  - Removed "(if graph-memory-core enforces topology)" conditional from AC30-AC31 (topology enforcement confirmed in graph-memory-core spec)
  - Updated status to Approved
- v1.2 (2025-11-01): Addressed second round of spec review feedback
  - Fixed create_ontology schema to match graph-memory-core contract (node_types as string array, not objects)
  - Removed AC33-AC35 (node-level required property validation) - graph-memory-core doesn't enforce; Feature 4 responsibility
  - Renumbered ACs: AC30-AC33 (error), AC34-AC35 (performance), AC36-AC38 (documentation)
  - Fixed postconditions to include Context
  - Updated coverage goals count to 38 ACs, 9 scenarios
  - Total acceptance criteria: 42 → 38 (removed 4 unenforceable validation ACs)
- v1.1 (2025-11-01): Addressed spec review feedback
  - Added Context nodes with isTrue property (per reviewer feedback and user decision)
  - Added error handling acceptance criteria (AC30-AC37) for invalid topology and property validation
  - Added performance acceptance criteria (AC38-AC39) for <2s queries at MVP scale
  - Clarified initialization script signature with inputs/outputs/exit codes
  - Enhanced singleton idempotency semantics documentation
  - Added Scenario 8 (Context-based filtering) and Scenario 9 (Invalid topology errors)
  - Updated query patterns to include Context.isTrue checks
  - Total acceptance criteria increased from 29 to 42
- v1.0 (2025-11-01): Initial specification following spec-writing-helper collaboration

**Related Specs:**
- Depends on: specs/done/graph-memory-core.md (Feature 2)
- Enables: Feature 4 (Conversational Layer) - to be specified next
