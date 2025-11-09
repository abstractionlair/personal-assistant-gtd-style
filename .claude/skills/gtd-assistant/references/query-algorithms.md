# Query Algorithms Reference

Precise algorithms for computing derived views (Projects, Next Actions, Waiting For, Stuck Projects). These are NOT stored node types—they're computed on demand via queries.

## Projects Query

**Definition:** Tasks with outgoing DependsOn connections

**Algorithm:**

```typescript
// Step 1: Get all Tasks
const allTasks = query_nodes({ type: "Task" })

// Step 2: For each Task, check for outgoing DependsOn connections
const projects = []
for (const taskId of allTasks.node_ids) {
  const outgoingDeps = query_connections({
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

**Key points:**
- A Task is a project if it has at least one outgoing DependsOn connection
- Both complete and incomplete tasks can be projects
- No separate "Project" node type exists

**Example:**
- Task "Launch website" with DependsOn connections to "Design homepage", "Write content", "Deploy" → **IS** a Project
- Task "Buy birthday card" with no DependsOn connections → **NOT** a Project

---

## Next Actions Query

**Definition:** Incomplete Tasks where all immediate dependencies are satisfied

**Algorithm:**

```typescript
// Step 1: Get all incomplete Tasks
const incompleteTasks = query_nodes({
  type: "Task",
  properties: { isComplete: false }
})

// Step 2: Filter to Tasks with satisfied dependencies
const nextActions = []

for (const taskId of incompleteTasks.node_ids) {
  // Get immediate dependencies (outgoing DependsOn connections)
  const depNodeIds = get_connected_nodes({
    node_id: taskId,
    connection_type: "DependsOn",
    direction: "out"
  })

  // Check if all dependencies satisfied
  let allSatisfied = true
  for (const depId of depNodeIds.node_ids) {
    const depNode = get_node({ node_id: depId })

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

**Key points:**
- Only checks immediate dependencies (no recursion)
- UNSPECIFIED always blocks (tasks depending on UNSPECIFIED never actionable)
- Empty dependencies array means task is actionable (no blockers)
- Tasks with `responsibleParty` not equal to "me" should be excluded (they're Waiting For)

**Example:**
- Task "Write report" (isComplete=false, no dependencies) → **IS** Next Action
- Task "Review report" (isComplete=false, depends on incomplete "Write report") → **NOT** Next Action
- Task "Define requirements" (isComplete=false, depends on UNSPECIFIED) → **NOT** Next Action

---

## Context-Filtered Next Actions

**Definition:** Next Actions that respect context availability

**Algorithm:**

```typescript
// Step 1: Run standard Next Actions query
const nextActions = computeNextActions() // from above

// Step 2: Get available contexts
const availableContexts = query_nodes({
  type: "Context",
  properties: { isAvailable: true }
})
const availableContextIds = new Set(availableContexts.node_ids)

// Step 3: Filter next actions by context requirements
const filteredActions = []

for (const taskId of nextActions) {
  const dependencies = get_connected_nodes({
    node_id: taskId,
    connection_type: "DependsOn",
    direction: "out"
  })

  // Check if all context dependencies are available
  let contextsSatisfied = true
  for (const depId of dependencies.node_ids) {
    const depNode = get_node({ node_id: depId })
    if (depNode.type === "Context") {
      if (!availableContextIds.has(depId)) {
        contextsSatisfied = false
        break
      }
    }
  }

  if (contextsSatisfied) {
    filteredActions.push(taskId)
  }
}

return filteredActions
```

**Returns:** Array of Task node IDs for Next Actions with available contexts

**Key points:**
- Builds on Next Actions query
- Only includes tasks where ALL required contexts are available
- Tasks with no context dependencies are always included

**Example:**
- Task "Review code" requiring @laptop (unavailable) → **EXCLUDED**
- Task "Call client" requiring @phone (available) → **INCLUDED**
- Task "Plan meeting" with no context requirements → **INCLUDED**

---

## Waiting For Query

**Definition:** Incomplete Tasks delegated to external parties

**Algorithm:**

```typescript
// Get all incomplete Tasks with external responsibility
const incompleteTasks = query_nodes({
  type: "Task",
  properties: { isComplete: false }
})

const waitingFor = []

for (const taskId of incompleteTasks.node_ids) {
  const task = get_node({ node_id: taskId })

  // Check if responsibleParty exists and is not "me"
  if (task.properties.responsibleParty &&
      task.properties.responsibleParty !== "me") {
    waitingFor.push(taskId)
  }
}

return waitingFor
```

**Returns:** Array of Task node IDs representing Waiting For tasks

**Key points:**
- "me" is special value indicating current user
- All other values indicate external party (e.g., "Jane", "Finance team", "City council")
- Tasks without `responsibleParty` assumed to be user's responsibility

**Example:**
- Task "Waiting for logo designs" (isComplete=false, responsibleParty="Jane") → **IS** Waiting For
- Task "Write documentation" (isComplete=false, responsibleParty="me") → **NOT** Waiting For
- Task "Review code" (isComplete=false, no responsibleParty) → **NOT** Waiting For

---

## Stuck Projects Query

**Definition:** Projects with no recent activity (>14 days since last dependency completion)

**Algorithm:**

```typescript
// Step 1: Get all Projects (Tasks with outgoing dependencies)
const projects = computeProjects() // from above

// Step 2: Filter to incomplete Projects
const incompleteProjects = []
for (const projId of projects) {
  const proj = get_node({ node_id: projId })
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
  const depNodeIds = get_connected_nodes({
    node_id: projId,
    connection_type: "DependsOn",
    direction: "out"
  })

  // Find most recent completion timestamp among dependencies
  let mostRecentCompletion = null

  for (const depId of depNodeIds.node_ids) {
    const depNode = get_node({ node_id: depId })

    if (depNode.type === "Task" && depNode.properties.isComplete) {
      const modifiedTime = new Date(depNode.modified).getTime()
      if (!mostRecentCompletion || modifiedTime > mostRecentCompletion) {
        mostRecentCompletion = modifiedTime
      }
    }
  }

  // Check if stuck (no completions or last completion >14 days ago)
  if (!mostRecentCompletion) {
    // No dependencies ever completed
    // Use project's created timestamp instead
    const projNode = get_node({ node_id: projId })
    const createdTime = new Date(projNode.created).getTime()
    if ((now - createdTime) > TWO_WEEKS_MS) {
      stuck.push({
        projId,
        lastCompletion: null,
        daysSince: Math.floor((now - createdTime) / (24 * 60 * 60 * 1000))
      })
    }
  } else if ((now - mostRecentCompletion) > TWO_WEEKS_MS) {
    stuck.push({
      projId,
      lastCompletion: new Date(mostRecentCompletion).toISOString(),
      daysSince: Math.floor((now - mostRecentCompletion) / (24 * 60 * 60 * 1000))
    })
  }
}

return stuck
```

**Returns:** Array of stuck project info with:
- `projId`: Task ID
- `lastCompletion`: ISO 8601 timestamp or null
- `daysSince`: Integer days since last completion

**Criteria for "stuck":**
- Project is incomplete (isComplete=false)
- No dependencies completed in last 14 days (checked via `modified` timestamp)
- If no dependencies ever completed, use project's `created` timestamp

**Key points:**
- Only completed dependencies count (isComplete=true)
- Use `modified` timestamp on dependency Tasks
- If no completions at all, evaluate against project's `created` timestamp
- Report exact timestamps in ISO 8601 format

**Example:**
- Project "Redesign landing page" with 5 subtasks, last completed subtask 21 days ago → **IS** Stuck
- Project "Refactor auth" with 3 subtasks, completed subtask 3 days ago → **NOT** Stuck
- Project "Launch marketing" with 0 completed subtasks, created 20 days ago → **IS** Stuck

**Required output fields (per stuck project):**
- `task_id`: exact id of the project task
- `last_completion`: ISO 8601 timestamp of most recent completed dependency, or `null` if none
- `days_since`: integer (omit when `last_completion` is null)
- `dependency_title`: the completed dependency whose timestamp you reported (omit when `last_completion` is null)

**Example output:**
> Stuck project: Update employee handbook (task_id=mem_xyz789_abc123) — no recent activity in 21 days (last progress: 2025-10-20T15:42:00Z on 'Outline draft').

---

## Weekly Review Queries

**Definition:** Combined view of user's GTD system state

**Components:**

### 1. Completed This Week

```typescript
const now = Date.now()
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000

const completedTasks = query_nodes({
  type: "Task",
  properties: { isComplete: true }
})

const completedThisWeek = []
for (const taskId of completedTasks.node_ids) {
  const task = get_node({ node_id: taskId })
  const modifiedTime = new Date(task.modified).getTime()
  if ((now - modifiedTime) <= SEVEN_DAYS_MS) {
    completedThisWeek.push({
      taskId,
      completed: task.modified
    })
  }
}

// Sort by modified desc (most recent first)
completedThisWeek.sort((a, b) =>
  new Date(b.completed) - new Date(a.completed)
)

// Limit to 20
return completedThisWeek.slice(0, 20)
```

### 2. Active Projects

```typescript
const projects = computeProjects() // from Projects query

const activeProjects = []
for (const projId of projects) {
  const proj = get_node({ node_id: projId })
  if (!proj.properties.isComplete) {
    // Count incomplete dependencies
    const deps = get_connected_nodes({
      node_id: projId,
      direction: "out"
    })

    let incompleteDeps = 0
    let lastActivity = null

    for (const depId of deps.node_ids) {
      const dep = get_node({ node_id: depId })
      if (dep.type === "Task") {
        if (!dep.properties.isComplete) {
          incompleteDeps++
        } else {
          const modTime = new Date(dep.modified).getTime()
          if (!lastActivity || modTime > lastActivity) {
            lastActivity = modTime
          }
        }
      } else if (dep.type === "State") {
        if (!dep.properties.isTrue) incompleteDeps++
      } else if (dep.type === "Context") {
        if (!dep.properties.isAvailable) incompleteDeps++
      }
    }

    activeProjects.push({
      projId,
      incompleteDeps,
      lastActivity: lastActivity ? new Date(lastActivity).toISOString() : proj.created
    })
  }
}

// Sort by last activity (most recent first)
activeProjects.sort((a, b) =>
  new Date(b.lastActivity) - new Date(a.lastActivity)
)

return activeProjects
```

### 3. Next Actions

```typescript
const nextActions = computeNextActions() // from Next Actions query

// Optionally group by context
const actionsByContext = {}

for (const taskId of nextActions) {
  const deps = get_connected_nodes({
    node_id: taskId,
    direction: "out"
  })

  let contexts = []
  for (const depId of deps.node_ids) {
    const dep = get_node({ node_id: depId })
    if (dep.type === "Context") {
      contexts.push(dep.id)
    }
  }

  const contextKey = contexts.length > 0
    ? contexts.sort().join(',')
    : 'no-context'

  if (!actionsByContext[contextKey]) {
    actionsByContext[contextKey] = []
  }
  actionsByContext[contextKey].push(taskId)
}

// Limit to first 20 total
const flatActions = Object.values(actionsByContext).flat()
return flatActions.slice(0, 20)
```

### 4. Waiting For

```typescript
const waitingFor = computeWaitingFor() // from Waiting For query

// Sort by modified asc (oldest first)
const waitingWithTimestamps = []
for (const taskId of waitingFor) {
  const task = get_node({ node_id: taskId })
  waitingWithTimestamps.push({
    taskId,
    responsibleParty: task.properties.responsibleParty,
    waitingSince: task.created,
    daysWaiting: Math.floor((Date.now() - new Date(task.created).getTime()) / (24 * 60 * 60 * 1000))
  })
}

waitingWithTimestamps.sort((a, b) =>
  new Date(a.waitingSince) - new Date(b.waitingSince)
)

// Limit to 20
return waitingWithTimestamps.slice(0, 20)
```

### 5. Context Availability

```typescript
const allContexts = query_nodes({ type: "Context" })

const contextStatus = []
for (const ctxId of allContexts.node_ids) {
  const ctx = get_node({ node_id: ctxId })
  const content = get_node_content({ node_id: ctxId })
  contextStatus.push({
    ctxId,
    name: content.content, // or extract from content
    isAvailable: ctx.properties.isAvailable
  })
}

// Sort alphabetically
contextStatus.sort((a, b) => a.name.localeCompare(b.name))

return contextStatus
```

---

## Performance Notes

**Query Complexity:**
- Projects: O(n) where n = number of Tasks
- Next Actions: O(n*m) where n = Tasks, m = avg dependencies per task
- Waiting For: O(n) where n = number of Tasks
- Stuck Projects: O(n*m) where n = Projects, m = avg dependencies

**Scale Considerations:**
- MVP targets 50-100 projects, 200-500 tasks
- Linear scans acceptable at this scale
- No caching or optimization needed for MVP
- Beyond 1000 tasks, consider optimizations

**MCP Round-Trip Latency:**
- Each tool call: ~50-100ms
- Multi-step queries: 500ms-1s total
- Weekly review: 2-5 seconds (multiple queries)

---

## Query Optimization Tips

1. **Batch node fetches:** If fetching many nodes, consider which data you actually need
2. **Cache query results:** Within a single conversation turn, reuse query results
3. **Filter early:** Apply `isComplete=false` filters at query time, not in code
4. **Traverse efficiently:** Use `get_connected_nodes` instead of `query_connections` + iteration

---

## Testing Query Correctness

**Validate with known graph states:**

```typescript
// Example test case for Next Actions
Given:
- Task A (isComplete=false, no deps)
- Task B (isComplete=false, depends on Task C)
- Task C (isComplete=false)
- Task D (isComplete=false, depends on Context @office where isAvailable=true)

Expected Next Actions:
- Task A (no blockers)
- Task D (context available)

NOT Next Actions:
- Task B (depends on incomplete Task C)
- Task C (no blockers, should be included)

Correction: Task C should be in Next Actions too!
```

**Test edge cases:**
- Empty graph
- All tasks complete
- All contexts unavailable
- Circular dependencies (should not occur, but test handling)
- Tasks with multiple dependencies (all vs some satisfied)
