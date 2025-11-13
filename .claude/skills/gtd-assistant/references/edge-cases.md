# Edge Cases Guide

Reference for handling ambiguous, conflicting, or unusual situations. Consult when encountering edge cases not covered in primary conversation patterns.

## Empty Results

### Empty Next Actions

**Situation:** Query returns no actionable tasks.

**Response pattern:**
> "No next actions available right now. [Explain why: all tasks have unsatisfied dependencies / all tasks require unavailable contexts / no tasks captured yet]. [Suggestion: Consider capturing new tasks / changing context availability / clarifying blocked items]."

**Examples:**
- "No next actions available—all tasks require contexts that aren't available. You might want to update your context availability or capture tasks that don't depend on specific contexts."
- "No next actions found. We haven't captured any tasks yet. Would you like to add something to your list?"

**Key:** Be helpful, not just factual. Explain why and suggest next steps.

---

### Empty Projects

**Situation:** User asks for projects but none exist.

**Response pattern:**
> "No projects found. [Clarify: Projects are tasks with dependencies]. [Suggestion: capture multi-step work if you have any]."

**Example:**
- "You don't have any projects right now. Projects are tasks with subtasks or dependencies—let me know if you have any multi-step work to capture."

---

### Empty Waiting For

**Situation:** No delegated tasks.

**Response pattern:**
> "No tasks delegated to others right now. You're handling everything yourself."

**Key:** Brief and neutral. Don't add unnecessary suggestions.

---

## Ambiguous References

### Multiple Matches

**Situation:** User references task ambiguously, multiple candidates exist.

**Response pattern:**
1. List matching options with brief context
2. Ask user to clarify
3. Don't proceed until clarification received

**Example:**
> User: "Update the report"
>
> "I found multiple tasks mentioning 'report':
> 1. Financial report (Q3 summary, waiting on data)
> 2. Status report (weekly team update, due Friday)
>
> Which one did you mean? No changes made yet."

**Key:** Always list options. Never guess which one the user meant.

---

### No Matches

**Situation:** User references task that doesn't exist.

**Response pattern:**
1. State clearly that no match was found
2. Offer to search more broadly
3. Offer to create if appropriate

**Example:**
> User: "Delete the vendor task"
>
> "I don't see a task matching 'vendor'. No changes made. Would you like me to search for similar tasks, or did you mean something else?"

**Key:** Don't apologize excessively. State facts and offer help.

---

### Unclear Pronoun Reference

**Situation:** User uses "it", "that", "this" without clear antecedent.

**Response pattern:**
1. Ask for clarification
2. Offer likely candidates if context suggests

**Example:**
> User: "Mark it complete"
>
> "Which task do you want to mark complete? [If recent context: Did you mean 'Call dentist'?]"

**Key:** Use conversation context when available, but don't over-assume.

---

## Conflicting Instructions

### Complete vs Add Subtask

**Situation:** User says task is done but wants to add more work to it.

**Response pattern:**
1. Highlight the conflict
2. Present options
3. Wait for clarification

**Example:**
> User: "Mark the proposal complete and add a subtask for final review"
>
> "I'm seeing conflicting instructions: you said it's done but also to add a subtask. Completed tasks typically don't have new subtasks added. Do you want to:
> 1. Mark it complete without adding the subtask?
> 2. Add the subtask first, then mark complete later?
> 3. Keep it incomplete with the new subtask?"

**Key:** Present clear options. Don't interpret the conflict yourself.

---

### Delete vs Update

**Situation:** User wants to both delete and modify a task.

**Response pattern:**
1. Clarify intent
2. Explain consequences

**Example:**
> User: "Delete the meeting task and change its time to 3pm"
>
> "Did you want to delete the meeting task or update its time? I can't do both—once deleted, the task is gone."

**Key:** Mutually exclusive operations need clarification.

---

## Dependency Direction Ambiguity

### Unclear Sequence

**Situation:** User describes dependency but direction is ambiguous.

**Response pattern:**
1. Present both interpretations
2. Ask for explicit confirmation

**Example:**
> User: "The research and draft are connected"
>
> "Does research depend on draft (can't research until draft is done), or does draft depend on research (can't draft until research is done)? Please confirm the direction."

**Key:** Use concrete language—"X must be done before Y"—to clarify.

---

### "Before" vs "After" Confusion

**Situation:** User says "do A before B" (sequence unclear).

**Response pattern:**
1. Interpret "before" as prerequisite
2. Confirm interpretation

**Example:**
> User: "Do the research before writing the draft"
>
> "Got it—you need to complete research before you can start the draft. I'll make 'Write draft' depend on 'Research', so research must be done first."

**Key:** "Before" usually means prerequisite. Confirm if unsure.

---

## Undefined Entities

### Undefined Context

**Situation:** User mentions context that doesn't exist.

**Response pattern:**
1. State it doesn't exist
2. Offer to create with default availability
3. Wait for confirmation

**Example:**
> User: "I'm at the makerspace now"
>
> "I don't have a context named @makerspace yet. Should I create it with isTrue=true?"

**Key:** Offer to create, but don't assume. User might have meant something else.

---

### Undefined State

**Situation:** User reports a state that hasn't been defined.

**Response pattern:**
1. Create the state based on user report
2. Set initial value from context
3. Remind user to report changes

**Example:**
> User: "The weather is good for painting now"
>
> "I'll track 'Weather is good for painting' as a manual state (currently true). Let me know when this changes."

**Key:** MANUAL states are user-reported. Create immediately based on what user says.

---

## Property Mismatches

### Task Already Complete

**Situation:** User tries to mark complete task as complete again.

**Response pattern:**
1. Note it's already complete
2. Ask if they meant something else

**Example:**
> User: "Mark 'File taxes' complete"
>
> "'File taxes' is already marked complete (done on 2025-11-01). Did you mean a different task?"

**Key:** Acknowledge current state. Don't silently no-op.

---

### Task Already Incomplete

**Situation:** User tries to reopen a task that's not complete.

**Response pattern:**
1. Note it's already incomplete
2. Confirm intent

**Example:**
> User: "Reopen the design task"
>
> "'Design homepage' is already incomplete (not marked done). Did you want to update it in some other way?"

**Key:** Clarify what "reopen" means if already incomplete.

---

## Cascade Delete Edge Cases

### Delete with Many Dependents

**Situation:** Task has many dependent tasks.

**Response pattern:**
1. List count and first few dependents
2. Emphasize impact
3. Require explicit confirmation

**Example:**
> User: "Delete 'Set up infrastructure'"
>
> "Warning: 8 tasks depend on 'Set up infrastructure'. Deleting will leave these blocked:
> - Deploy staging environment
> - Configure monitoring
> - Set up CI/CD
> ... and 5 more.
>
> Delete anyway and leave these tasks with missing dependencies?"

**Key:** Emphasize impact. Make user think before confirming.

---

### Circular Dependency Prevention

**Situation:** User tries to create circular dependency (A→B→A).

**Response pattern:**
1. Explain the issue
2. Don't create the connection

**Example:**
> User: "Make A depend on B" (when B already depends on A)
>
> "I can't create that dependency—it would create a circular loop (A→B→A). Tasks can't depend on themselves indirectly. Which dependency should I remove first?"

**Key:** Graph-memory-core may enforce this. If not, check manually.

---

## Duplicate Detection Edge Cases

### False Positive Duplicate

**Situation:** User confirms two tasks are different despite similarity.

**Response pattern:**
1. Create the new task
2. Don't argue with user

**Example:**
> User: "No, those are different—one is for the Q3 report and one is for Q4"
>
> "Got it. I'll capture the Q4 report as a separate task."

**Key:** User knows their intent better than similarity algorithms.

---

### False Negative Duplicate

**Situation:** User accidentally creates true duplicate (detection missed it).

**Response pattern:**
1. If noticed later, present both to user
2. Offer to merge or delete one

**Example:**
> "I noticed you have two very similar tasks: 'Call dentist' and 'Schedule dentist appointment'. Do you want to keep both or consolidate them?"

**Key:** Don't auto-merge without permission. Present options.

---

## Context Availability Edge Cases

### All Contexts Unavailable

**Situation:** User marks all contexts unavailable, making nothing actionable.

**Response pattern:**
1. Note the impact
2. Suggest updating availability

**Example:**
> User: "I'm not at the office, home, or phone right now"
>
> "With all contexts marked unavailable, most tasks are now blocked. When you're ready to work, let me know which context becomes available."

**Key:** Neutral tone. Don't nag.

---

### Multiple Contexts for Same Task

**Situation:** Task requires multiple contexts (e.g., atOffice AND hasLaptop).

**Response pattern:**
1. Create dependencies to both contexts
2. Explain requirement

**Example:**
> User: "Print packets at the office, need my laptop too"
>
> "Captured task with dependencies on both atOffice and hasLaptop. You'll need both available to work on this."

**Key:** Multiple context dependencies are allowed. Task is only actionable when ALL are available.

---

## Parent Completion Edge Cases

### Parent with Incomplete Dependencies

**Situation:** User tries to complete parent before all dependencies done.

**Response pattern:**
1. List remaining dependencies
2. Ask for confirmation

**Example:**
> User: "Mark the investor packet complete"
>
> "The investor packet still has 2 incomplete dependencies:
> - Draft the narrative (not done)
> - Polish the slides (not done)
>
> Do you want to mark the project complete anyway, or finish these first?"

**Key:** Present the facts. Let user decide.

---

### All Dependencies Complete, Parent Incomplete

**Situation:** All subtasks done but parent not marked complete.

**Response pattern:**
1. Note the situation
2. Offer to mark parent complete
3. Don't auto-complete

**Example:**
> User: "I finished polishing the slides" (last subtask)
>
> "Marked 'Polish slides' complete. All dependencies of 'Prepare investor packet' are now done. Do you want to mark the project complete?"

**Key:** Offer, don't presume. User might want to review first.

---

## Delegation Edge Cases

### Delegate Already-Delegated Task

**Situation:** User tries to reassign task to different person.

**Response pattern:**
1. Note current assignment
2. Update to new person

**Example:**
> User: "Actually, Alex should handle the logo designs, not Jane"
>
> "Updated: Logo designs now delegated to Alex (previously Jane)."

**Key:** Simple updates don't need permission. Just confirm change.

---

### Delegate to Self

**Situation:** User delegates task to "me".

**Response pattern:**
1. Set responsibleParty="me"
2. Exclude from Waiting For

**Example:**
> User: "I'll handle the report myself"
>
> "Updated: Report assigned to you (removed from Waiting For)."

**Key:** Tasks with responsibleParty="me" are treated as user's tasks.

---

## UNSPECIFIED Edge Cases

### Task with Both UNSPECIFIED and Real Dependencies

**Situation:** Task depends on UNSPECIFIED plus other tasks.

**Response pattern:**
1. Task remains blocked by UNSPECIFIED
2. Explain that UNSPECIFIED always blocks

**Example:**
> User: "The marketing launch depends on budget approval and... I'm not sure what else"
>
> "Captured dependencies: budget approval (concrete) and UNSPECIFIED (placeholder). The task won't be actionable until we define that missing step, even if budget approval completes."

**Key:** UNSPECIFIED always blocks, regardless of other dependencies.

---

### Removing UNSPECIFIED Dependency

**Situation:** User defines the missing step.

**Response pattern:**
1. Create new concrete dependency
2. Remove UNSPECIFIED dependency
3. Explain task may now be actionable

**Example:**
> User: "The next step for marketing launch is to draft the announcement"
>
> "Created 'Draft announcement' and made marketing launch depend on it. Removed the UNSPECIFIED blocker. Marketing launch will be actionable once the announcement is drafted."

**Key:** Removing UNSPECIFIED + adding concrete dependency unblocks the task (if no other blockers).

---

## State Update Edge Cases

### State with Logic Other Than MANUAL

**Situation:** User tries to update ANY/ALL/IMMUTABLE state (Phase 2 only).

**Response pattern:**
1. Note that only MANUAL states are supported in MVP
2. Suggest alternative

**Example:**
> User: "Update the 'All reviews approved' state"
>
> "I can only update MANUAL states in this version. If 'All reviews approved' should be tracked manually, I can create a MANUAL state. Otherwise, this will be supported in Phase 2."

**Key:** Phase 1 MVP limitation. Be clear about what's supported.

---

## General Principles

1. **Be explicit:** Don't silently no-op. Acknowledge current state.
2. **Offer alternatives:** "Can't do X, but can do Y" is better than just "can't do X."
3. **Wait for confirmation on ambiguity:** Don't guess.
4. **Present facts, let user decide:** Especially for conflicts or edge cases.
5. **Keep responses helpful:** Explain why something can't be done and what can be done instead.
