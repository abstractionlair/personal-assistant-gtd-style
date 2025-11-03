---
feature_id: conversational-layer
version: 2.0
status: Approved
created: 2025-11-02
author: spec-writer (revised after review)
dependencies:
  - GTD Ontology (Feature 3) - specs/done/gtd-ontology.md
  - Graph Memory Core (Feature 2) - specs/done/graph-memory-core.md
  - File Storage Backend (Feature 1)
related_specs:
  - specs/done/gtd-ontology.md
  - specs/done/graph-memory-core.md
gatekeeper: spec-reviewer
---

# Specification: Conversational Layer

## Overview

The Conversational Layer provides system prompts, conversation patterns, and instructions that enable Claude to manage GTD (Getting Things Done) memory through natural language interaction using the graph-memory-core MCP server. This feature transforms the generic graph memory infrastructure into a conversational GTD system by teaching Claude when to create Task/State/Context nodes, how to query planning structures through graph traversals, and how to maintain consistency across conversations.

This is the critical integration layer that validates the project's core assumption: "Can Claude reliably manage GTD memory structures through conversational interaction?" The feature uses the Task/State/DependsOn planning model defined in the GTD Ontology (Feature 3), where Projects, Next Actions, and Waiting For are derived views computed through queries rather than separate node types. Users interact naturally without explicit commands, and Claude learns to recognize when information should be persisted, queried, or updated based on conversational context.

## Feature Scope

### Included

**Core Capabilities:**
- Task node creation, querying, and updates through natural language
  - Properties: `isComplete: boolean`, `responsibleParty?: string`
  - No `type` field - Projects are Tasks with outgoing dependencies (derived view)
- Context node conversational patterns
  - Properties: `isAvailable: boolean`
  - Context availability tracking based on user reports
- State node creation and updates for MANUAL logic States
  - Properties: `isTrue: boolean`, `logic: "MANUAL"`
  - ANY/ALL/IMMUTABLE logic States deferred to Phase 2
- DependsOn connection creation and management
  - Topology: Task→Task, Task→State, Task→Context, State→Task supported in Phase 1
- Duplicate detection using intelligent content similarity (frontier model judgment)
- Task deletion with dependency warnings (no automatic cascade unless explicitly requested)
- UNSPECIFIED node handling (encourage decomposition, don't force)
- Inference guidelines (when to infer vs ask user for clarification)

**Query Patterns:**
- Projects query: Tasks with outgoing DependsOn connections (Tasks that depend on other Tasks/States/Contexts)
- Next Actions query: Incomplete Tasks with all immediate dependencies satisfied
- Waiting For query: Incomplete Tasks where `responsibleParty` is set and not "me"
- Context-filtered queries: Next Actions requiring only available Contexts
- Stuck projects identification: Projects with no recent activity (>2 weeks)

**Maintenance:**
- Basic weekly review (data presentation, stuck project identification)
- State update for MANUAL States (user reports world conditions)
- No automatic parent completion (user explicitly marks project complete)
- Persistence across conversation boundaries (all state in graph, not conversation)

### Excluded

**Advanced State Management (Deferred to Phase 2):**
- ANY/ALL/IMMUTABLE logic State creation and automatic updates
- State DAG traversal and propagation
- Complex state dependency evaluation

**Advanced Pattern Detection (Deferred to Phase 2A):**
- Pattern-aware weekly review (over-investment, avoidance patterns)
- Behavioral insights and recommendations

**Not in MVP:**
- Someday/Maybe category
- GUI visualization
- Real-time monitoring or file watching
- Multi-user support
- Task scheduling or calendar integration
- Priority or urgency sorting

### Deferred

- ANY/ALL/IMMUTABLE State nodes → Phase 2 (State Management)
- Automatic state propagation → Phase 2 (State Management)
- Pattern detection and behavioral insights → Phase 2A (Pattern Awareness)
- Optimization for >1000 projects → Future performance phase

## User/System Perspective

### User Perspective

Users interact with Claude through natural language without explicit commands or structured syntax. They can:
- Capture tasks by mentioning them in conversation ("I need to call the dentist")
- Describe dependencies naturally ("X depends on Y" or "Do A before B")
- Ask questions about their work ("What should I work on next?", "Show me my projects")
- Update task status ("I finished writing the report")
- Mark contexts as available/unavailable ("I'm at the office now")
- Report world conditions for MANUAL States ("The weather is good today")
- Request weekly reviews ("Show me my weekly review")
- Delete tasks with awareness of dependencies ("Remove the old design task")
- Delegate tasks externally ("Jane is handling the logo designs")

The system feels like talking to an assistant who understands task management, remembers everything across conversations, and proactively asks clarifying questions when needed.

### System Perspective

Claude maintains graph-based memory using the Graph Memory Core MCP server with the GTD Ontology:

**Node Types:**
- **Task**: Work items with `isComplete: boolean`, optional `responsibleParty: string`
- **State**: World conditions with `isTrue: boolean`, `logic: "MANUAL"` (only MANUAL in Phase 1)
- **Context**: Locations/tools with `isAvailable: boolean`
- **UNSPECIFIED**: Singleton marking incomplete decomposition

**Connection Types:**
- **DependsOn**: Directional dependencies (Task→Task, Task→State, Task→Context, State→Task)

**Derived Views** (computed via queries, not stored):
- **Projects**: Tasks with outgoing DependsOn connections (query: find Tasks with `query_connections({ from_node_id: task.id, type: "DependsOn" })` returning results)
- **Next Actions**: Incomplete Tasks where all immediate dependencies satisfied
- **Waiting For**: Incomplete Tasks where `responsibleParty` property exists and is not "me"

The system must:
1. **Recognize capture opportunities**: Identify when conversation mentions work to be done
2. **Query before responding**: Check memory via `query_nodes` before answering questions
3. **Maintain consistency**: Update related nodes when dependencies change or tasks complete
4. **Infer when appropriate**: Use judgment to fill in obvious details vs ask for clarification
5. **Handle duplicates intelligently**: Recognize semantically similar tasks (not just exact text matches)
6. **Warn before breaking relationships**: Alert user if deleting tasks with dependencies

All state persists in graph memory (via MCP server), not in conversation context. Each conversation starts stateless and rebuilds understanding through queries.

## Value Delivered

**Primary Value:**
- Natural language GTD interaction without learning specialized commands or syntax
- Validates the project's core assumption: Claude can reliably manage memory through conversation
- Enables immediate use of the GTD system for personal productivity

**Secondary Value:**
- De-risks the biggest project uncertainty (conversational reliability)
- Provides foundation for Phase 2 advanced features (ANY/ALL State management, pattern detection)
- Demonstrates feasibility of conversational memory management for future domains

**Success Metrics:**
- Users can capture, query, and update tasks without referring to documentation
- Memory remains consistent across conversations (no "forgetting" or conflicts)
- Duplicate detection prevents task proliferation
- 3-5 days of real usage reveals "solid" vs "rough" vs "broken" areas per ROADMAP Phase 1 checkpoint

## Interface Contract

### MCP Server: graph-memory-core

All graph operations use the `graph-memory-core` MCP server (Feature 2, Complete). The conversational layer composes these primitive tools to implement GTD workflows.

**Server Name:** `graph-memory-core`

**Ontology:** GTD Ontology (Feature 3, Complete) defines node types (Task, State, Context, UNSPECIFIED) and connection type (DependsOn)

**Key Tools Used:**

#### create_node
```typescript
Input: {
  type: string,              // "Task" | "State" | "Context" | "UNSPECIFIED"
  content: string,           // UTF-8 text description
  encoding: "utf-8",
  format: string,            // "markdown" typical
  properties?: {             // Type-specific properties
    // For Task:
    isComplete?: boolean,    // Required for Task (default false)
    responsibleParty?: string // Optional, "me" or external party name
    // For State:
    isTrue?: boolean,        // Required for State
    logic?: "MANUAL",        // Only MANUAL in Phase 1
    // For Context:
    isAvailable?: boolean    // Required for Context
  }
}
Returns: { node_id: string }
```

#### query_nodes
```typescript
Input: {
  type?: string,             // Filter by node type
  properties?: {             // Filter by properties (AND semantics)
    isComplete?: boolean,    // E.g., find incomplete Tasks
    responsibleParty?: string
  }
}
Returns: { node_ids: string[] }
```

#### get_node
```typescript
Input: { node_id: string }
Returns: {
  id: string,
  type: string,
  created: string,           // ISO 8601
  modified: string,          // ISO 8601
  properties: object,
  content_format: string
}
```

#### update_node
```typescript
Input: {
  id: string,
  properties?: object,       // Merge with existing (can't remove properties)
  content?: string,
  encoding?: "utf-8",
  format?: string
}
Returns: void
```

#### create_connection
```typescript
Input: {
  type: "DependsOn",
  from_node_id: string,      // Source (dependent)
  to_node_id: string,        // Target (dependency)
  properties?: object        // Optional connection metadata
}
Returns: { connection_id: string }
```

#### query_connections
```typescript
Input: {
  from_node_id?: string,     // Find connections from this node
  to_node_id?: string,       // Find connections to this node
  type?: "DependsOn",
  properties?: object
}
Returns: { connection_ids: string[] }
```

#### get_connected_nodes
```typescript
Input: {
  node_id: string,
  connection_type?: "DependsOn",
  direction: "out" | "in" | "both"  // Outgoing, incoming, or both
}
Returns: { node_ids: string[] }
```

#### delete_node
```typescript
Input: { node_id: string }
Returns: void
Postcondition: All connections involving this node are automatically deleted (cascade)
```

#### ensure_singleton_node
```typescript
Input: {
  type: "UNSPECIFIED",
  content?: string,
  encoding?: "utf-8",
  format?: string,
  properties?: object,
  on_multiple?: "oldest" | "newest"
}
Returns: { node_id: string, created: boolean }
Idempotency: Returns existing UNSPECIFIED singleton on subsequent calls
```

**Property Constraints:**
- Property values must be string, number, or boolean (no nested objects/arrays)
- String matching is case-sensitive and exact
- Query matching uses AND semantics (all specified properties must match)
- Cannot remove properties via update (workaround: delete and recreate node)

**Topology Rules** (enforced by graph-memory-core):
- DependsOn connections: Task→Task, Task→State, Task→Context, State→Task, State→State
- UNSPECIFIED can only be target (dependency), never source
- Context can only be target, never source

---

### System Prompt Structure

**Format:** Monolithic system prompt (single unified document, not modular)

**Inspiration:** Claude Skills format (example-heavy, concrete pattern demonstration)

**Content Sections:**

1. **Introduction** (2-3 paragraphs)
   - Role: GTD Task Management Assistant
   - Core capability: Manage tasks and projects using graph-based memory
   - Interaction style: Natural language, no explicit commands

2. **Planning Model Explanation** (standalone, not GTD-derived)
   - **Task**: Unit of work with completion tracking
     - Properties: `isComplete: boolean`, `responsibleParty?: string`
     - Content: Description, notes, context in markdown
   - **State**: World condition or precondition
     - Properties: `isTrue: boolean`, `logic: "MANUAL"`
     - MANUAL: User reports when condition is true/false (e.g., "weather is good")
     - Content: Description of condition
     - Note: ANY/ALL/IMMUTABLE deferred to Phase 2
   - **Context**: Location, tool, or situation
     - Properties: `isAvailable: boolean`
     - User reports when context becomes available/unavailable
     - Content: Description of context
   - **DependsOn Connection**: "from depends on to"
     - Direction: Task A DependsOn Task B means "A cannot be completed until B is complete"
     - Topology: Task→Task, Task→State, Task→Context, State→Task supported
   - **UNSPECIFIED Singleton**: Placeholder for incomplete decomposition
     - Tasks depending on UNSPECIFIED are blocked (never actionable)

3. **Derived Views** (GTD concepts as queries)
   - **Projects**: Tasks with outgoing DependsOn connections
     - Not a separate node type - it's a derived view
     - Query: Find Tasks where `query_connections({ from_node_id, type: "DependsOn" })` returns results
   - **Next Actions**: Incomplete Tasks where all immediate dependencies satisfied
     - Query: Find Tasks with `isComplete=false` AND all connected dependencies satisfied (Task.isComplete=true, State.isTrue=true, Context.isAvailable=true)
     - Exclude: Tasks depending on UNSPECIFIED
   - **Waiting For**: Tasks delegated to external parties
     - Query: Find Tasks with `isComplete=false` AND `responsibleParty` set AND `responsibleParty !== "me"`

4. **MCP Tools Available** (conceptual overview)
   - Brief explanation of create_node, query_nodes, get_node, update_node, create_connection, query_connections, get_connected_nodes, delete_node
   - Note: Detailed signatures provided via MCP tool configuration

5. **Conversation Patterns with Examples** (25-30 concrete examples)
   - Each example shows: User utterance → Claude reasoning → Tool calls → Response
   - Categories:
     - Capture (7 examples): Simple task, with context, with dependency, UNSPECIFIED, duplicate detection, project with subtasks, delegated task
     - Query (7 examples): Next actions, projects, waiting for, context-filtered, stuck projects, specific task lookup, weekly review
     - Update (5 examples): Mark complete, update details, add dependency, change context availability, report MANUAL state
     - Delete (2 examples): Delete with warning, cascade delete when confirmed
     - Edge cases (5 examples): Empty results, ambiguous reference, conflicting updates, undefined context, inference vs asking

6. **Inference Principles** (5 guidelines)
   - When to infer vs when to ask
   - Examples of obvious inferences (e.g., "call dentist" → likely needs phone context)
   - Examples requiring clarification (e.g., "work on project" → which specific task?)

7. **Weekly Review Format** (template for data presentation)
   - Completed this week: Last 7 days, sorted by modified desc, limit 20
   - Active projects: Projects (Tasks with outgoing deps) that are incomplete, show count of incomplete dependencies
   - Stuck projects: Projects with no recently completed dependencies (>14 days), sorted by oldest first
   - Next actions: First 20 actionable tasks, grouped by context if applicable
   - Waiting for: Delegated tasks, sorted by modified asc (oldest first)
   - Context availability: Current state of all Contexts

8. **Critical Reminders**
   - All state persists in graph memory (query before responding)
   - Recognize semantic similarity for duplicates (not exact text matching)
   - Warn before deleting tasks with dependencies (no auto-cascade)
   - MANUAL States: User reports conditions, don't auto-update
   - Projects are derived (don't create separate "Project" type nodes)
   - Parent completion is explicit (don't auto-complete when all deps satisfied)

**Preconditions:**
- graph-memory-core MCP server running and accessible
- GTD Ontology loaded (Task, State, Context, UNSPECIFIED types; DependsOn connection type)
- UNSPECIFIED singleton created
- Claude Code invoked with MCP server configuration

**Postconditions:**
- Claude understands Task/State/DependsOn model
- Claude recognizes when to call MCP tools
- Claude follows inference principles appropriately
- Claude maintains consistency across conversations

---

### Query Pattern Specifications

These define precise, testable query semantics used by the conversational layer.

#### Projects Query

**Definition:** Tasks with outgoing DependsOn connections

**Algorithm:**
```typescript
// Step 1: Get all Tasks
const allTasks = await query_nodes({ type: "Task" })

// Step 2: For each Task, check for outgoing DependsOn connections
const projects = []
for (const taskId of allTasks.node_ids) {
  const outgoingDeps = await query_connections({
    from_node_id: taskId,
    type: "DependsOn"
  })

  if (outgoingDeps.connection_ids.length > 0) {
    projects.push(taskId)
  }
}

return projects
```

**Returns:** Array of Task node IDs representing Projects

**Note:** Projects are NOT stored - this is a derived view computed on demand

**Example:**
- Task "Launch website" with DependsOn connections to "Design homepage", "Write content", "Deploy" → IS a Project
- Task "Buy birthday card" with no DependsOn connections → NOT a Project

---

#### Next Actions Query

**Definition:** Incomplete Tasks where all immediate dependencies are satisfied

**Algorithm:**
```typescript
// Step 1: Get all incomplete Tasks
const incompleteTasks = await query_nodes({
  type: "Task",
  properties: { isComplete: false }
})

// Step 2: Filter to Tasks with satisfied dependencies
const nextActions = []

for (const taskId of incompleteTasks.node_ids) {
  // Get immediate dependencies (outgoing DependsOn connections)
  const depNodeIds = await get_connected_nodes({
    node_id: taskId,
    connection_type: "DependsOn",
    direction: "out"
  })

  // Check if all dependencies satisfied
  let allSatisfied = true
  for (const depId of depNodeIds.node_ids) {
    const depNode = await get_node({ node_id: depId })

    if (depNode.type === "Task") {
      if (!depNode.properties.isComplete) {
        allSatisfied = false
        break
      }
    } else if (depNode.type === "State") {
      if (!depNode.properties.isTrue) {
        allSatisfied = false
        break
      }
    } else if (depNode.type === "Context") {
      if (!depNode.properties.isAvailable) {
        allSatisfied = false
        break
      }
    } else if (depNode.type === "UNSPECIFIED") {
      // UNSPECIFIED always blocks
      allSatisfied = false
      break
    }
  }

  if (allSatisfied) {
    nextActions.push(taskId)
  }
}

return nextActions
```

**Returns:** Array of Task node IDs representing Next Actions (actionable tasks)

**Note:**
- Only checks immediate dependencies (no recursion)
- UNSPECIFIED always blocks (tasks depending on UNSPECIFIED never actionable)
- Empty dependencies array means task is actionable (no blockers)

**Example:**
- Task "Write report" (isComplete=false, no dependencies) → IS Next Action
- Task "Review report" (isComplete=false, depends on incomplete "Write report") → NOT Next Action
- Task "Define requirements" (isComplete=false, depends on UNSPECIFIED) → NOT Next Action

---

#### Waiting For Query

**Definition:** Incomplete Tasks delegated to external parties

**Algorithm:**
```typescript
// Get all incomplete Tasks with external responsibility
const incompleteTasks = await query_nodes({
  type: "Task",
  properties: { isComplete: false }
})

const waitingFor = []

for (const taskId of incompleteTasks.node_ids) {
  const task = await get_node({ node_id: taskId })

  // Check if responsibleParty exists and is not "me"
  if (task.properties.responsibleParty &&
      task.properties.responsibleParty !== "me") {
    waitingFor.push(taskId)
  }
}

return waitingFor
```

**Returns:** Array of Task node IDs representing Waiting For tasks

**Note:**
- "me" is special value indicating current user
- All other values indicate external party (e.g., "Jane", "Finance team", "City council")
- Tasks without `responsibleParty` assumed to be user's responsibility

**Example:**
- Task "Waiting for logo designs" (isComplete=false, responsibleParty="Jane") → IS Waiting For
- Task "Write documentation" (isComplete=false, responsibleParty="me") → NOT Waiting For
- Task "Review code" (isComplete=false, no responsibleParty) → NOT Waiting For

---

#### Stuck Projects Query

**Definition:** Projects with no recent activity (>14 days since last dependency completion)

**Algorithm:**
```typescript
// Step 1: Get all Projects (Tasks with outgoing dependencies)
const projects = await getProjects() // Use Projects query above

// Step 2: Filter to incomplete Projects
const incompleteProjects = []
for (const projId of projects) {
  const proj = await get_node({ node_id: projId })
  if (!proj.properties.isComplete) {
    incompleteProjects.push(projId)
  }
}

// Step 3: Check last activity for each Project
const stuck = []
const now = Date.now()
const TWO_WEEKS_MS = 14 * 24 * 60 * 60 * 1000

for (const projId of incompleteProjects) {
  // Get all dependencies (Tasks this Project depends on)
  const depNodeIds = await get_connected_nodes({
    node_id: projId,
    connection_type: "DependsOn",
    direction: "out"
  })

  // Find most recent completion timestamp among dependencies
  let mostRecentCompletion = null

  for (const depId of depNodeIds.node_ids) {
    const depNode = await get_node({ node_id: depId })

    if (depNode.type === "Task" && depNode.properties.isComplete) {
      const modifiedTime = new Date(depNode.modified).getTime()
      if (!mostRecentCompletion || modifiedTime > mostRecentCompletion) {
        mostRecentCompletion = modifiedTime
      }
    }
  }

  // Check if stuck (no completions or last completion >14 days ago)
  if (!mostRecentCompletion || (now - mostRecentCompletion) > TWO_WEEKS_MS) {
    stuck.push(projId)
  }
}

return stuck
```

**Returns:** Array of Project Task node IDs with no recent activity

**Criteria for "stuck":**
- Project is incomplete (isComplete=false)
- No dependencies completed in last 14 days (checked via `modified` timestamp)
- If no dependencies ever completed, Project considered stuck

**Example:**
- Project "Redesign landing page" with 5 subtasks, last completed subtask 21 days ago → IS Stuck
- Project "Refactor auth" with 3 subtasks, completed subtask 3 days ago → NOT Stuck

## Acceptance Criteria

### Category: Capture

**AC1: Simple Task Capture**
- When user mentions work to be done ("I need to X"), Claude creates Task node with `isComplete=false`
- `create_node` called with type="Task", properties={isComplete: false}
- Task content includes user's description
- User receives confirmation with task details

**AC2: Dependent Task Capture**
- When user describes dependency ("X depends on Y"), Claude creates both Tasks and DependsOn connection
- Both Tasks created with isComplete=false
- `create_connection` called with correct direction: X→Y (X depends on Y)
- User can query Projects and see X listed (has outgoing dependency)

**AC3: Context Association**
- When user mentions location/tool ("at office" or "needs laptop"), Claude creates or links Context
- Context node created with `isAvailable` inferred from context (or asked)
- DependsOn connection created from Task to Context
- Next Actions query respects Context.isAvailable

**AC4: Project with Subtasks Capture**
- When user describes multi-step work, Claude creates parent Task and child Tasks
- Parent Task has outgoing DependsOn connections to each child (parent depends on children)
- Projects query returns parent Task (has outgoing dependencies)
- Next Actions initially returns only children with no dependencies

**AC5: UNSPECIFIED Handling**
- When user mentions vague task without clear decomposition, Claude encourages defining next action
- If user defers, Claude can create Task with DependsOn to UNSPECIFIED singleton
- Task depending on UNSPECIFIED is never returned by Next Actions query
- User can later remove UNSPECIFIED dependency and add concrete dependencies

**AC6: Duplicate Prevention**
- When user mentions task similar to existing task, Claude queries for potential duplicates
- Similarity is intelligent (frontier model judgment), not exact text match
- Claude asks "Is this the same as [existing task]?" before creating duplicate
- User confirms same/different; no duplicate created without confirmation

**AC7: Inference on Capture**
- Claude infers obvious details without asking (e.g., "call dentist" → Context=phone)
- Claude asks when intent ambiguous (e.g., "work on project" → which task?)
- Inference follows principles: infer type/context for common patterns, ask for ambiguous specifics
- User not overwhelmed with unnecessary questions

**AC8: Delegated Task Capture**
- When user delegates task ("Jane is handling X"), Claude creates Task with `responsibleParty="Jane"`
- Task excluded from Next Actions query (responsibleParty not "me")
- Task included in Waiting For query (responsibleParty set and not "me")
- User receives confirmation of delegation

### Category: Dependencies

**AC9: Dependency Creation**
- When user states dependency, Claude creates DependsOn connection with correct direction
- `create_connection` called with from_node_id=dependent, to_node_id=dependency
- Both nodes verified to exist before creating connection
- Dependency immediately affects Next Actions query (blocks dependent task)

**AC10: Dependency Updates**
- When user removes dependency ("X no longer depends on Y"), Claude deletes DependsOn connection
- Connection deleted via appropriate tool (delete_connection not specified in contract - may require node recreation)
- Next Actions query reflects updated dependencies immediately
- No orphaned connections remain

**AC11: Dependency Direction Correctness**
- "Task A depends on Task B" creates A→B connection (A is from, B is to)
- "Do A before B" creates B→A connection (B depends on A being done first)
- Direction affects query results correctly (Projects vs Next Actions)
- User confirmation if direction is ambiguous

### Category: Context

**AC12: Context Availability Updates**
- When user indicates location/tool change ("I'm at office now"), Claude updates Context.isAvailable=true
- `update_node` called with properties={isAvailable: true}
- Next Actions query immediately reflects change (tasks requiring office now actionable)
- Multiple Contexts can be available simultaneously

**AC13: Context-Filtered Queries**
- Next Actions query respects Context.isAvailable for tasks depending on Contexts
- Tasks requiring unavailable Context excluded from Next Actions
- Tasks requiring only available Contexts (or no Contexts) included in Next Actions
- Empty result when no Contexts available returns helpful message

**AC14: Context Creation**
- When user mentions new location/tool, Claude creates Context node
- Properties: isAvailable inferred from user statement or asked
- Content: Description of context
- Can be created standalone or during Task capture

### Category: Queries

**AC15: Projects Query**
- Returns all Tasks with outgoing DependsOn connections (incomplete or complete)
- Uses query pattern: check `query_connections({ from_node_id, type: "DependsOn" })`
- Tasks without outgoing dependencies not included
- Correctly identifies Projects even if all dependencies satisfied

**AC16: Next Actions Query**
- Returns Tasks where isComplete=false AND all immediate dependencies satisfied
- Checks Task dependencies: Task.isComplete, State.isTrue, Context.isAvailable
- Excludes tasks depending on UNSPECIFIED
- Excludes tasks with external responsibleParty

**AC17: Waiting For Query**
- Returns Tasks where isComplete=false AND responsibleParty set AND responsibleParty !== "me"
- Uses query pattern: filter Tasks by property check
- Tasks with responsibleParty="me" excluded
- Tasks without responsibleParty excluded

**AC18: Stuck Projects Query**
- Returns Projects (Tasks with outgoing deps) where no dependencies completed in >14 days
- Uses modified timestamp on dependency Tasks to determine last activity
- Incomplete Projects with no completed dependencies ever are considered stuck
- Sorted by oldest activity first

**AC19: Specific Task Lookup**
- When user references specific task, Claude queries by content/properties similarity
- Returns Task details: content, isComplete, responsibleParty, dependencies, contexts
- Handles ambiguity if multiple matches found (asks user to clarify)
- Graceful handling if no matches found

**AC20: Query Before Responding**
- When user asks question requiring memory, Claude calls query_nodes before responding
- Doesn't hallucinate or guess task existence
- Returns empty results gracefully ("No next actions found")
- Offers to help create tasks if appropriate

### Category: Updates

**AC21: Task Completion**
- When user indicates completion ("I finished X"), Claude updates Task.isComplete=true
- `update_node` called with properties={isComplete: true}
- Task immediately excluded from Next Actions query
- Task immediately excluded from Projects query if it was a Project with all deps complete
- Dependent tasks (Tasks depending on this Task) may become actionable (Next Actions query reflects change)

**AC22: Task Detail Updates**
- When user updates task info ("Change title" or "Add note"), Claude calls update_node
- Only specified properties/content updated (no unintended side effects)
- Updated task details reflected in subsequent queries
- User receives confirmation of update

**AC23: Task Deletion**
- When user requests deletion ("Remove task X"), Claude checks for dependent tasks
- Queries incoming DependsOn connections (tasks that depend on this task)
- If dependents exist: Warns user with list, asks for confirmation
- If confirmed or no dependents: Deletes via delete_node (auto-cascades connections)
- Does NOT cascade delete dependents unless explicitly requested

**AC24: MANUAL State Updates**
- When user reports world condition ("Weather is good"), Claude updates State.isTrue
- Only for States with logic="MANUAL"
- `update_node` called with properties={isTrue: true/false}
- Tasks depending on State immediately affected (Next Actions query reflects change)
- State changes persist across conversations

### Category: Duplicates

**AC25: Intelligent Duplicate Detection**
- Duplicate detection uses semantic similarity (frontier model judgment), not exact match
- "Call dentist" and "Schedule dentist appointment" recognized as similar
- "Write report" and "Review report" recognized as different
- User makes final decision if Claude presents duplicate candidate

### Category: Persistence

**AC26: Cross-Conversation Persistence**
- All Tasks, States, Contexts, Connections persist in graph memory (via MCP)
- New conversation can query all previously created nodes
- No conversation-specific state required (all state in graph)
- Behavior consistent across conversation boundaries

**AC27: State Isolation**
- Each conversation starts stateless (queries graph to rebuild understanding)
- No hidden state in conversation context that affects behavior
- Behavior deterministic based on graph state + user input
- Claude queries graph explicitly before responding to memory-dependent questions

### Category: Delete

**AC28: Dependency Warning on Delete**
- Before deleting Task with dependent tasks, Claude warns: "Tasks [X, Y] depend on this. Delete anyway?"
- Lists all dependent Tasks explicitly (via query_connections with to_node_id)
- Waits for user confirmation before proceeding
- If user cancels, no deletion occurs

**AC29: No Automatic Cascade**
- Deleting Task does NOT automatically delete dependent tasks
- Only the specified Task deleted (connections auto-deleted by graph-memory-core)
- Dependents remain with unsatisfied dependencies (DependsOn to non-existent node)
- Note: graph-memory-core auto-deletes connections when nodes deleted, but not dependent nodes

**AC30: Cascade Delete When Requested**
- When user explicitly requests cascade ("Delete X and everything that depends on it"), Claude recursively deletes dependents
- Confirmation shows full list of Tasks to be deleted
- User must confirm before cascade executes
- All specified Tasks deleted in appropriate order (children before parents)

**AC31: Delete Confirmation**
- After successful delete, Claude confirms: "Deleted task [X]" (or "Deleted [X] and N dependent tasks")
- Subsequent queries immediately reflect deletion
- No orphaned references in responses

### Category: Edge Cases

**AC32: Empty Query Results**
- When query returns empty, Claude returns helpful message: "No next actions available"
- Suggests possible reasons (e.g., "All tasks have unsatisfied dependencies")
- Offers to help create tasks if appropriate
- No errors thrown for empty results

**AC33: Ambiguous Task References**
- When user refers to task ambiguously ("Update the report"), Claude queries for matches
- If multiple matches: Lists options, asks user to specify
- If no matches: "I don't see a task matching 'the report'. Did you mean...?" or offers to create
- No assumptions about user's intended task

**AC34: Invalid Delete Requests**
- When user tries to delete non-existent task, Claude responds gracefully: "I don't see a task matching X"
- Offers to search or list tasks
- No error thrown for invalid delete request

**AC35: Conflicting Updates**
- When user requests conflicting changes ("Mark X complete and add subtask Y"), Claude asks for clarification
- Processes unambiguous parts, asks about conflicts
- Doesn't make assumptions about resolution
- User clarifies intent before proceeding

**AC36: Context Not Yet Defined**
- When user mentions location/tool not in graph ("I'm at the park"), Claude offers to create Context
- "I don't have 'park' as a context. Create it?" with isAvailable=true
- Doesn't assume Context exists without confirmation
- User confirms creation

### Category: Inference Principles

**AC37: Infer Obvious Details**
- For tasks with clear context implications ("call dentist" → phone), Claude infers without asking
- Uses domain knowledge appropriately
- Doesn't overwhelm user with questions about obvious details
- User can always override inferences

**AC38: Ask When Ambiguous**
- For ambiguous intent ("work on project"), Claude asks: "Which task specifically?"
- Doesn't guess at user's intended task
- Provides options if multiple matches exist
- Waits for user clarification before proceeding

**AC39: Infer Completion**
- When user clearly indicates completion ("I finished X"), Claude infers isComplete should be true
- Doesn't require explicit "mark complete" command
- Handles natural language variations
- User receives confirmation of completion

**AC40: Ask for Dependency Clarification**
- When dependency direction unclear, Claude asks: "Does X depend on Y, or Y depend on X?"
- If clear from context, infers without asking
- Balances inference with accuracy
- User confirms if Claude uncertain

**AC41: Infer Project Structure**
- When user describes task with subtasks ("Build feature X: design, implement, test"), Claude creates parent and children
- Parent has outgoing DependsOn connections to children (derived as Project)
- Doesn't require explicit "this is a project" statement
- Uses natural language understanding to identify structure

### Category: Testing Infrastructure

**AC42: Eval Framework Exists**
- Python script accepts test case JSON, invokes `claude --print <prompt>`, captures output
- Judging Claude evaluates output against behavioral criteria (not exact text)
- Returns pass/fail with justification
- Script is single file, <300 lines, no external dependencies beyond subprocess

**AC43: Test Cases Cover Critical Scenarios**
- Minimum 24 test cases across 5 categories: Capture (8), Query (6), Update (4), Delete (2), Edge Cases (4)
- Each test case includes: prompt, expected behavior (behavioral, not exact text), pass criteria
- Test cases use conceptual scenarios (specific enough to test but not brittle exact prompts)
- Test suite runnable via simple command (e.g., `python test_conversational_layer.py`)

**AC44: TDD Workflow Supported**
- Test can be written before prompt is finalized (Red step)
- Prompt refinement makes test pass (Green step)
- Test validates behavior, not exact wording (Refactor step possible)
- Test failures provide actionable feedback for prompt improvement

**AC45: Single Judge Model**
- Judging uses one model (same as conversational Claude for MVP)
- Pass criteria are behavioral: "Creates Task with isComplete=false", not "Responds with exact text X"
- Judge output includes reasoning for pass/fail
- Judge runs automatically on each test case

### Category: Parent Completion

**AC46: No Automatic Parent Completion**
- When all dependencies of a Project Task complete, parent is NOT automatically marked complete
- Claude MAY notify user: "All subtasks of [Project] complete. Mark project complete?"
- User explicitly updates Task.isComplete=true (or confirms notification)
- Parent completion is deliberate user action, not automatic inference

## Scenarios

### Scenario 1: Simple Task Capture and Next Actions Query

**Given:**
- Empty graph (no Tasks or Contexts exist)
- User starts new conversation with Claude Code

**When:**
- User: "I need to call the dentist tomorrow to schedule a cleaning"
- Claude calls: `create_node({ type: "Task", content: "Call the dentist to schedule a cleaning", encoding: "utf-8", format: "markdown", properties: { isComplete: false } })`
- Returns: `{ node_id: "task_001" }`
- Claude responds: "I've captured that task: 'Call the dentist to schedule a cleaning'. I've marked it as a next action."

**Then:**
- Task exists with id="task_001", type="Task", properties.isComplete=false
- User: "What should I work on next?"
- Claude calls: `query_nodes({ type: "Task", properties: { isComplete: false } })`
- Returns: `{ node_ids: ["task_001"] }`
- Claude calls: `get_connected_nodes({ node_id: "task_001", connection_type: "DependsOn", direction: "out" })`
- Returns: `{ node_ids: [] }` (no dependencies)
- Next Actions includes "task_001"
- Claude responds: "You have one next action: Call the dentist to schedule a cleaning."

---

### Scenario 2: Dependent Tasks with Context Filtering

**Given:**
- Conversation in progress
- Context "@office" exists with id="ctx_001", isAvailable=true
- Context "@home" exists with id="ctx_002", isAvailable=false

**When:**
- User: "I need to write the Q4 report, but first I need to gather data from finance. Both need to be done at the office."
- Claude creates Task "Gather data from finance" (task_101) with isComplete=false
- Claude creates Task "Write Q4 report" (task_102) with isComplete=false
- Claude creates DependsOn: task_102→task_101 (Write depends on Gather)
- Claude creates DependsOn: task_101→ctx_001 (@office)
- Claude creates DependsOn: task_102→ctx_001 (@office)

**Then:**
- task_102 has outgoing dependency → IS a Project (per Projects query)
- User: "What can I work on right now?"
- Projects query: Returns task_102 (has outgoing DependsOn)
- Next Actions query:
  - task_101: isComplete=false, depends on ctx_001 (isAvailable=true) → INCLUDED
  - task_102: isComplete=false, depends on task_101 (isComplete=false) → EXCLUDED (unsatisfied dependency)
- Claude responds: "You have one next action available at the office: Gather data from finance. (Write Q4 report is blocked until you gather the data first.)"

---

### Scenario 3: Duplicate Detection

**Given:**
- Task "Schedule dentist appointment" exists (task_201) with content="Call to book cleaning"
- User in new conversation (doesn't remember existing task)

**When:**
- User: "I need to call the dentist to set up an appointment"
- Claude queries: `query_nodes({ type: "Task" })`
- Claude uses semantic similarity (content search or LLM judgment) to find task_201
- Claude reads: `get_node({ node_id: "task_201" })` → "Schedule dentist appointment: Call to book cleaning"
- Claude recognizes similarity between user's intent and existing task

**Then:**
- Claude responds: "You already have a task 'Schedule dentist appointment: Call to book cleaning'. Is this the same task or a new one?"
- User: "Oh right, same task. Thanks for catching that."
- No new task created
- Claude: "Got it. That task is still in your next actions."
- OR User: "No, this is a different appointment for my spouse."
- Claude creates new task: "Call the dentist to set up appointment [for spouse]"

---

### Scenario 4: Task Completion and Dependency Unblocking

**Given:**
- Project "Launch website" (task_301, isComplete=false) exists
- Subtask "Design homepage" (task_302, isComplete=false)
- Subtask "Write content" (task_303, isComplete=false)
- Subtask "Deploy" (task_304, isComplete=false)
- Dependencies: task_301→task_302, task_301→task_303, task_301→task_304 (Project depends on all subtasks)

**When:**
- User: "I finished designing the homepage"
- Claude queries for "Design homepage": finds task_302
- Claude calls: `update_node({ id: "task_302", properties: { isComplete: true } })`
- Claude responds: "Marked 'Design homepage' as complete. Great work!"
- User: "I also wrote all the content"
- Claude finds task_303, updates: `update_node({ id: "task_303", properties: { isComplete: true } })`
- User: "What should I work on next?"
- Next Actions query:
  - task_302: isComplete=true → EXCLUDED (complete)
  - task_303: isComplete=true → EXCLUDED (complete)
  - task_304: isComplete=false, no dependencies → INCLUDED
  - task_301: isComplete=false, depends on task_302 (complete), task_303 (complete), task_304 (incomplete) → EXCLUDED (unsatisfied dependency)

**Then:**
- Claude responds: "Next action: Deploy. (This is the last step for 'Launch website')"
- task_301 ("Launch website") still incomplete (not auto-completed even though 2/3 subtasks done)
- User must explicitly complete task_301 after deploying (or Claude can prompt: "All subtasks complete, mark project done?")

---

### Scenario 5: Delete with Dependency Warning

**Given:**
- Task "Gather data" (task_401, isComplete=true)
- Task "Write report" (task_402, isComplete=false)
- DependsOn: task_402→task_401 (Write depends on Gather)

**When:**
- User: "Delete the 'Gather data' task"
- Claude queries: `query_connections({ to_node_id: "task_401", type: "DependsOn" })`
- Returns: `{ connection_ids: ["conn_001"] }` (connection from task_402)
- Claude gets dependent: finds task_402 "Write report"

**Then:**
- Claude responds: "Task 'Write report' depends on 'Gather data'. Deleting 'Gather data' will leave 'Write report' with an unsatisfied dependency. Delete anyway?"
- User: "Yes, delete it"
- Claude calls: `delete_node({ node_id: "task_401" })`
- Connection conn_001 automatically deleted by graph-memory-core (cascade delete connections)
- task_402 remains with broken dependency (DependsOn to non-existent node)
- Claude: "Deleted 'Gather data'. Note: 'Write report' now has a missing dependency."
- OR User: "No, keep it"
- Claude: "Okay, keeping 'Gather data'."
- No deletion occurs

---

### Scenario 6: Context Availability Change

**Given:**
- Task "Review code" (task_501, isComplete=false)
- Context "@laptop" (ctx_101, isAvailable=false)
- DependsOn: task_501→ctx_101
- Task "Call client" (task_502, isComplete=false)
- Context "@phone" (ctx_102, isAvailable=true)
- DependsOn: task_502→ctx_102
- Task "Plan meeting" (task_503, isComplete=false, no dependencies)

**When:**
- User: "What can I work on right now?"
- Next Actions query:
  - task_501: depends on ctx_101 (isAvailable=false) → EXCLUDED
  - task_502: depends on ctx_102 (isAvailable=true) → INCLUDED
  - task_503: no dependencies → INCLUDED
- Claude responds: "You can work on: 1) Call client (requires phone), 2) Plan meeting. ('Review code' requires laptop which is not available.)"

**Then:**
- User: "I just opened my laptop"
- Claude queries: `query_nodes({ type: "Context" })` or remembers ctx_101
- Claude calls: `update_node({ id: "ctx_101", properties: { isAvailable: true } })`
- Claude: "Updated @laptop to available."
- User: "What can I work on now?"
- Next Actions query now includes task_501 (ctx_101 now available)
- Claude: "You can work on: 1) Review code (laptop now available), 2) Call client, 3) Plan meeting."

---

### Scenario 7: Weekly Review with Stuck Projects

**Given:**
- Current date: 2025-11-15
- Project "Redesign landing page" (task_601, isComplete=false)
  - Last dependency completed: 2025-10-25 (21 days ago, modified timestamp on task_602)
- Project "Refactor auth module" (task_701, isComplete=false)
  - Last dependency completed: 2025-11-12 (3 days ago, modified timestamp on task_702)
- 3 Tasks completed this week (task_801, task_802, task_803 with modified in last 7 days)
- 5 incomplete Tasks with no dependencies (Next Actions)

**When:**
- User: "Show me my weekly review"
- Claude queries:
  - Completed this week: `query_nodes({ type: "Task", properties: { isComplete: true } })`, filter by modified in last 7 days
  - Projects: Tasks with outgoing DependsOn connections
  - Stuck projects: Projects with no dependencies modified >14 days
  - Next actions: Per Next Actions query
  - Contexts: `query_nodes({ type: "Context" })`

**Then:**
- Claude responds:
  ```
  Weekly Review (week of Nov 8-15, 2025)

  Completed this week:
  - [task_801 title]
  - [task_802 title]
  - [task_803 title]

  Active projects (2):
  - Refactor auth module (last activity 3 days ago, 2 incomplete subtasks)
  - Redesign landing page (last activity 21 days ago, 4 incomplete subtasks) ⚠️ STUCK

  Stuck projects needing attention:
  - Redesign landing page (no activity in 21 days)

  Next actions available (5):
  - [task details...]

  Waiting for (0):
  - (No tasks waiting on external parties)

  Contexts:
  - @office: Available
  - @laptop: Available
  - @home: Not available
  ```

---

### Scenario 8: Delegated Task (Waiting For)

**Given:**
- Graph has some existing tasks

**When:**
- User: "Jane is handling the logo designs. I'm waiting on her."
- Claude creates Task "Logo designs" (task_901, isComplete=false, responsibleParty="Jane")
- `create_node({ type: "Task", content: "Logo designs - waiting on Jane", encoding: "utf-8", format: "markdown", properties: { isComplete: false, responsibleParty: "Jane" } })`

**Then:**
- Claude responds: "I've captured 'Logo designs' as delegated to Jane. This will show up in your 'Waiting For' list."
- User: "What should I work on next?"
- Next Actions query: Excludes task_901 (responsibleParty="Jane", not "me")
- Waiting For query: Includes task_901 (responsibleParty set and not "me")
- Claude: "Next actions: [other tasks]. You're waiting on: Logo designs (Jane)."
- Later, user: "Jane finished the logos"
- Claude: `update_node({ id: "task_901", properties: { isComplete: true } })`
- task_901 excluded from Waiting For (isComplete=true)

## Data Structures

This feature uses data structures defined in the GTD Ontology (Feature 3). All structures are nodes/connections in graph-memory-core.

### Task Node

**Type:** Graph node (type="Task")

**Properties:**
```typescript
{
  isComplete: boolean,       // Required, default false when creating
  responsibleParty?: string, // Optional, "me" or external party name
  created: string,           // Automatic (ISO 8601)
  modified: string           // Automatic (ISO 8601)
}
```

**Content:** Markdown description of task, notes, context

**Invariants:**
- isComplete is boolean (true/false)
- responsibleParty "me" indicates current user; other values indicate external party
- If responsibleParty missing, assumed to be user's responsibility

**Example:**
```typescript
{
  id: "task_001",
  type: "Task",
  properties: {
    isComplete: false,
    responsibleParty: "me",
    created: "2025-11-02T10:00:00Z",
    modified: "2025-11-02T10:00:00Z"
  },
  content_format: "markdown"
}
// Content (in _content/nodes/task_001.txt):
"Call the dentist to schedule cleaning appointment"
```

---

### State Node (MANUAL only in Phase 1)

**Type:** Graph node (type="State")

**Properties:**
```typescript
{
  isTrue: boolean,           // Required, current truth value
  logic: "MANUAL",           // Only MANUAL supported in Phase 1
  created: string,           // Automatic (ISO 8601)
  modified: string           // Automatic (ISO 8601)
}
```

**Content:** Markdown description of world condition

**Invariants:**
- isTrue is boolean
- logic is "MANUAL" in Phase 1 (ANY/ALL/IMMUTABLE deferred to Phase 2)
- MANUAL States: User reports when condition becomes true/false (not auto-computed)

**Example:**
```typescript
{
  id: "state_001",
  type: "State",
  properties: {
    isTrue: false,
    logic: "MANUAL",
    created: "2025-11-02T10:00:00Z",
    modified: "2025-11-02T10:00:00Z"
  },
  content_format: "markdown"
}
// Content:
"Weather is suitable for outdoor painting (no rain, temp above 50°F)"
```

---

### Context Node

**Type:** Graph node (type="Context")

**Properties:**
```typescript
{
  isAvailable: boolean,      // Required, current availability
  created: string,           // Automatic (ISO 8601)
  modified: string           // Automatic (ISO 8601)
}
```

**Content:** Markdown description of location/tool/situation

**Invariants:**
- isAvailable is boolean
- Set by user/AI based on user reports ("I'm at the office" → isAvailable=true)

**Example:**
```typescript
{
  id: "ctx_001",
  type: "Context",
  properties: {
    isAvailable: true,
    created: "2025-11-02T10:00:00Z",
    modified: "2025-11-02T10:00:00Z"
  },
  content_format: "markdown"
}
// Content:
"@office - At the office location with access to desktop computer and meeting rooms"
```

**Common Contexts:**
- @home, @office, @errands, @computer, @phone, @laptop, @internet

---

### UNSPECIFIED Singleton

**Type:** Singleton node (type="UNSPECIFIED")

**Properties:**
```typescript
{
  created: string,           // Automatic
  modified: string           // Automatic
}
```

**Content:** Fixed description

**Semantics:**
- Special singleton type (only one instance exists)
- Can be dependency target (Task/State → UNSPECIFIED)
- Cannot have outgoing dependencies
- Always blocks actionability (Next Actions never returns tasks depending on UNSPECIFIED)
- Created once via `ensure_singleton_node` during GTD Ontology initialization

**Access:**
```typescript
// Query for UNSPECIFIED singleton
const result = await query_nodes({ type: "UNSPECIFIED" })
const unspecifiedId = result.node_ids[0] // Always exactly one
```

---

### DependsOn Connection

**Type:** Graph connection (type="DependsOn")

**Structure:**
```typescript
{
  id: string,                // Connection ID
  type: "DependsOn",
  from_node_id: string,      // Dependent node
  to_node_id: string,        // Dependency node
  properties?: object,       // Optional metadata
  created: string,           // Automatic
  modified: string           // Automatic
}
```

**Semantics:**
- Direction: "from depends on to" (from cannot be completed until to is complete/satisfied)
- Topology (Phase 1): Task→Task, Task→State, Task→Context, State→Task

**Invariants:**
- from and to nodes must exist
- Topology rules enforced by graph-memory-core
- Auto-deleted when either node is deleted (cascade)

**Example:**
```typescript
{
  id: "conn_001",
  type: "DependsOn",
  from_node_id: "task_002",  // "Write report"
  to_node_id: "task_001",    // "Gather data"
  created: "2025-11-02T10:05:00Z",
  modified: "2025-11-02T10:05:00Z"
}
// Meaning: "Write report" depends on "Gather data"
```

---

### Derived View: Projects

**Type:** Query result (not stored)

**Definition:** Tasks with outgoing DependsOn connections

**Query:** See "Query Pattern Specifications" section for algorithm

**Returns:** Array of Task node IDs

**Note:** Projects are NOT a separate node type - no Task.properties.type field exists

---

### Derived View: Next Actions

**Type:** Query result (not stored)

**Definition:** Incomplete Tasks with all immediate dependencies satisfied

**Query:** See "Query Pattern Specifications" section for algorithm

**Returns:** Array of Task node IDs

---

### Derived View: Waiting For

**Type:** Query result (not stored)

**Definition:** Incomplete Tasks with external responsibleParty

**Query:** See "Query Pattern Specifications" section for algorithm

**Returns:** Array of Task node IDs

## Dependencies

### External Dependencies

- **Python 3.9+**: For eval framework test runner script
- **Claude Code CLI**: Required for `--print` mode in non-interactive evaluations
- **Frontier Model (Claude Sonnet 4+)**: Required for:
  - Complex instruction following (multi-step tool calling)
  - Intelligent duplicate detection (semantic similarity judgment)
  - Inference judgment (when to infer vs ask)
  - Reliable tool calling (MCP integration with graph-memory-core)
  - Note: Smaller models likely insufficient for conversational memory management

### Internal Dependencies

- **File Storage Backend (Feature 1)**: Complete ✅
  - Provides persistent storage for graph memory

- **Graph Memory Core (Feature 2)**: Complete ✅
  - Provides MCP server: graph-memory-core
  - Tools: create_node, get_node, query_nodes, update_node, create_connection, query_connections, get_connected_nodes, delete_node, ensure_singleton_node
  - Version: 1.2 (specs/done/graph-memory-core.md)

- **GTD Ontology (Feature 3)**: Complete ✅
  - Defines node types: Task (isComplete, responsibleParty), State (isTrue, logic), Context (isAvailable), UNSPECIFIED
  - Defines connection type: DependsOn
  - Defines query patterns for Projects, Next Actions, Waiting For
  - Version: 1.3 (specs/done/gtd-ontology.md)
  - Implementation: src/gtd-ontology/ (types.ts defines property interfaces)

- **MCP Server Running**: Required
  - graph-memory-core MCP server must be running
  - Claude Code configured to connect to server
  - GTD Ontology initialized (ontology loaded, UNSPECIFIED singleton created)

### Assumptions

- **Single user**: MVP assumes one user (no multi-user concurrency or permissions)
- **Trusted input**: No adversarial input handling required
- **Development environment**: Designed for personal productivity use, not production deployment
- **UTF-8 text**: All text input/output assumes UTF-8 encoding
- **Reasonable scale**: Designed for 50-100 projects, 200-500 tasks (MVP scale per ROADMAP)
  - Query performance acceptable at this scale (linear scans OK)
- **Manual invocation**: User invokes Claude Code explicitly (no background processes)
- **Standard terminal**: Claude Code runs in bash/zsh/similar terminal
- **Conversation continuity**: User manages conversation boundaries (knows when starting new vs continuing)

## Constraints and Limitations

### Technical Constraints

- **Frontier model required**: Claude Sonnet 4+ necessary for reliable conversational memory management
  - Smaller models likely fail at duplicate detection, complex tool calling, or inference judgment
- **MCP round-trip latency**: Each graph operation requires MCP round-trip (typically <100ms)
  - Multi-step operations (create project with 5 subtasks) may take 500ms-1s total
- **Memory scale**: MVP targets 50-100 projects, 200-500 tasks
  - Performance beyond 1000 tasks not optimized
  - Query patterns use linear scans (O(n) to O(n*m))
- **Context window**: Long conversations may exceed context window
  - Requires new conversation start (graph state persists, conversation history lost)
- **Property immutability**: Cannot remove properties via update_node
  - Workaround: Delete and recreate node, or use sentinel values

### Architectural Constraints

- **Stateless conversations**: Each conversation starts fresh, rebuilds understanding via queries
  - Cannot rely on conversation context for state
  - All persistent state must be in graph memory
- **No real-time updates**: Graph changes only occur when Claude explicitly calls MCP tools
  - No background synchronization or external updates
- **Single graph instance**: MVP assumes one graph per user (no multiple projects/workspaces)

### Functional Constraints

- **Limited State management**: Only MANUAL States in Phase 1
  - ANY/ALL/IMMUTABLE logic deferred to Phase 2
  - Waiting For query relies on responsibleParty (not MANUAL States)
- **No pattern detection**: Advanced pattern awareness deferred to Phase 2A
  - Weekly review is basic data presentation, not behavioral insights
- **No Someday/Maybe**: Not implemented in MVP
  - Users can create UNSPECIFIED dependencies as alternative
- **Basic duplicate detection**: Relies on frontier model judgment
  - No tuning, confidence scoring, or learning from corrections
  - May produce false positives or miss duplicates
- **Delete cascading**: Manual only (must explicitly request cascade)
  - Deleting task with dependents creates broken dependencies
  - No automatic cleanup of orphaned connections (graph-memory-core auto-deletes connections, not nodes)
- **No parent auto-completion**: User must explicitly mark projects complete
  - Even when all dependencies satisfied, parent remains incomplete
  - Claude may prompt but doesn't auto-complete

### Performance Constraints

- **Query complexity**: Projects/Next Actions/Waiting For require multiple MCP calls and graph traversals
  - May be slow at scale (>1000 tasks)
  - O(n*m) for Next Actions where n=tasks, m=avg dependencies
- **Duplicate detection**: Semantic similarity requires frontier model inference
  - May take 1-2s per duplicate check
  - Not suitable for batch operations
- **Multi-step operations**: Creating project with many subtasks is serial
  - 10 subtasks = 10 create_node calls + 10 create_connection calls = ~1-2 seconds total

### Known Limitations

- **Inference variability**: Frontier model behavior may vary
  - Same prompt may get different inference decisions across conversations
  - No deterministic inference logic
- **Empty query results**: When no Next Actions, Claude can only suggest creating tasks
  - Cannot proactively recommend actions
- **Ambiguity resolution**: When multiple tasks match, Claude lists options
  - User must explicitly choose (no intelligent selection)
- **Context tracking burden**: User must manually update Context.isAvailable
  - No automatic detection of location/tool availability
- **No task scheduling**: No date/time awareness beyond timestamps
  - "Tomorrow" in task description is just text, not scheduled date
- **No priority or urgency**: All Next Actions presented equally
  - No sorting by importance or deadline
- **Broken dependencies after delete**: Deleting task leaves dependents with unsatisfied dependencies
  - No automatic cleanup (unless cascade delete explicitly requested)

### Out of Scope

Explicitly excluded from Feature 4:
- ANY/ALL/IMMUTABLE State creation and logic (Phase 2)
- Pattern-aware weekly review (Phase 2A)
- Someday/Maybe category (not in MVP)
- GUI visualization (not in MVP)
- Real-time monitoring (not in MVP)
- Multi-user support (not in MVP)
- Task scheduling or calendar integration (future)
- Priority or urgency management (future)
- Optimization for >1000 tasks (future)
- Person nodes for collaboration (Phase 2)

## Implementation Notes

### Testing Strategy

**Two-Phase Approach:**

1. **Automated Eval Tests (TDD during development)**
   - **Script**: `test_conversational_layer.py` (single file, <300 lines)
   - **Test cases**: `test_cases.json` (24 minimum, expandable)
   - **Execution**: Invoke `claude --print <prompt>` in non-interactive mode, capture stdout
   - **Judging**: Separate Claude invocation evaluates output against behavioral criteria
   - **TDD Workflow**:
     - **Red**: Write test case defining desired behavior
     - **Green**: Refine system prompt until test passes
     - **Refactor**: Improve prompt clarity without breaking tests

2. **Real Usage Validation (3-5 days manual testing)**
   - Use Claude Code for actual GTD management (self-dogfooding)
   - Assess "solid vs rough vs broken" per ROADMAP Phase 1 checkpoint
   - Track failure cases, ambiguities, inference errors, duplicate misses
   - Iterate on system prompt based on real usage patterns
   - Document rough/broken areas for Phase 2 improvements

**Eval Framework Structure:**

```python
# test_conversational_layer.py

import json
import subprocess
import sys

def run_test(test_case):
    """Execute one test case."""
    prompt = test_case['prompt']
    expected_behavior = test_case['expected_behavior']

    # Invoke Claude Code in non-interactive mode
    result = subprocess.run(
        ['claude', '--print', prompt],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        return {
            'pass': False,
            'reasoning': f'Claude Code exited with error: {result.stderr}'
        }

    # Judge output (call Claude to evaluate behavioral match)
    judgment = judge_output(result.stdout, expected_behavior)
    return judgment

def judge_output(actual_output, expected_behavior):
    """Use Claude to judge if output satisfies behavioral criteria."""
    judge_prompt = f"""
You are evaluating a conversational GTD assistant's response.

Expected behavior: {expected_behavior}

Actual output: {actual_output}

Does the actual output satisfy the expected behavior? Consider:
- Behavioral match (not exact text match)
- Correct tool usage (if applicable)
- Appropriate inference vs asking
- Helpful user communication

Respond in JSON:
{{
  "pass": true/false,
  "reasoning": "explanation of judgment"
}}
"""

    result = subprocess.run(
        ['claude', '--print', judge_prompt],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Parse JSON response
    try:
        return json.loads(result.stdout)
    except:
        return {
            'pass': False,
            'reasoning': 'Judge failed to return valid JSON'
        }

def main():
    with open('test_cases.json') as f:
        test_cases = json.load(f)

    results = []
    for i, test_case in enumerate(test_cases):
        print(f"Running test {i+1}/{len(test_cases)}: {test_case['name']}")
        judgment = run_test(test_case)
        results.append({
            'test': test_case['name'],
            'pass': judgment['pass'],
            'reasoning': judgment['reasoning']
        })

    # Print summary
    passed = sum(1 for r in results if r['pass'])
    print(f"\n{passed}/{len(results)} tests passed")

    # Print failures
    failures = [r for r in results if not r['pass']]
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"- {f['test']}: {f['reasoning']}")

    sys.exit(0 if passed == len(results) else 1)

if __name__ == '__main__':
    main()
```

**Test Case Categories** (minimum 24):
- **Capture (8)**: Simple task, with context, with dependency, UNSPECIFIED, duplicate detection, project with subtasks, delegated task, MANUAL state
- **Query (6)**: Next actions, projects, waiting for, context-filtered, stuck projects, specific lookup
- **Update (4)**: Mark complete, update details, change context availability, report MANUAL state
- **Delete (2)**: Delete with warning, cascade when confirmed
- **Edge Cases (4)**: Empty results, ambiguous reference, conflicting updates, undefined context

**Pass Criteria Examples:**
- "Creates Task node with isComplete=false and appropriate content"
- "Queries graph before responding (calls query_nodes or similar)"
- "Warns user about dependencies before deleting"
- "Recognizes duplicate and asks user for confirmation"

**Not Pass Criteria:**
- "Responds with exact text X" (too brittle)
- "Uses specific node ID" (IDs are opaque)

### Prompt Engineering Approach

1. **Start Simple**:
   - Begin with core concepts (Task/State/Context, DependsOn, derived views)
   - Add 5-7 examples per category
   - Test with basic scenarios

2. **Iterate Based on Tests**:
   - Run eval tests, identify failures
   - Add examples addressing failure modes
   - Refine inference principles
   - Expand to 25-30 examples based on test coverage needs

3. **Test Edge Cases Early**:
   - Duplicate detection (semantic similarity)
   - Ambiguity handling (multiple matches, unclear intent)
   - Empty results (helpful messages)
   - Delete warnings (dependency checking)

4. **Balance Inference vs Asking**:
   - Monitor over-asking (annoying) vs over-inferring (inaccurate)
   - Adjust principles based on user feedback during manual validation
   - Use eval tests to codify inference expectations

5. **TDD Loop**:
   - Write test for desired behavior (Red)
   - Add/refine prompt section or example (Green)
   - Simplify prompt without breaking tests (Refactor)
   - Repeat for all acceptance criteria

### Weekly Review Format Details

**Completed this week:**
- Query: Tasks with isComplete=true AND modified in last 7 days
- Sort: modified desc (most recent first)
- Limit: 20 tasks
- Display: Title, completion date

**Active projects:**
- Query: Projects query (Tasks with outgoing DependsOn) AND isComplete=false
- For each: Count incomplete dependencies (Tasks/States/Contexts that are not satisfied)
- Sort: By last activity (most recent dependency completion)
- Limit: All (typically <50 for MVP scale)
- Display: Title, incomplete dependency count, last activity date

**Stuck projects:**
- Query: Active projects with no dependencies completed in >14 days
- Sort: By oldest activity (least recent first)
- Limit: All stuck projects
- Display: Title, days since last activity, incomplete dependency count

**Next actions:**
- Query: Next Actions query (per specification)
- Sort: By created date (oldest first) or by context
- Limit: 20 tasks
- Display: Title, required contexts (if any)

**Waiting for:**
- Query: Waiting For query (responsibleParty != "me")
- Sort: By modified asc (oldest waiting first)
- Limit: 20 tasks
- Display: Title, responsible party, days waiting (now - created)

**Context availability:**
- Query: All Context nodes
- Sort: Alphabetically
- Limit: All (typically <10 for MVP)
- Display: Title, current availability status

### Parent Completion Behavior

**Decision:** No automatic parent completion

**Rationale:**
- Explicit completion gives user control
- "Done" for project may mean different things (all tasks done, vs project abandoned, vs project redefined)
- User may want to review/reflect before marking project complete

**Implementation:**
- When all dependencies of a Task satisfied, Task does NOT auto-update isComplete=true
- Claude MAY notify user: "All subtasks of [Project] complete. Mark project complete?"
- User responds "yes" (or "mark it complete") → Claude updates Task.isComplete=true
- User responds "no" or ignores → Project remains incomplete

**Testing:**
- AC46 codifies no auto-completion
- Scenario 4 demonstrates explicit parent completion

## Open Questions

None. All questions resolved during spec-writing-helper collaboration and review feedback incorporation.

If issues arise during implementation or testing, they will be tracked here.

## References

- **ROADMAP.md** - Feature 4: Conversational Layer
  - Phase 1, Week 2
  - Why now: Tests risky integration (Claude reliability assumption)
  - Delivers: Natural language GTD interaction, validates core assumption
  - Effort: 2 days (1 day prompt engineering with TDD, 1 day manual testing/iteration)

- **VISION.md** - Strategic Context
  - Core assumption: "Claude can reliably manage GTD memory through conversation"
  - Technical requirements: Task/State/DependsOn model, Context.isAvailable
  - Philosophy: Derived views (Projects/Next Actions) instead of separate types

- **SCOPE.md** - MVP Boundaries
  - Context nodes included in MVP (not deferred)
  - State nodes partially included (MANUAL only, ANY/ALL/IMMUTABLE deferred to Phase 2)
  - MVP scale: 50-100 projects, 200-500 tasks

- **specs/done/gtd-ontology.md** - GTD Ontology v1.3 (Feature 3)
  - Node types: Task (isComplete, responsibleParty), State (isTrue, logic), Context (isAvailable), UNSPECIFIED
  - Connection type: DependsOn with topology rules
  - Query patterns: Projects, Next Actions, Waiting For
  - Property schemas and algorithms
  - Status: Approved, Implemented

- **specs/done/graph-memory-core.md** - Graph Memory Core v1.2 (Feature 2)
  - MCP server: graph-memory-core
  - Tools: create_node, get_node, query_nodes, update_node, create_connection, query_connections, get_connected_nodes, delete_node, ensure_singleton_node
  - Property constraints: string/number/boolean only, no nested objects
  - Topology validation, cascade delete
  - Status: Done

- **src/gtd-ontology/src/types.ts** - GTD Ontology TypeScript Types
  - TaskProperties interface: isComplete, responsibleParty
  - StateProperties interface: isTrue, logic
  - ContextProperties interface: isAvailable
  - GraphMemoryClient interface: MCP tool signatures

---

**Version History:**

- **v2.0 (2025-11-02)**: Addressed spec review feedback (NEEDS-CHANGES → Draft for re-review)
  - Fixed header metadata: Added created, author; changed status to "Draft"; fixed title to "Specification:"
  - Aligned all data model with GTD Ontology v1.3:
    - Removed type (TASK/PROJECT) and completedAt fields
    - Used isComplete: boolean for Tasks
    - Projects are derived views (Tasks with outgoing DependsOn connections), not separate type
    - Waiting For redefined using responsibleParty property (not MANUAL States)
  - Added concrete Interface Contract with MCP tool signatures from graph-memory-core
  - Wrote precise query semantics with TypeScript algorithms for Projects/Next Actions/Waiting For/Stuck
  - Clarified MANUAL State support in Phase 1 (ANY/ALL/IMMUTABLE deferred to Phase 2)
  - Updated all 46 Acceptance Criteria to use correct ontology properties
  - Updated all 8 Scenarios with correct properties and concrete examples (node IDs, exact tool calls)
  - Clarified parent completion behavior: No auto-completion, user explicit action
  - Added weekly review format details (sort orders, limits, display format)
  - Included eval framework structure (Python script example)
  - Removed placeholder examples (noted 25-30 examples needed in system prompt section)

- **v1.0 (2025-11-02)**: Initial specification following spec-writing-helper collaboration
  - Comprehensive 7-phase Socratic dialogue
  - User decisions documented throughout
  - Ready for review process

---

**Next Steps:**

1. **Spec re-review**: Submit to spec-reviewer for validation against checklist
2. **Approval criteria**:
   - All schema-required sections present with concrete content
   - Data model aligned with GTD Ontology v1.3
   - MCP tool contract specified
   - Query semantics precise and testable
   - Acceptance criteria and scenarios concrete with correct properties
3. **Upon approval**: Move to specs/todo/conversational-layer.md
4. **Implementation**:
   - Create system prompt file (with 25-30 concrete examples)
   - Create eval framework (test_conversational_layer.py + test_cases.json)
   - TDD prompt engineering: Red-Green-Refactor until tests pass
   - Manual validation: 3-5 days real usage, assess solid/rough/broken
   - Phase 1 checkpoint: Decide if ready for Phase 2 or needs iteration
