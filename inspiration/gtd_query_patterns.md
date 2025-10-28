# GTD Assistant - Query Patterns

## Overview

How to compose primitive queries to support intelligent coaching.

**Part of:** GTD Assistant Specification  
**See also:** memory_system_core.md, gtd_interaction_principles.md

## Core Principle

Don't use high-level "what_can_user_do()" functions. Instead, **compose primitive queries** to maintain flexibility and deploy full reasoning.

## Primitive Operations

```typescript
// Available primitives
query_nodes(type?, property_filter?)
query_connections(from?, to?, type?, property_filter?)
get_connected_nodes(from, connection_type?, direction?)
search_content(query, node_type?, limit?)
recall(query, limit?)  // Semantic search
```

## Pattern: Finding Available Actions

```typescript
// 1. Get all next actions
const actions = query_nodes('Action', {status: 'next'})

// 2. Filter by context
const contextFiltered = actions.filter(id => {
  const node = get_node(id)
  return contexts.includes(node.properties.context)
})

// 3. Check dependencies (not blocked)
const available = contextFiltered.filter(id => {
  const deps = get_connected_nodes(id, 'DependsOn', 'out')
  return deps.every(depId => {
    return get_node(depId).properties.status === 'complete'
  })
})

// 4. Get rich content for top items
const enriched = available.slice(0, 5).map(id => ({
  id,
  node: get_node(id),
  content: get_node_content(id)
}))

// 5. REASON about what this reveals
// - Which build on recent momentum?
// - Which are being avoided?
// - What matches energy level?
```

## Pattern: Stuck Project Detection

```typescript
const projects = query_nodes('Project', {status: 'active'})

const stuck = projects.filter(projId => {
  const nextActions = get_connected_nodes(projId, 'NextAction')
  
  // No next actions defined
  if (nextActions.length === 0) return true
  
  // All next actions are blocked
  const allBlocked = nextActions.every(actId => {
    const deps = get_connected_nodes(actId, 'DependsOn')
    return deps.some(depId => 
      get_node(depId).properties.status !== 'complete'
    )
  })
  
  return allBlocked
})
```

## Pattern: Avoidance Detection

```typescript
// Find frequently migrated actions
const actions = query_nodes('Action', {status: 'next'})

const avoided = actions.filter(actId => {
  const content = get_node_content(actId)
  // Count migrations in content
  const migrations = (content.match(/Migrated:/g) || []).length
  return migrations >= 3
})

// These need attention - something's blocking the user
```

## Pattern: Overdue Waiting Items

```typescript
const waiting = query_connections({type: 'WaitingFor'})
const now = new Date()

const overdue = waiting.filter(connId => {
  const conn = get_connection(connId)
  const followUp = new Date(conn.properties.follow_up_date)
  return followUp < now
})

// Proactively remind user to follow up
```

## Pattern: Weekly Review

```typescript
for (const projId of active_projects) {
  // Check multiple aspects
  const nextActions = get_connected_nodes(projId, 'NextAction')
  const waiting = query_connections({from: projId, type: 'WaitingFor'})
  const recentActivity = recall(`${projId} progress`, limit=5)
  
  // Synthesize insights
  if (nextActions.length === 0) {
    // Project is stuck
  }
  if (waiting.some(isOverdue)) {
    // Need to follow up
  }
  if (recentActivity.length === 0) {
    // Project has stalled
  }
}
```

## Pattern: Context-Based Recommendations

```typescript
// User asks "What can I do @home for 30min?"

// 1. Get actions requiring @home context
const homeActions = query_nodes('Action', {
  status: 'next',
  context: 'home'
})

// 2. Check time estimates in content
const shortActions = homeActions.filter(actId => {
  const content = get_node_content(actId)
  const timeMatch = content.match(/Time: (\d+)/)
  return timeMatch && parseInt(timeMatch[1]) <= 30
})

// 3. Consider recent history
const recentWork = recall("completed @home actions", limit=10)

// 4. Synthesize recommendation
// - Suggest variety
// - Build on momentum
// - Address important projects
```

## Key Insights

1. **Compose, don't prescribe**: Multiple simple queries > one complex query
2. **Think about results**: Don't just return data, reason about what it means
3. **Context matters**: Consider recent history, patterns, user's situation
4. **Multiple sources**: Query graph + search content + semantic recall
5. **Synthesize**: Combine information to create insights

## Why This Matters

High-level functions like `what_can_user_do()` lock you into predefined patterns.

Primitive composition lets you:
- Adapt to specific questions
- Be creative in reasoning
- Notice unexpected patterns
- Provide personalized insight

This is the difference between retrieving "standard advice" and deploying full capabilities.
