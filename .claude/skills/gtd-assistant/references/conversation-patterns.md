# Conversation Patterns Reference

This reference provides concrete examples of GTD conversational interactions. Consult this when encountering unfamiliar request patterns or when uncertain about tool usage flow.

## Pattern Structure

Each pattern shows:
1. User utterance (natural language)
2. Assistant reasoning/plan
3. Tool operations (create, query, update, delete)
4. User-facing confirmation

## Capture Patterns

### 1. Simple Task Capture

**User:** "I need to call the dentist tomorrow to schedule a cleaning."

**Response:** Captured task: Call the dentist tomorrow to schedule a cleaning. I saved it as a next action (isComplete=false).

**Tool operations:**
- `create_node` with type="Task", isComplete=false
- Content includes user's description

---

### 2. Task With Context Association

**User:** "Log a reminder to print the quarterly packets when I'm at the office."

**Plan:**
- Ensure @office context exists
- Create task
- Connect task to @office

**Tool operations:**
```
create_node({
  "type": "Context",
  "content": "Tasks that require being at the office",
  "properties": { "isAvailable": true }
})

create_node({
  "type": "Task",
  "content": "Print quarterly packets",
  "properties": { "isComplete": false }
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<task_id>",
  "to_node_id": "<context_id>"
})
```

**Response:** Captured task: Print the quarterly packets when @office is available.

---

### 3. Task With Dependency

**User:** "I need to send the board update, but only after I finish the financial summary."

**Plan:**
- Create dependent task
- Create prerequisite task (if missing)
- Connect dependent to prerequisite

**Tool operations:**
```
create_node({
  "type": "Task",
  "content": "Send the board update",
  "properties": { "isComplete": false }
})

create_node({
  "type": "Task",
  "content": "Finish the financial summary",
  "properties": { "isComplete": false }
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<board_update_id>",
  "to_node_id": "<financial_summary_id>"
})
```

**Response:** Captured task: Send the board update now depends on finishing the financial summary.

**Key:** Direction is critical—"from" depends on "to". Board update depends on summary being done first.

---

### 4. Task With UNSPECIFIED Dependency

**User:** "I'm not sure what the next step is for the marketing launch, but something needs to happen."

**Plan:**
- **FIRST: Search for existing "marketing launch" tasks**
- Check if this is a new project or existing one
- If existing, ask if they want to add UNSPECIFIED dependency to it
- If new, create task with UNSPECIFIED dependency

**Tool operations:**
```
// STEP 1: Search first!
search_content({
  "query": "marketing launch",
  "node_type": "Task",
  "limit": 10
})

// If found: Present to user and ask if same
// If not found: Create new

ensure_singleton_node({
  "type": "UNSPECIFIED",
  "content": "Placeholder for missing next step."
})

create_node({
  "type": "Task",
  "content": "Define next step for marketing launch",
  "properties": { "isComplete": false }
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<task_id>",
  "to_node_id": "<unspecified_id>"
})
```

**Response:**
- If found existing: "I found an existing 'Marketing launch campaign' project. Do you want to add an UNSPECIFIED dependency to track the missing next step?"
- If new: "Captured: Define next step for marketing launch is blocked until we clarify what that step is."

**Semantics:** Tasks depending on UNSPECIFIED are never actionable (never returned by Next Actions query).

---

### 5. Duplicate Detection

**User:** "Add a task to finalize the vendor contract."

**Plan:**
- Query for semantic duplicates
- If found, present to user for decision

**Tool operations:**
```
query_nodes({
  "type": "Task"
})
# Then semantic comparison via content
```

**Response:** I found a possible duplicate via semantic similarity: "Finalize vendor agreement" from last week. Would you like me to reuse the existing entry or capture a fresh task?

**Key:** Use semantic similarity, not exact text matching. Different phrasings can represent the same task.

---

### 6. Project With Subtasks

**User:** "I need to prepare the investor packet: gather metrics, draft the narrative, and polish the slides."

**Plan:**
- Create parent project task
- Create child tasks
- Connect parent to each child

**Tool operations:**
```
create_node({
  "type": "Task",
  "content": "Prepare the investor packet",
  "properties": { "isComplete": false }
})

create_node({
  "type": "Task",
  "content": "Gather metrics",
  "properties": { "isComplete": false }
})

create_node({
  "type": "Task",
  "content": "Draft the narrative",
  "properties": { "isComplete": false }
})

create_node({
  "type": "Task",
  "content": "Polish the slides",
  "properties": { "isComplete": false }
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<parent_id>",
  "to_node_id": "<gather_metrics_id>"
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<parent_id>",
  "to_node_id": "<draft_narrative_id>"
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<parent_id>",
  "to_node_id": "<polish_slides_id>"
})
```

**Response:** Captured: Prepare the investor packet parent project now depends on gather metrics, draft the narrative, and polish the slides.

**Key:** The three subtasks are the actionable next actions. The parent is an organizing container and should be marked complete only after all three dependencies are finished; the parent itself is not a next action.

---

### 7. Delegated Task Capture

**User:** "Log that Jane is handling the new logo design."

**Plan:**
- Search for existing task (optional)
- Create or update delegated task

**Tool operations:**
```
create_node({
  "type": "Task",
  "content": "New logo design",
  "properties": {
    "isComplete": false,
    "responsibleParty": "Jane"
  }
})
```

**Response:** Waiting For: Jane is responsible for the new logo design and it remains delegated. I'll keep an eye on it.

**Key:** Tasks with `responsibleParty` not equal to "me" appear in Waiting For query, not Next Actions.

---

### 8. MANUAL State Capture

**User:** "Track that the conference room projector is working right now."

**Plan:**
- Create or update MANUAL state

**Tool operations:**
```
create_node({
  "type": "State",
  "content": "Conference room projector is working",
  "properties": {
    "logic": "MANUAL",
    "isTrue": true
  }
})
```

**Response:** Captured state: Conference room projector is working. Let me know if this changes.

**Key:** MANUAL states are user-reported. Don't auto-update. Ask user to report when condition changes.

---

### 9. Infer Obvious Context

**User:** "Add a reminder to call the dentist."

**Plan:**
- Infer @phone context (obvious)
- Ensure @phone exists
- Create task
- Connect task to @phone

**Tool operations:**
```
create_node({
  "type": "Context",
  "content": "Tasks that require a phone",
  "properties": { "isAvailable": true }
})

create_node({
  "type": "Task",
  "content": "Call the dentist",
  "properties": { "isComplete": false }
})

create_connection({
  "type": "DependsOn",
  "from_node_id": "<task_id>",
  "to_node_id": "<phone_context_id>"
})
```

**Response:** Captured task: I inferred the @phone context so the reminder stays linked to phone availability.

**Key:** Infer obvious contexts but state the inference. User can override if wrong.

---

## Anti-Patterns: What NOT To Do

### ❌ Creating Without Searching

**User:** "Something needs to happen with the board presentation."

**WRONG:**
```
create_node({
  "type": "Task",
  "content": "Clarify board presentation next steps"
})
```

**RIGHT:**
```
// FIRST: Search
search_content({
  "query": "board presentation",
  "node_type": "Task"
})

// THEN: Based on results, either update existing or create new
```

### ❌ Asking Questions Before Querying

**User:** "What's the status of the vendor contract?"

**WRONG:** "Can you tell me more about which vendor contract?"

**RIGHT:**
```
search_content({
  "query": "vendor contract",
  "node_type": "Task"
})

// If found: Present status
// If not found: "I don't have any tasks about vendor contracts yet. Would you like to create one?"
```

### ❌ Creating New Instead of Updating Existing

**User:** "I finished the quarterly taxes."

**WRONG:**
```
create_node({
  "type": "Task",
  "content": "File quarterly taxes",
  "properties": { "isComplete": true }
})
```

**RIGHT:**
```
// FIRST: Find the existing task
search_content({
  "query": "quarterly taxes",
  "node_type": "Task"
})

// THEN: Update it
update_node({
  "node_id": "<found_id>",
  "properties": { "isComplete": true }
})
```

**Key:** Always search first. Never assume. Never create when you should update.

---

## Query Patterns

### 1. Next Actions Inquiry

**User:** "What should I work on next?"

**Plan:**
- Query incomplete tasks
- Inspect dependencies for actionability

**Tool operations:**
```
query_nodes({
  "type": "Task",
  "properties": { "isComplete": false }
})

get_connected_nodes({
  "node_id": "<task_id>",
  "direction": "out",
  "connection_type": "DependsOn"
})

# For each dependency:
# - If Task: check isComplete
# - If State: check isTrue
# - If Context: check isAvailable
# - If UNSPECIFIED: exclude task
```

**Response:**
Next actions:
- Task A (all dependencies clear)
- Task B (context available, ready to go)

**Key:** Only return tasks where ALL immediate dependencies are satisfied.

---

### 2. Projects Overview Request

**User:** "Show me my active projects."

**Plan:**
- Query outgoing DependsOn connections
- Gather dependency status

**Tool operations:**
```
query_connections({
  "type": "DependsOn"
})
# Collect unique from_node_ids → projects

get_connected_nodes({
  "node_id": "<project_id>",
  "direction": "out"
})
# Check status of dependencies
```

**Response:**
Project: Redesign website
- incomplete dependencies: 2 remaining (Finalize copydeck, QA review)

This project still has incomplete dependencies to resolve.

**Key:** Projects are tasks with outgoing dependencies. Not a separate node type.

---

### 3. Waiting For List

**User:** "Remind me what I'm waiting on from others."

**Plan:**
- Query delegated tasks

**Tool operations:**
```
query_nodes({
  "type": "Task",
  "properties": { "isComplete": false }
})
# Filter to where responsibleParty exists and != "me"
```

**Response:**
Waiting For items delegated to others:
- Vendor contract follow-up (delegated to Alex, last update 5 days ago)
- Logo design proof (delegated to Jane, awaiting review)

**Key:** Use `responsibleParty` property. Tasks without this property are assumed to be user's responsibility.

---

### 4. Context-Filtered Suggestions

**User:** "I'm at home with my laptop. What can I do?"

**Plan:**
- Detect @home and @laptop contexts
- Filter actionable tasks matching available contexts

**Tool operations:**
```
query_nodes({
  "type": "Task",
  "properties": { "isComplete": false }
})

get_connected_nodes({
  "node_id": "<task_id>",
  "direction": "out"
})
# Check context dependencies

query_nodes({
  "type": "Context",
  "properties": { "isAvailable": true }
})
```

**Response:**
Filtered next actions:
- Focus on @home work while @laptop contexts remain available.
- Capture new tasks if nothing fits these available contexts.

**Key:** Respect context availability. Tasks requiring unavailable contexts are not actionable.

---

### 5. Stuck Projects Review

**User:** "Which projects are stuck?"

**Plan:**
- Find projects
- Measure last progress timestamps

**Definition of "stuck":**
- Project (Task with outgoing DependsOn) is stuck if no completion activity on any dependency for ≥14 days
- "Completion activity" = dependency Task with `isComplete=true`; use `modified` timestamp
- If no dependencies ever completed, evaluate against project's `created` timestamp

**Tool operations:**
```
query_connections({
  "type": "DependsOn"
})
# Collect unique from_node_ids → project_ids

get_connected_nodes({
  "node_id": "<project_id>",
  "direction": "out"
})
# Get dependency IDs

get_node({ "node_id": "<dependency_id>" })
# Check isComplete and modified timestamp for each

# Compute last_completion = max(modified where isComplete=true)
# If daysSince >= 14, mark as stuck
```

**Response:**
Stuck project: Update employee handbook — no recent activity in 14+ days (last progress: 2025-10-20T15:42Z on 'Outline draft').

**Key:** Report exact IDs and timestamps from graph. Don't guess. Include ISO 8601 timestamps.

---

### 6. Specific Lookup

**User:** "Do we already have anything about renewing the security certificates?"

**Plan:**
- Search for security certificate work

**Tool operations:**
```
search_content({
  "node_type": "Task",
  "query": "security certificates"
})
```

**Response:** Found related work on renewing the security certificates and linked tasks that might help you continue.

**Key:** Use content search for text matching. Follow up with semantic similarity if exact match fails.

---

### 7. Weekly Review Snapshot

**User:** "Show me my weekly review."

**Plan:**
- Combine multiple queries
- Format according to weekly review template

**Sections:**
1. Completed this week (last 7 days, limit 20)
2. Active projects (incomplete, with dependency counts)
3. Stuck projects (no activity ≥14 days)
4. Next actions (actionable tasks, first 20)
5. Waiting for (delegated tasks, oldest first)
6. Context availability (all contexts with status)

**Tool operations:** Combine query patterns from above sections.

**Response:** Format as structured review with clear sections and counts.

---

## Update Patterns

### 1. Mark Task Complete

**User:** "I finished filing the quarterly taxes."

**Plan:**
- Search for the task
- Retrieve its details
- Mark isComplete=true
- Surface downstream impact

**Tool operations:**
```
search_content({
  "node_type": "Task",
  "query": "quarterly taxes"
})

get_node({ "node_id": "<task_id>" })

update_node({
  "node_id": "<task_id>",
  "properties": { "isComplete": true }
})

# Optional: check for tasks that depend on this one
get_connected_nodes({
  "node_id": "<task_id>",
  "direction": "in"
})
```

**Response:** Marked complete: Filing the quarterly taxes is done and the project is now unblocked.

**Key:** Check for dependent tasks that may become actionable.

---

### 2. Update Task Details

**User:** "Add a note to the press release draft that marketing requested bullet points."

**Plan:**
- Search for the task
- Fetch existing content
- Append note (preserve existing content)

**Tool operations:**
```
search_content({
  "node_type": "Task",
  "query": "press release draft"
})

get_node({ "node_id": "<task_id>" })

get_node_content({ "node_id": "<task_id>" })

update_node({
  "node_id": "<task_id>",
  "content": "<existing_content>\n\nAdded: Marketing requested bullet points."
})
```

**Response:** Added note about marketing's bullet point request; other properties unchanged.

**Key:** Always fetch existing content before updating to avoid overwriting.

---

### 3. Add Dependency to Existing Task

**User:** "Make sure we get legal approval before sending the press release."

**Plan:**
- Identify tasks (search if needed)
- Confirm dependency direction
- Create DependsOn edge

**Tool operations:**
```
# Assume tasks already exist
create_connection({
  "type": "DependsOn",
  "from_node_id": "<press_release_id>",
  "to_node_id": "<legal_approval_id>"
})
```

**Response:** Dependency added: Send press release now depends on legal approval before distribution.

**Key:** Confirm direction when ambiguous. "Before" indicates sequence.

---

### 4. Change Context Availability

**User:** "I just left the office."

**Plan:**
- Mark @office unavailable

**Tool operations:**
```
query_nodes({
  "type": "Context"
})
# Find @office

update_node({
  "node_id": "<office_context_id>",
  "properties": { "isAvailable": false }
})
```

**Response:** Next actions requiring @office will be hidden until you return.

**Key:** Context changes immediately affect Next Actions query.

---

### 5. Report MANUAL State Update

**User:** "The design review was approved."

**Plan:**
- Find or create State
- Set isTrue

**Tool operations:**
```
# Assume state exists or create it
update_node({
  "node_id": "<state_id>",
  "properties": { "isTrue": true }
})
```

**Response:** This is manual tracking — please let me know if this changes. Thanks for the update.

**Key:** MANUAL states are user-reported. Remind user to report changes.

---

### 6. Parent Completion Guardrail

**User:** "I finished the last subtask of the investor packet."

**Plan:**
- Mark subtask complete
- Check if parent has more incomplete dependencies
- If all deps complete, ASK before marking parent complete

**Tool operations:**
```
update_node({
  "node_id": "<subtask_id>",
  "properties": { "isComplete": true }
})

# Check parent dependencies
get_connected_nodes({
  "node_id": "<parent_id>",
  "direction": "out"
})
# If all deps complete: ASK USER
```

**Response:** The parent project is not automatically marked complete. Do you want me to mark the project complete?

**Key:** Never auto-complete parent projects. Always ask first.

---

## Delete Patterns

### 1. Delete With Dependency Warning

**User:** "Delete the 'gather data' task."

**Plan:**
- Find task
- Inspect connections in both directions
- Warn if dependents exist

**Tool operations:**
```
search_content({
  "node_type": "Task",
  "query": "gather data"
})

get_connected_nodes({
  "node_id": "<task_id>",
  "direction": "both"
})
# Check for incoming connections (dependents)
```

**Response:** Deletion warning: Task 'Write report' depends on 'Gather data'. Deleting will leave 'Write report' with an unsatisfied dependency. Delete anyway?

**Key:** Always warn when dependents exist. Wait for explicit confirmation.

---

### 2. Cascade Delete Confirmed

**User:** "Yes, delete it and everything that depends on it."

**Plan:**
- Confirm cascade scope
- Delete node (connections cascade automatically)

**Tool operations:**
```
# Recursive delete or explicit cascade
delete_node({
  "node_id": "<task_id>"
})
# Note: MCP auto-deletes connections, but NOT dependent nodes
# For true cascade, must manually delete dependents first
```

**Response:** Removing dependent items via cascade. Deleted.

**Key:** Be clear about what's being deleted. Confirm cascade scope explicitly.

---

## Edge Case Patterns

### 1. Invalid Delete Request

**User:** "Delete the task about the vendor."

**Response:** I don't see a task matching "vendor." No changes made. Would you like me to search for similar tasks?

**Key:** Don't assume. Offer to help find the task.

---

### 2. Empty Result Set

**User:** "What can I work on at the studio?"

**Plan:**
- Query for tasks requiring @studio context
- Result: empty

**Response:** No next actions require @studio right now. Consider capturing something new or checking if other contexts are available.

**Key:** Graceful handling of empty results. Offer constructive next steps.

---

### 3. Ambiguous Reference

**User:** "Update the report."

**Plan:**
- Search for "report"
- Find multiple matches

**Response:** I found multiple matches for 'report': 'Financial report' and 'Status report'. Please clarify which one you meant; no changes made yet.

**Key:** List options, ask for clarification. Don't guess.

---

### 4. Dependency Direction Clarification

**User:** "The research and draft are related."

**Plan:**
- Unclear which depends on which

**Response:** Does research depend on draft, or the other way around? Please confirm the direction.

**Key:** Ask when dependency direction is ambiguous. Direction matters.

---

### 5. Conflicting Updates

**User:** "Mark the proposal complete and add a subtask to it."

**Plan:**
- Conflicting: complete tasks shouldn't have new subtasks

**Response:** I'm seeing conflicting instructions: you said it's done but also to add a subtask. Do you want me to mark it complete, or add the subtask first?

**Key:** Highlight conflicts, ask for clarification before proceeding.

---

### 6. Undefined Context

**User:** "I'm at the makerspace now."

**Plan:**
- Context doesn't exist
- Offer to create

**Response:** I don't have a context named @makerspace. Should I create it with isAvailable=true?

**Key:** Offer to create, wait for confirmation. Don't assume.

---

## Inference Principles Summary

1. **Infer obvious contexts:** phone calls → @phone, office work → @office
2. **Ask when ambiguous:** "work on project" → which task?
3. **State inferences explicitly:** "I inferred @phone" lets user override
4. **Balance helpfulness with accuracy:** Don't overwhelm with questions, but don't guess critical details
5. **React to availability changes:** When context becomes available, suggest affected tasks
6. **Document duplicates carefully:** Show similarity reasoning, wait for user decision
