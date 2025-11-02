# GTD Graph Ontology Specification

## Overview

This document specifies a graph-based task management system inspired by David Allen's Getting Things Done (GTD) methodology, but designed to scale from personal productivity to team/organizational workflows. The system uses a directed acyclic graph (DAG) of tasks and states to model work, with emergent properties that naturally surface actionable items.

## Design Philosophy

### Core Insights

1. **Everything is atomic relative to its dependencies**: Rather than pre-classifying tasks as "atomic actions" vs "compound projects", we allow any task to be atomic IF its dependencies are properly specified. An improperly decomposed task simply won't advance.

2. **Hierarchy emerges from structure**: Projects are not special node types - they are simply subgraphs of related tasks. The distinction between "action" and "project" emerges from the graph topology and completion state.

3. **Dependencies can target states or tasks**: While direct task-to-task dependencies are practical and common, we support optional state-based dependencies for richer modeling (inspired by STRIPS/PDDL planning systems).

4. **The boundary layer is what matters**: At any moment, the actionable tasks ("next actions" in GTD terms) are automatically identified by graph topology: incomplete tasks where all dependencies are satisfied and you're responsible.

5. **Progressive disclosure**: You don't need to specify all dependencies upfront. Tasks can be added incrementally as you discover what's needed.

### Relationship to GTD

**What we preserve:**
- Weekly review surfaces (Projects, Waiting For, Next Actions - all derived queries)
- Context-based filtering
- Clear distinction between "mine" vs "external" responsibility
- Incremental planning (don't need full task decomposition upfront)
- Low cognitive load during capture

**What we change:**
- Projects and Actions are unified as Tasks
- Dependencies are explicit rather than implicit
- Natural support for task hierarchies and sub-projects
- Can express parallel work and complex dependencies
- Foundation for value-based prioritization (future)

### Connection to Operating System Schedulers

This design is inspired by viewing GTD as analogous to an OS process scheduler:
- Tasks are like processes with state (ready/blocked/complete)
- Dependencies are like waiting on I/O or semaphores
- The boundary layer is like the ready queue
- Review processes are like garbage collection
- External tasks are like blocking on external events

## Core Data Model

### Node Types

#### Task
Represents a commitment, outcome, or unit of work. Can be atomic (doable in one step) or compound (requires subtasks), though this distinction is emergent rather than explicit.

**Properties:**
- `description: string` - What needs to be done or achieved
- `isComplete: boolean` - Whether this task is done
- `responsibleParty: string` - Who owns this: "me", "external", team name, or person ID
- `context: string[]` - Optional GTD contexts (e.g., ["@computer", "@home"])
- `intrinsicValue: number` - Optional. Value delivered by completing this task alone (default: 0)
- `instrumentalValue: number` - Optional. Computed value accounting for downstream tasks
- `notes: string` - Optional. Additional details, references, etc.
- `dateAdded: timestamp` - When this task was created
- `dateCompleted: timestamp` - When marked complete (if applicable)

**Semantics:**
- A task is *actionable* when: not complete AND all dependencies satisfied AND I'm responsible
- A task is *blocked* when: not complete AND some dependencies unsatisfied
- A task is *delegated/external* when: not complete AND responsibleParty != "me"
- A task is *compound* when: it has outgoing DependsOn edges (has been explicitly decomposed)
- A task is *atomic* (relative to its dependencies) when: no outgoing DependsOn edges OR dependencies specify all work needed

**Proper vs Improper task specification:**
- A task is *properly specified* if, once all its dependencies are satisfied, it can be completed without further decomposition or planning
- An *improperly specified* task has no dependencies but still requires thinking/decomposition before execution
- Example: "Write book" with no dependencies = improper (needs decomposition)
- Example: "Write book" depending on all chapters = proper (just assemble and publish)
- The system doesn't enforce this - users learn through practice (like GTD)

#### State
Represents a condition or state of the world that can be true or false. Used for richer dependency modeling when task-to-task dependencies are insufficient.

**Properties:**
- `description: string` - What needs to be true (e.g., "pizza is delivered", "report is reviewed")
- `isTrue: boolean` - Current truth value
- `notes: string` - Optional. How to verify, additional context

**Semantics:**
States are optional. Many dependencies can be expressed task-to-task. Use states when:
- Multiple tasks could satisfy the same precondition
- The achievement method is truly an implementation detail
- Explicitly modeling world state aids clarity

### Relationship Types

#### DependsOn
A unified dependency relationship that works across all node types.

**Valid connections:**
- `Task --DependsOn--> Task`
- `Task --DependsOn--> State`
- `State --DependsOn--> Task`

**Semantics:**
The source cannot be satisfied/completed until the target is satisfied/completed.

- For Tasks: Cannot complete until all DependsOn targets are satisfied
- For States: Becomes true when DependsOn tasks complete (see logic below)
- Transitive: if A depends on B and B depends on C, then A implicitly depends on C
- Acyclic: cycles indicate improper specification and should be detected/prevented
- Can have null source: for tracking external events not tied to specific tasks (MVP: allow this for "Waiting For" items without explicit follow-up actions)

**Completion logic:**
- **Task satisfaction:** A task is satisfied when `isComplete == true`
- **State satisfaction:** A state is satisfied when `isTrue == true`
- **Task actionability:** A task becomes actionable when ALL DependsOn targets are satisfied
- **State truth:** A state becomes true when its DependsOn condition is met (ANY or ALL logic - see below)

**ANY/ALL logic for States:**
States can have multiple incoming DependsOn edges, representing alternative ways to achieve that state.

**ANY logic (default for MVP):**
State becomes true when ANY of its DependsOn tasks complete.
```
State: "Have food"
  - DependsOn: ["Order pizza", "Cook dinner", "Get takeout"]
  - Logic: ANY
→ "Have food" becomes true when first of these completes
```

**ALL logic (optional, future):**
State becomes true only when ALL of its DependsOn tasks complete.
```
State: "Ready to deploy"
  - DependsOn: ["Tests pass", "Security review done", "Docs updated"]
  - Logic: ALL
→ "Ready to deploy" becomes true only when all three complete
```

**For MVP:** Default to ANY logic for states. ALL logic can be added later if needed.

**Complex logic (future):** Could support nested ANY/ALL expressions, but defer this complexity.

**Examples:**
- `"Write Chapter 2" --DependsOn--> "Write Chapter 1"` (sequential tasks)
- `"Book trip" --DependsOn--> "Research hotels"` (prerequisite)
- `"Book trip" --DependsOn--> "Research flights"` (parallel prerequisites)
- `"Eat dinner" --DependsOn--> "Have food"` (task depends on state)
- `"Have food" --DependsOn--> "Order pizza"` (state depends on task)
- `null --DependsOn--> "Toothpaste delivery"` (standalone waiting item)

## Emergent Concepts

### Projects
A project is any task that has been explicitly decomposed - that is, a task with outgoing DependsOn edges to other tasks or states. It's a compound task whose completion depends on completing subtasks.

**To model a traditional project:**
1. Create a high-level task for the project outcome
2. Create subtasks for the work needed
3. Make the project task depend on its subtasks

Example:
```
"Book published" --DependsOn--> ["Chapter 1 complete", "Chapter 2 complete", ..., "Cover design complete"]
```

**GTD Projects list query:**
All incomplete tasks that have outgoing DependsOn edges (i.e., have been explicitly decomposed into subtasks).

### Next Actions
Next actions are tasks in the "boundary layer" - ready to be executed.

**Query:**
- `isComplete == false`
- `responsibleParty == "me"`
- All DependsOn targets are satisfied (tasks complete, states true)
- Optionally filtered by `context`

This is the primary "what can I do right now?" view.

### Waiting For
External tasks or outcomes you're tracking.

**Query options:**
1. All tasks where `responsibleParty == "external"`
2. All incomplete tasks that have incoming DependsOn edges (things blocking my work)
3. All DependsOn connections with null source (standalone tracking items)

Should be reviewed weekly to determine if follow-up is needed.

### Someday/Maybe
Tasks you might want to do but haven't committed to.

**Modeling options:**
1. Use a special context: `["@someday"]`
2. Add a `status: string` field with values like "active", "someday", "dropped"
3. Simply don't create DependsOn links from other tasks (orphaned in the graph)

Needs design decision for MVP.

## Query Patterns

### Essential Queries

**Next Actions by Context:**
```
Tasks where:
  - isComplete == false
  - responsibleParty == "me"  
  - All DependsOn targets satisfied (tasks complete, states true)
  - context includes specified context
Order by: instrumentalValue desc (when implemented)
```

**Weekly Review - Projects:**
```
Tasks where:
  - isComplete == false
  - Has any task depending on it (is compound)
Order by: dateAdded or custom priority
```

**Weekly Review - Waiting For:**
```
Tasks where:
  - responsibleParty != "me"
  - isComplete == false
OR
DependsOn edges where source is null
```

**Blocked Tasks:**
```
Tasks where:
  - isComplete == false
  - responsibleParty == "me"
  - Some DependsOn target not satisfied (task incomplete or state false)
```

### Visualization Queries

**Subgraph for a Project:**
Given a task T, return all tasks that transitively depend on T (the "upstream" that must complete for T).

**Critical Path:**
For a given goal task, find the longest dependency chain (most time-critical path).

**My Scope:**
All incomplete tasks where I'm responsible or where any descendant task has me as responsible.

## Workflow Patterns

### Capture
```
1. Create new Task node with description
2. Set responsibleParty = "me" (default)
3. Leave isComplete = false
4. Don't worry about dependencies yet (can be added later)
```

### Process (Weekly Review / Clarification)
```
For each unclear or unconnected task:
1. Is this actionable? If not, delete or mark someday
2. What needs to be true/done first? Add DependsOn edges
3. If complex, what are the subtasks? Create them and link
4. Am I responsible or someone else? Update responsibleParty
5. What contexts apply? Add to context array
6. If decomposition is incomplete, optionally mark with UNSPECIFIED dependency
```

**UNSPECIFIED marker (future):**
An explicit signal that a task needs further decomposition but you're not ready to do it yet.
```
Task: "Write book"
  DependsOn: ["Research topic", UNSPECIFIED]
```
This prevents the task from entering the boundary layer even if known dependencies are met. Useful for progressive planning without premature commitment.

### Complete a Task
```
1. Mark isComplete = true
2. Set dateCompleted = now
3. Check if any States have this task as a DependsOn source
   - Update state truth values based on their logic (ANY/ALL)
4. Recompute boundary layer (new next actions may emerge)
```

### Delegate a Task
```
Option A: Change responsibility
  - Update responsibleParty to external/person
  - Now appears in Waiting For list
  
Option B: Create external successor  
  - Mark original task complete
  - Create new Task with responsibleParty = external
  - Make dependent tasks DependsOn the new external task
```

### Follow Up on Waiting Item
```
If too much time has passed:
1. Create new Task "Follow up on X"
2. Make it DependsOn the external task you're waiting on (optional)
3. Or just make it actionable (no dependencies)
```

## Design Decisions for MVP

### Included in MVP
- [x] Task nodes with core properties
- [x] State nodes (basic implementation)
- [x] DependsOn relationships (unified - works across all node combinations)
- [x] responsibleParty field
- [x] context field
- [x] Next Actions query
- [x] Waiting For query  
- [x] Projects list query
- [x] Allow null source for DependsOn (standalone waiting items)
- [ ] Decision needed: ANY/ALL logic for state dependencies
- [ ] Decision needed: UNSPECIFIED dependency marker
- [ ] Decision needed: Distance-based review filtering

### Deferred for Later
- [ ] instrumentalValue computation (requires goal marking + backward propagation)
- [ ] Visual graph rendering
- [ ] Team/multi-user support
- [ ] Historical analysis / completed task graphs
- [ ] Someday/Maybe handling (needs design decision)
- [ ] Recurring tasks
- [ ] Due dates / scheduling
- [ ] Priority beyond value
- [ ] Areas of Responsibility as nodes
- [ ] Effort estimates
- [ ] Batch operations (complete multiple, delete subgraphs)

## Extension Points for Future Vision

This design is intended to be expandable toward a grander vision:

### Distance-Based Review Filtering

**The scalability problem:** As graphs grow, reviewing all Projects or Waiting items becomes overwhelming. Not everything needs weekly attention.

**Solution:** Filter reviews by graph distance from the boundary layer (actionable tasks).

**Graph distance definitions:**
- **Distance 0:** Tasks in boundary layer (actionable now)
- **Distance 1:** Tasks that become actionable when current work completes  
- **Distance 2:** Next wave after that
- **Distance N:** Far future goals

**Mapping to GTD horizons:**
- **Runway (Next Actions):** Distance 0 - actionable now
- **10,000 ft (Projects):** Distance 1-3 - near-term focus
- **20,000 ft (Areas of Responsibility):** Distance 4-6 - medium-term
- **30,000+ ft (Goals/Vision):** Distance 7+ - long-term strategic

**Review frequency by distance:**
- Distance 0-1: Daily/continuous
- Distance 1-3: Weekly (standard GTD weekly review)
- Distance 4-6: Monthly 
- Distance 7+: Quarterly/annually

**Implementation:**
Queries can filter by maximum distance: "Show me all incomplete Projects within distance 3 of the boundary layer."

**Benefits:**
- Keeps weekly reviews focused and manageable
- Ensures near-term work gets attention
- Long-term goals reviewed less frequently but not forgotten
- Natural prioritization emerges from structure

### Multi-Scale Organizational Graph
- Add `team` and `organization` fields to Tasks
- External subgraphs (other teams' work) can collapse into compound nodes
- Same model scales from individual to enterprise

### Value-Based Prioritization
- `intrinsicValue`: utility delivered by this task alone
- `instrumentalValue`: computed by propagating value backward from goals
- `totalValue = intrinsicValue + instrumentalValue`
- Prioritize next actions by value + context match

### Progressive Disclosure / Zoom Levels
- Collapse compound tasks to single nodes when viewing high-level
- Expand to see detailed dependency structure
- Different views for different audiences (your tasks vs team's vs org's)

### Time Flow Visualization
- Layout graph left-to-right by dependency structure
- Completed tasks on left (contiguous region)
- Boundary layer in middle (actionable now)
- Future goals on right
- Time emerges from structure rather than imposed

### Integration Points
- Import/export to other systems (Jira, Asana, etc.)
- Sync with calendar (time-blocked tasks)
- Bidirectional: GTD graph feeds other systems, other systems create tasks

## Implementation Notes

### Graph Storage
Recommend property graph database (Neo4j, TypeDB) or graph library (NetworkX) depending on scale:
- Small scale (personal): NetworkX or similar in-memory
- Medium scale (team): Embedded graph DB
- Large scale (org): Distributed graph DB

### MCP Server API Design
Should expose operations:
- CRUD for Tasks and States
- CRUD for relationships
- Query operations (next actions, projects, waiting for)
- Bulk operations (mark multiple complete, add dependencies)
- Graph traversal (subgraph, critical path)

### Data Integrity
- Enforce acyclic property on DependsOn
- Validate responsibleParty values
- Ensure isComplete tasks don't have dependencies on incomplete tasks (or handle gracefully)

### Performance Considerations
- Index on: responsibleParty, isComplete, context
- Cache boundary layer computation
- Lazy load subgraphs for visualization

## Examples

### Example 1: Simple Sequential Tasks
```
Task: "Publish blog post"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: ["Write draft", "Review draft", "Create images"]

Task: "Write draft"  
  - isComplete: true
  - responsibleParty: "me"
  
Task: "Review draft"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: ["Write draft"]
  
Task: "Create images"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@computer"]

→ Next Actions: ["Review draft", "Create images"]
→ "Publish blog post" is a Project (compound task)
```

### Example 2: External Dependencies
```
Task: "Launch feature"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: ["Code complete", "Design approved", "Marketing ready"]

Task: "Code complete"
  - isComplete: true
  - responsibleParty: "me"

Task: "Design approved"
  - isComplete: false
  - responsibleParty: "external" (Design team)
  
Task: "Marketing ready"
  - isComplete: false
  - responsibleParty: "external" (Marketing team)

→ Next Actions: [] (blocked)
→ Waiting For: ["Design approved", "Marketing ready"]
→ Once externals complete, "Launch feature" enters Next Actions
```

### Example 3: State-Based Dependencies
```
State: "Have pizza"
  - isTrue: false
  - DependsOn: "Order delivery"

Task: "Order delivery"
  - isComplete: false
  - responsibleParty: "external"

Task: "Eat dinner"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: "Have pizza"
  - context: ["@home"]

→ Waiting For: ["Order delivery"]
→ When "Order delivery" completes, "Have pizza" becomes true
→ "Eat dinner" then enters Next Actions (if @home context)
```

### Example 4: Parallel Decomposition
```
Task: "Vacation booked"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: ["Hotel reserved", "Flights booked", "Car rental arranged"]

Task: "Hotel reserved"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@computer"]
  - DependsOn: ["Research hotels"]

Task: "Flights booked"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@computer"]
  - DependsOn: ["Research flights"]

Task: "Car rental arranged"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@computer", "@phone"]

Task: "Research hotels"
  - isComplete: true

Task: "Research flights"
  - isComplete: true

→ Next Actions: ["Hotel reserved", "Flights booked", "Car rental arranged"] (all in parallel)
→ "Vacation booked" is the project (compound task)
```

### Example 5: Standalone Waiting Item (Null Source)
```
DependsOn: null -> "Toothpaste delivery"
  
Task: "Toothpaste delivery"
  - isComplete: false
  - responsibleParty: "external"

→ Waiting For: ["Toothpaste delivery"]
→ No explicit follow-up action
→ When delivery arrives, mark complete
```

### Example 6: Alternative Paths (State with ANY logic)
```
State: "Have food"
  - isTrue: false
  - DependsOn: ["Order pizza", "Cook dinner", "Get takeout"]
  - Logic: ANY (default)

Task: "Order pizza"
  - isComplete: false
  - responsibleParty: "external"
  - context: ["@phone"]

Task: "Cook dinner"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@home"]
  - DependsOn: ["Get groceries"]

Task: "Get takeout"
  - isComplete: false
  - responsibleParty: "me"
  - context: ["@car"]

Task: "Get groceries"
  - isComplete: true

Task: "Eat dinner"
  - isComplete: false
  - responsibleParty: "me"
  - DependsOn: "Have food"

→ Next Actions: ["Order pizza", "Cook dinner", "Get takeout"] 
   (pick one based on context)
→ When ANY completes, "Have food" becomes true
→ "Eat dinner" then enters Next Actions
```

## Open Questions for Implementation

1. **ANY/ALL logic for States**: MVP defaults to ANY (state true when any dependency completes). Should we support ALL logic? How to specify? Property on State node or on DependsOn edges?

2. **UNSPECIFIED dependency marker**: Should we support explicit marker that task needs more decomposition? E.g., `Task DependsOn [UNSPECIFIED]` to signal "I know this isn't complete yet"?

3. **Distance-based review filtering**: Should weekly review only show Projects/Waiting items within N hops of boundary layer? How to determine N for different review types (Projects vs Areas vs Goals)?

4. **State truth update mechanism**: When a task completes and has States depending on it, do we:
   - Automatically update state to true?
   - Require manual confirmation?
   - Semi-automatic with notification?

5. **Someday/Maybe modeling**: Context tag vs status field vs disconnected nodes?

6. **Recurring tasks**: How to model? Clone task when complete? Perpetual incomplete task with reset mechanism?

7. **Due dates**: Add to Task properties? Separate notion of "scheduled" vs "someday"?

8. **Delegation transform**: When delegating, change responsibleParty in place, or create new external task?

9. **Multi-project tasks**: Can a task contribute to multiple projects? (Task with multiple incoming DependsOn edges from different project tasks)

10. **Archive/history**: Keep completed tasks in graph forever? Archive after N days? Separate historical graph?

11. **Context hierarchy**: Should contexts be structured? (e.g., @work.computer, @work.phone)

12. **Batch capture**: How to efficiently add many related tasks at once?

13. **Error handling**: What when user creates cycle? Dangling references?

14. **Complex State logic (future)**: Support for nested ANY/ALL expressions like: `State DependsOn ANY([ALL(["A", "B"]), "C"])` meaning "(A AND B) OR C"?

## References

- Allen, David. *Getting Things Done: The Art of Stress-Free Productivity*. 2001, 2015.
- Allen, David. *Making It All Work: Winning at the Game of Work and Business of Life*. 2008.
- STRIPS Planning System (Stanford Research Institute Problem Solver)
- PDDL (Planning Domain Definition Language)
- Process Scheduler architectures in operating systems

## Versioning

- **Version**: 1.0  
- **Date**: 2025-11-01
- **Authors**: Scott (design), Claude (documentation)
- **Status**: Ready for MVP implementation
