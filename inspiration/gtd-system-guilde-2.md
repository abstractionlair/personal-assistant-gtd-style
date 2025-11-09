# GTD: A State Machine for Personal Productivity

## Core Principle
GTD is a state machine that maintains complete knowledge of all commitments, with well-defined data structures for each state and explicit transition functions between states. Like a process scheduler, it ensures nothing is lost and every item can answer: "What is my current state and what are my possible next states?"

## State Space

### Primary States
Every item exists in exactly one of these states:
- **Uncaptured** (external world)
- **Inbox** (captured but unprocessed)
- **Next Action** (actionable, single-step, context-specific)
- **Project** (multi-step outcome requiring tracking)
- **Waiting For** (blocked on external dependency)
- **Someday/Maybe** (deferred decision)
- **Calendar** (time-specific commitment)
- **Reference** (non-actionable information)
- **Complete/Trash** (terminal states)

### State Invariants
- Projects must have ≥1 next action
- Next actions must be atomic
- Calendar only for hard commitments
- Waiting For requires clear blocker

## Data Structures

### Inbox (Input Queue)
- FIFO processing
- No filtering on input
- Multiple sources feed single logical queue
- Processing is separate operation
- Target: Zero after processing

### Next Actions (Context-Indexed Lists)
- Organized by execution context (@Computer, @Phone, @Office, @Home, @Errands, etc.)
- Each entry is atomic
- Ready to execute immediately
- No dependencies
- No orphan actions (all linked to projects or standalone)

### Projects List (Outcome Registry)
- Desired outcomes requiring >1 step
- Each has clear completion criteria
- Minimum one next action per project
- Links to support material
- Regular review required
- Acts as integrity check

### Waiting For (Blocked Process List)
- Items blocked on external party
- Format: [What] from [Who] by [When]
- Regular review to check unblocking
- Tracks process state changes
- Follow-up triggers

### Someday/Maybe (Deferred Queue)
- Long-term storage
- No commitment yet
- Periodic review (monthly/quarterly)
- Reactivation path defined
- Prevents premature commitment
- Reduces active system load

### Calendar (Time-Bound Hard Landscape)
- Strict: only scheduled commitments
- Date-specific or time-specific
- Not a task list
- Reference for daily planning
- Includes: appointments, deadlines, day-specific information

## State Transition Functions

### Capture (External → Inbox)
```
capture(item):
  inbox.append(item)
  return
```
**Implementation:**
- Capture tools always accessible
- No processing during capture
- Complete capture required
- Multiple capture points OK (physical inbox, email, voice notes, mobile app)
- Weekly mind sweep to catch uncaptured items

### Process (Inbox → Classified State)
```
process(item):
  # Step 1: Actionable?
  if not actionable:
    if reference: move to reference
    if maybe_later: move to someday/maybe
    else: trash
    return
    
  # Step 2: Multi-step?
  if multi_step:
    projects.add(item)
    # fall through to extract next_action
    
  next_action = extract_next_action(item)
  
  # Step 3: Under 2 minutes?
  if time < 2_minutes:
    execute(next_action)
    return complete
    
  # Step 4: Delegate?
  if delegatable:
    delegate(next_action)
    waiting_for.add(next_action, person)
    return
    
  # Step 5: Time-specific?
  if time_specific:
    calendar.add(next_action, datetime)
    return
    
  # Step 6: Context-specific action
  context = determine_context(next_action)
  next_actions[context].add(next_action)
```

**Implementation Notes:**
- Process top to bottom of inbox
- One item at a time
- Decision tree must complete for each item
- No items return to inbox
- Process to zero regularly

### Execute (Next Action → Complete)
**Selection criteria:**
1. Context (what can I do here?)
2. Time available (how much time do I have?)
3. Energy available (what's my mental/physical state?)
4. Priority (what has highest impact?)

**Implementation:**
- Scan context-appropriate list
- Choose based on current state
- Mark complete when done
- Check if project advances
- Generate new next action if needed
- Update project status

### Review (System Maintenance)
```
weekly_review():
  # Step 1: Garbage collection - clear inputs
  for inbox in all_inboxes:
    process(inbox.items)
    
  # Step 2: Review past
  review(previous_week_calendar)
  capture_missed_items()
  
  # Step 3: Review future
  review(upcoming_calendar)
  prepare_for_scheduled_items()
  
  # Step 4: Integrity checks
  for project in projects:
    assert has_next_action(project)
    check_progress()
    generate_next_actions()
    
  # Step 5: State updates  
  for item in waiting_for:
    if unblocked:
      reprocess(item)
    else:
      check_follow_up_needed()
      
  # Step 6: Review all lists
  review(next_actions by context)
  review(projects)
  review(waiting_for)
  review(someday_maybe)
  
  # Step 7: Future planning
  review(higher_horizons)
  align_activities()
```

## Execution Model

### Daily Operation
1. **Morning Review** (5-10 min)
   - Check calendar (hard landscape)
   - Review next actions for context
   - Identify must-dos
   - Preview day

2. **During Day**
   - Select next actions by context, time, energy, priority
   - Execute
   - Capture new inputs immediately
   - Mark completions
   - Update waiting-for when unblocked

3. **Evening** (optional, 5 min)
   - Quick inbox scan
   - Mark completions
   - Capture loose ends
   - Preview tomorrow's calendar

### Weekly Maintenance (60-120 min)
1. **Get Clear**
   - Collect all loose papers, materials
   - Process all inboxes to zero
   - Empty head with mind sweep

2. **Get Current**
   - Review action lists
   - Review previous week's calendar
   - Review upcoming calendar
   - Review waiting for
   - Review project list (all projects)
   - Review someday/maybe

3. **Get Creative**
   - Review goals and objectives
   - Identify new projects
   - Capture new ideas
   - Higher horizons alignment

### Monthly/Quarterly (as needed)
- Review Areas of Focus
- Review 1-2 year goals
- Review 3-5 year vision
- Review Purpose/Principles
- Adjust system as needed

## System Properties

### Completeness
- All commitments captured somewhere
- All states represented in system
- No orphaned items
- Clear ownership of all items
- Nothing "on your mind"

### Integrity
- Projects always have next actions
- Next actions are always atomic
- Calendar contains only hard commitments
- Waiting items have clear blockers
- Regular review maintains accuracy

### Accessibility
- Context-based retrieval
- Quick state queries
- Clear next actions visible
- Trusted system
- No mental search required

## Implementation

### Setup Phase (2-6 hours)
1. **Initialize data structures**
   - Set up inbox(es)
   - Create list system
   - Define initial contexts

2. **Collect all inputs** (mind sweep)
   - Physical spaces
   - Digital spaces
   - Mental inventory
   - Pending items
   - Future items

3. **Process inbox to zero**
   - Apply processing workflow
   - Establish all lists
   - Create initial projects
   - Define initial next actions

4. **Set contexts**
   - Based on actual work locations
   - Based on tools available
   - Based on people involved
   - Keep simple initially

### Operational Phase
1. **Capture continuously**
   - Inbox always accessible
   - No trusted memory
   - Process later, not now

2. **Process regularly**
   - Daily if possible
   - Multiple times daily ideal
   - Always to zero

3. **Review weekly**
   - Non-negotiable
   - Schedule it
   - Full protocol
   - Maintains system trust

4. **Execute by context**
   - Context-appropriate lists
   - Time/energy consideration
   - Priority awareness
   - Trust choices

5. **Maintain integrity**
   - Projects have next actions
   - Lists are current
   - System reflects reality
   - Regular pruning

### Maintenance
- **Weekly review** (required, scheduled)
- **Context refinement** (as work changes)
- **Project pruning** (remove completed/obsolete)
- **Reference organization** (keep accessible)
- **Higher horizons alignment** (monthly/quarterly)

## Key Design Patterns

### Two-Minute Rule
**Concept:** If it takes less than 2 minutes, do it now rather than track it.

**Rationale:**
- Reduces state tracking overhead
- Immediate execution when possible
- Prevents queue buildup
- Overhead of tracking exceeds execution cost

**Implementation:**
- Apply during processing
- Rough estimate sufficient
- Err toward action
- Builds momentum

### Context Separation
**Concept:** Organize actions by execution context, not priority or project.

**Rationale:**
- Enables efficient filtering
- Reduces decision overhead
- Matches execution capability
- Natural parallelism
- Pre-filters impossible actions

**Implementation:**
- Start with obvious contexts
- Based on location, tools, people
- Not too granular initially
- Refine through use
- Common contexts: @Computer, @Phone, @Office, @Home, @Errands, @Agenda[Person]

### Project Tracking
**Concept:** Separate registry of multi-step outcomes with required next actions.

**Rationale:**
- Ensures forward progress
- Prevents orphan actions
- Maintains completion state
- Links outcomes to actions
- Provides review structure

**Implementation:**
- Clear outcome definition
- Always has ≥1 next action
- Regular review
- Link to support material
- Mark complete when outcome achieved

### Waiting For
**Concept:** Explicit tracking of items blocked on others.

**Rationale:**
- Explicit dependency tracking
- Blocked state management
- Follow-up triggers
- External process monitoring
- Prevents dropped balls

**Implementation:**
- Format: What/Who/When
- Regular review
- Follow-up actions
- Clear handoff
- Update when unblocked

### Inbox Zero
**Concept:** Process all inputs to classified states regularly.

**Rationale:**
- Maintains system currency
- Prevents backlog
- Ensures nothing lost
- Builds trust
- Forces decisions

**Implementation:**
- Process regularly
- Use decision tree
- No items return to inbox
- Target: Zero
- Multiple inboxes OK if consolidated

## System Failure Modes

### Incomplete Capture
**Symptoms:**
- Things "pop into mind"
- Missed commitments
- Stress about forgetting
- Mental rehearsal

**Causes:**
- No capture tool available
- Not capturing everything
- Trusting memory
- Incomplete mind sweeps

**Remediation:**
- Always-accessible capture
- Capture everything policy
- Regular mind sweeps
- Build capture habit

### Processing Breakdown
**Symptoms:**
- Growing inbox
- Unclear next actions
- Can't find things
- System distrust

**Causes:**
- Irregular processing
- Incomplete processing
- Skipping decision tree
- Items returned to inbox

**Remediation:**
- Schedule processing time
- Apply full workflow
- Process to zero
- Never return to inbox

### Review Neglect
**Symptoms:**
- Stale projects
- Orphan next actions
- Stuck waiting items
- System doesn't reflect reality

**Causes:**
- Skipped weekly reviews
- Incomplete reviews
- No review schedule
- Review takes too long

**Remediation:**
- Schedule weekly review
- Full review protocol
- Simplify if needed
- Non-negotiable commitment

### Action Ambiguity
**Symptoms:**
- Resistance to actions
- Procrastination
- Can't start
- Unclear what to do

**Causes:**
- Non-atomic actions
- Unclear context
- Missing dependencies
- Vague descriptions

**Remediation:**
- Break down actions
- Clarify contexts
- Identify blockers
- Concrete verb + object

### Project Stagnation
**Symptoms:**
- Projects not advancing
- No next actions
- Perpetual "thinking about"
- Lost momentum

**Causes:**
- No next action defined
- Next action not atomic
- Dependencies unclear
- Project not reviewed

**Remediation:**
- Always define next action
- Make actions atomic
- Clear dependencies
- Regular project review

## Performance Characteristics

### Strengths
- **Complete state tracking:** Nothing falls through cracks
- **Clear decision making:** Context/time/energy framework
- **Reliable retrieval:** Context-indexed access
- **Scalable organization:** Handles increasing complexity
- **Reduced mental load:** System holds state
- **Trusted system:** Regular review maintains trust

### Trade-offs
- **Processing overhead:** Explicit classification required
- **Maintenance requirements:** Weekly review essential
- **Initial setup cost:** Requires upfront time investment
- **Structural rigidity:** Pre-defined lists and workflow
- **Learning curve:** Must internalize workflow
- **Tool dependency:** Requires reliable system

### Optimization Opportunities
- **Context granularity:** Adjust based on actual work patterns
- **Processing frequency:** More frequent = smaller batches
- **Review depth:** Adjust thoroughness based on needs
- **Tool selection:** Digital vs analog, specific apps
- **Workflow customization:** Adapt while maintaining principles
- **Reference system:** Optimize for retrieval patterns

## Comparison with Bullet Journal

### Structural Differences
- **GTD:** Fixed state machine with pre-defined lists
- **BuJo:** Flexible state storage with user-defined collections

### Capture Approach
- **GTD:** Separate capture and processing phases (inbox → lists)
- **BuJo:** Integrated rapid logging (directly into daily log)

### Organization Principle
- **GTD:** Context-based (where/how/with what can I do this?)
- **BuJo:** Primarily temporal (when should/might I do this?)

### Project Handling
- **GTD:** Strict definition, separate list, required next action
- **BuJo:** Marked items (⊙), Projects collection, flexible tracking

### State Transitions
- **GTD:** Processing workflow with explicit decision tree
- **BuJo:** Migration-based evolution through daily/monthly review

### Review Frequency
- **GTD:** Weekly review required with specific protocol
- **BuJo:** Daily migration + monthly review, more flexible structure

### Time Dimension
- **GTD:** Calendar separate, contexts primary, time secondary
- **BuJo:** Temporal organization primary (daily/monthly/future logs)

### System Trust
- **GTD:** Built through processing rigor and weekly review
- **BuJo:** Built through regular migration and visible history

### Implementation Medium
- **GTD:** Medium-agnostic (works equally well digital or analog)
- **BuJo:** Designed for analog (pen and paper), though can be adapted

### Learning Curve
- **GTD:** Steeper initially (must learn workflow)
- **BuJo:** Gentler start, complexity added as needed

### Customization
- **GTD:** Principles fixed, tools flexible
- **BuJo:** Core simple, extensive customization expected

**Both systems share:**
- Complete state tracking
- Regular review requirements
- Clear processes for capture and organization
- Support for projects and tasks
- Waiting-for/blocked item tracking
- Trusted system as goal

**Key Insight:** GTD is a prescribed state machine optimized for context-based action selection. BuJo is a flexible framework optimized for temporal organization with migration-based state management. Both achieve reliable personal productivity systems through different architectural approaches.