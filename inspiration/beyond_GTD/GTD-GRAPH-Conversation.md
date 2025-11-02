We are working on a graph based memory MCP server and prompts/context/Claude Skills to allow you to manage a GTD system for me. We are at the stage where we will develop on ontology for nodes like Actions and Projects as well as connections like NextAction. A couple of things are now giving me pause. First is what on paper would be my Waiting On list. Can you remind me of what David Allen wrote in both the major books about things that I am waiting for?Synthesized GTD waiting-for concepts for ontology design.The user is asking about David Allen's GTD (Getting Things Done) methodology, specifically about the "Waiting For" list as described in his books. They're working on a graph-based memory MCP server for managing a GTD system and want to understand how to properly model "Waiting For" items.
The user has explicitly asked me to be careful about not reproducing copyrighted material, which is good - they're aware of the constraints. I should provide a helpful summary of the concepts from my knowledge of GTD without quoting directly from the books.
From my knowledge of GTD:
The "Waiting For" list is one of the core lists/categories in the GTD system. It tracks:

Things you've delegated to others
Things you're expecting from others
Items where the next action depends on someone else
Things you've ordered or requested

Key aspects Allen discusses:

It's a tracking mechanism for delegated items and external dependencies
Should be reviewed regularly (weekly review)
Each item should have enough detail to know what you're waiting for and from whom
May need reminders or follow-up actions
Related to the concept of tracking "open loops" that depend on others

The main books are:

"Getting Things Done" (original and revised editions)
"Making It All Work"

I should provide a helpful conceptual summary without reproducing text from the books. I should focus on the functional aspects that would help with their ontology design.I can help you understand the "Waiting For" concept in GTD without reproducing copyrighted text from the books.
In David Allen's GTD methodology, the Waiting For list is one of the essential tracking categories. Here are the key functional concepts:
Core Purpose:

Tracks items where you've delegated something to someone else
Records things you're expecting to receive (deliverables, information, responses)
Captures external dependencies where the next action isn't yours

Key Characteristics:

Each entry should identify what you're waiting for AND who you're waiting on
Often includes a date when you initiated the request
These are "open loops" you want to close but can't act on directly yourself
Should be reviewed regularly (weekly review is critical) to determine if follow-up is needed

Relationship to Actions:

A Waiting For item might generate a follow-up action if enough time passes
When you delegate an action, it typically moves from your action list to Waiting For
When the waited-for item arrives, it often triggers new next actions

For Your Ontology Design:
This suggests you might want:

A WaitingFor node type with properties like: whatExpected, fromWhom, dateDelegated, context
Connections to Person or Contact nodes
Possible connection to the original Action or Project that generated the dependency
A flag or connection type for follow-up actions that get triggered if too much time passes
Links back to the Project the waiting item supports

Does this help clarify how to model these relationships in your graph structure?RetrySMIt agrees with my recollection. But in the documents we (it did include you, but in Claude Code rather than this chat interface) wrote we went in a slightly different direction I am now questioning. And I don't quite remember why but I have a guess. For projects and actions we ended up with two node types, Projects and Actions and two (IIRC) connections a DependsOn and a NextAction. (Multiple connections are allowed.) Is it clear how those would be used? I think in analogy we have WaitingFor as a _connection_. And there is s sense to that. But then what is on the each side of the connection? In theory, everything I am waiting for is connected to some action I would take upon the event coming to pass, otherwise why would I be waiting for it. But I might add to the list that I am waiting for a delivery of toothpaste and I won't explicitly have an Action for brushing my teeth. And on the other side, I guess you could argue that I sm waiting on an Action of some kind, but it isn't one for me to take and that maybe is such a large difference ss to warrant a different type.Show moreWeighed whether WaitingFor belongs as connection or node type.18sThis is a really interesting ontological question. Let me think through what Scott is describing:

They have Projects and Actions as node types
They have DependsOn and NextAction as connection types
They're treating WaitingFor as a CONNECTION rather than a node type

And now the question is: what are the two ends of a WaitingFor connection?
Scott's key insight is important: "everything I am waiting for is connected to some action I would take upon the event coming to pass, otherwise why would I be waiting for it."
But then the toothpaste example complicates this - he's waiting for toothpaste delivery, but doesn't have an explicit "brush teeth" Action node because that's routine maintenance.
And on the "waiting on" side - he's waiting on an Action of sorts, but it's not HIS action to take. It's someone else's action.
Let me think about the design options:
Option 1: WaitingFor as a connection between two Actions

One end: The action you'll take when the thing arrives
Other end: ??? This is where it breaks down. It's not YOUR action that you're waiting on.

Option 2: WaitingFor as a connection from an Action to... something else

Could be to a Person node (waiting on Bob to send report)
Could be to some kind of Event or Milestone node (waiting for package delivery)
Could be to an ExternalAction node (someone else's action)

Option 3: WaitingFor as a node type after all

Properties: what I'm waiting for, who from, date initiated
Can have connections TO it (from Actions or Projects that depend on it)
Can have connections FROM it (to Actions that will be triggered when it arrives)
Can have connection indicating who you're waiting on

The toothpaste example suggests that sometimes the "action you'll take" is implicit or routine, so requiring an explicit Action node on one end of the WaitingFor connection might be overly burdensome.
The core dilemma centers on whether waiting is fundamentally a relationship or an independent entity. Traditional productivity methods treat it as a collection of items, suggesting a node might better capture its essence. The complexity arises from the implicit connections and routine actions that don't neatly fit into a pure relationship model.
I'm exploring potential node properties that could represent waiting states comprehensively, considering how dependencies and triggers might be mapped within this conceptual framework.You've identified a real ontological tension here. Let me think through this with you:
How DependsOn/NextAction connections work (as I understand it):

Action1 --NextAction--> Action2 means Action2 is the next action after Action1 completes
Action/Project --DependsOn--> Action/Project captures prerequisite relationships

The WaitingFor-as-connection problem:
If WaitingFor is a connection, you need two nodes. The options seem to be:

MyAction --WaitingFor--> SomeoneElsesAction

But "SomeoneElsesAction" isn't really an Action in your system (it's not something YOU can mark complete or schedule)


MyAction --WaitingFor--> Person/Contact

But this loses the specificity of WHAT you're waiting for


MyAction --WaitingFor--> Event/Delivery/Thing

Now you need another node type anyway



The toothpaste problem is revealing:
You're waiting for toothpaste delivery, but there's no explicit "brush teeth" Action node because it's routine. So what would the WaitingFor connection attach to on "your" side? Maybe nothing explicit, which suggests WaitingFor needs to be self-sufficient.
My suspicion about why you made it a connection:
Perhaps to avoid duplication? In GTD, when you delegate an Action, it becomes a WaitingFor. So maybe the thinking was: keep one Action node, but add a WaitingFor connection to represent its delegated state?
Counter-argument for WaitingFor as a node type:

It naturally contains the data: what I'm waiting for, from whom, since when
Can have multiple connections: to Projects (blocks), to Actions (triggers), to Contacts (responsible party)
Handles edge cases like toothpaste (standalone waiting items)
More closely mirrors Allen's "list of items"

Question: What does your Action node become when you delegate it? Does it get deleted? Marked complete? Or stay as-is with a WaitingFor connection added?RetrySMI was thinking that NextAction would connect Project to Action. Good question about delegating. So two ways forward I can think of. 1) It remains an Action but they now have a field identify the actor. 2) We create a type for ActionByOthers or ExternalAction or ExternalEvent. I lean towards the latter so that we don't need to read the content of every Action to decide which are mine. In which case WaitingFor as a connection makes sense. <New Paragraph> Note: this may be a good time for you to search our conversation history for one in which I snslogized GTD to an OS process scheduler.1 stepRelevant chats2 resultsSelect Viewing GTD as an OS Process SchedulerViewing GTD as an OS Process SchedulerSelect Long-term memory for AI coachingLong-term memory for AI coachingRetrieved GTD-OS analogy and connected external action modeling to process states.Perfect! I found the conversation where Scott discussed GTD as an OS process scheduler. This is very relevant to the current discussion about how to model Actions, WaitingFor items, and the distinction between actions you take versus external events/actions by others.
Key insights from that conversation:

Scott views GTD as maintaining state of what needs doing (like process states: ready, running, blocked, etc.)
He discussed how different GTD lists map to process states
The analogy extended to distributed systems for higher-level horizons
The key is maintaining complete state, clear categorization, and well-defined processes

Now, relating this back to the current question about ExternalAction/ExternalEvent nodes:

In an OS, some processes are waiting on I/O or other external events
A process can be in "blocked" state waiting for something
Similarly, a WaitingFor could be modeled as a connection FROM an Action/Project TO an ExternalAction/ExternalEvent
This preserves the type distinction without needing to check content
It mirrors the OS concept of blocking on external events

Let me respond with this connection.Excellent find! That conversation is highly relevant. Let me connect it to your current ontology question.
From the OS scheduler analogy:

Process states include blocked - waiting on I/O or other external events
The scheduler maintains state about what each process is waiting for
External events (interrupts) trigger state transitions

Applied to your WaitingFor ontology:
Your instinct for ExternalAction or ExternalEvent node types makes perfect sense through this lens:
MyAction --WaitingFor--> ExternalAction/ExternalEvent
```

This mirrors the OS concept of:
- Your Action is in a "blocked" state
- It's waiting on an external event/action that's not under your direct control
- The external entity has clear identity (who/what is responsible)

**The toothpaste case specifically:**
```
(no Action needed) --WaitingFor--> ExternalEvent[type="delivery", item="toothpaste"]
Actually, maybe there IS an implicit Action on your side that only becomes explicit when the delivery arrives: "Put away toothpaste." But since that's trivial/obvious, you don't need to model it explicitly. The WaitingFor connection can optionally have a "from" node, or float without one.
State transitions in this model:

When you delegate an Action → Create ExternalAction node, add WaitingFor connection, possibly mark your Action as blocked/complete
When external event completes → Remove WaitingFor connection, potentially trigger new NextAction
When too much time passes → Generate follow-up Action

Does this preserve your "complete state" requirement?

✓ Type is explicit (ExternalAction vs Action)
✓ Can scan for "what am I waiting for" without reading content
✓ Clear what's under your control vs external
✓ Natural place for metadata: delegated-to-whom, since-when

Thoughts?RetrySMYes I think that's the way forward on this question (but it brought up new ones). Now the question of whether the connections are between action-like objects or an action-like and a Project object is on my mind. I think there's a shallow version and then a deep one which might make me rethink more. Let's start at the shallow end. With basically the existing design, what should the end points of the connectors be?Mapped valid connection endpoints across three relationship types.25sLet me think about the existing design as Scott described it:
Node types:

Project
Action
ExternalAction (or ExternalEvent - we just decided on this)

Connection types:

NextAction
DependsOn
WaitingFor (we just decided on this)

Now the question is: what are the valid endpoints for each connection type?
Let me think through each connection type:
NextAction:
Scott said "I was thinking that NextAction would connect Project to Action."
So: Project --NextAction--> Action
This makes sense - a Project has a next action that moves it forward.
But could there be:

Action --NextAction--> Action? (one action leads to another in sequence)
Project --NextAction--> ExternalAction? (the next thing to happen is external)

DependsOn:
This is about prerequisites. Could be:

Action --DependsOn--> Action (this action can't happen until that one completes)
Project --DependsOn--> Project (this project can't start until that one completes)
Action --DependsOn--> Project (this action can't happen until that project completes)
Project --DependsOn--> Action (this project can't start until that action completes)
Action --DependsOn--> ExternalAction (this action waits on external)
Project --DependsOn--> ExternalAction (this project waits on external)

WaitingFor:
We just decided this makes sense as:

Action --WaitingFor--> ExternalAction (I'm waiting to do this action until the external thing happens)
Could also be: Project --WaitingFor--> ExternalAction (the project is blocked waiting on this)
Or even: (nothing) --WaitingFor--> ExternalAction (I'm tracking something I'm waiting for that doesn't connect to an explicit action)

Actually, thinking about this more carefully:
In GTD (Getting Things Done) methodology, projects and actions have specific characteristics. A project encompasses multiple action steps, with each action representing a discrete, concrete task. The connection between projects and actions helps map out the progression of work, showing how individual steps contribute to larger outcomes.
The key consideration is how actions relate to each other - whether they form a linear sequence or represent distinct milestones within a project's lifecycle. This nuanced approach allows for flexible tracking of complex workflows.
When examining action relationships, there are interesting distinctions between structural dependencies. Some connections represent static prerequisites, while others capture dynamic tracking states. The goal is to create a system that accurately reflects the real-world complexity of task management, balancing logical sequencing with practical tracking mechanisms.
The design explores different relationship types between actions and projects, seeking to capture both the strategic overview and tactical details of work progression.
Key relationship types include NextAction, which primarily connects projects to actions, and DependsOn, which defines prerequisite conditions across various entities. WaitingFor emerges as a potentially nuanced tracking mechanism with specific use cases, particularly around external dependencies.
The proposed graph system allows for flexible yet structured representation of task interdependencies, enabling more sophisticated workflow modeling beyond simple linear progression.Let me think through the valid endpoints for each connection type with your current design:
NextAction:

Project --NextAction--> Action ✓ (you mentioned this - the next concrete step for a project)
Project --NextAction--> ExternalAction ? (if the next thing is external - waiting for something before you can act)
Action --NextAction--> Action ? (sequenced actions, though this might be implicit through parent Project)

DependsOn:
This feels like it should be quite flexible for expressing prerequisites:

Action --DependsOn--> Action ? (can't start this until that's done)
Action --DependsOn--> ExternalAction ? (can't start until external event occurs)
Action --DependsOn--> Project ? (can't do this action until whole project completes)
Project --DependsOn--> Project ? (can't start this until that's done)
Project --DependsOn--> ExternalAction ? (project blocked on external)

WaitingFor:

Action --WaitingFor--> ExternalAction ✓ (your action is blocked, waiting on external)
Project --WaitingFor--> ExternalAction ? (whole project blocked on external)
null --WaitingFor--> ExternalAction ? (tracking something you're waiting for, like toothpaste, that doesn't have an explicit action on your side)

Questions for you:

Should NextAction only go from Projects, or can Actions have NextAction too (chaining)?
Is WaitingFor distinct from DependsOn, or is WaitingFor just "DependsOn an ExternalAction that's on my review list"?
For the toothpaste case - do you want to allow a WaitingFor with no source node, or should there always be at least a Project it relates to?
RetrySM1) I think the ethos of GTD has "Next Action" as inherently about Projects, where Project is _defined_ as anything you commit to which takes more than one step/action. 2) I think that once we've decided that waiting is modeled as a connection and that we distinguish Action and ExternalAction that DependsOn covers both cases. It also covers IsBlockedBy or Blocks which crept in at some point. 3) Yes, I think one side should be allowed to be null. Or maybe there's an explicit placeholder like ObviousAction, DefaultAction, or ImplicitAction? Or ImplicitProject?Reconciled GTD principles with graph modeling, weighing null endpoints against placeholder node types.18sThis is good clarification. Let me work through this:

NextAction is Project → Action (or ExternalAction). This makes sense with GTD's definition that a project is multi-step. So NextAction is really "the next step to advance this project."
DependsOn subsumes both blocking relationships AND WaitingFor. So we might not need WaitingFor as a separate connection type. DependsOn can connect:

Action --DependsOn--> ExternalAction (I'm waiting for this)
Action --DependsOn--> Action (prerequisite)
Project --DependsOn--> ExternalAction
Project --DependsOn--> Project
Etc.


For the toothpaste case - Scott is thinking about whether to allow null endpoints or have a placeholder node type.

Let me think about the placeholder options:

ImplicitAction - something obvious you'll do, not worth tracking explicitly
ImplicitProject - a ongoing concern, like "Personal Care"
DefaultAction - similar to implicit
ObviousAction - similar to implicit

Actually, I think there's a deeper modeling question here. In GTD terms:

Some ExternalActions might relate to explicit Projects/Actions you're tracking
Some ExternalActions might relate to Areas of Responsibility or ongoing concerns that aren't "Projects" per se
Some ExternalActions might be truly standalone (toothpaste delivery)

For the toothpaste: it's part of your general "Personal Care" or "Household Management" but that's not a Project in the GTD sense. It's more like an Area of Focus.
So maybe the placeholder should be something like:

Area or AreaOfFocus node type (from GTD's horizons of focus at 20,000 ft)
Or RoutineConcern
Or just allow null

The advantage of a placeholder node type is:
I can attach multiple ExternalActions to the same concern, creating a clear way to query related activities. This approach provides explicit structure for tracking interconnected tasks within broader life areas. The graph becomes more meaningful, allowing nuanced connections between external actions and underlying organizational frameworks.
The null approach offers simplicity, reducing system complexity. However, the placeholder method provides richer context and querying capabilities, potentially outweighing the minimal overhead of creating additional node types.Great clarifications. Let me work through the implications:
1. NextAction scope:

Project --NextAction--> Action ✓
Project --NextAction--> ExternalAction ✓
No Action-to-Action NextAction (that's implicit through their shared Project)

2. Consolidating DependsOn:
So we can eliminate WaitingFor as a separate connection type. DependsOn handles all blocking relationships:

Action --DependsOn--> ExternalAction (what used to be "waiting for")
Action --DependsOn--> Action (prerequisite)
Project --DependsOn--> ExternalAction
Project --DependsOn--> Project

The semantic difference between "Action depends on Action" versus "Action depends on ExternalAction" is encoded in the node types, not the connection type. Clean.
3. The placeholder question:
For toothpaste, the options:
null --DependsOn--> ExternalAction["Toothpaste delivery"]
```
vs
```
ImplicitAction/Area/RoutineConcern --DependsOn--> ExternalAction["Toothpaste delivery"]
Thinking through the placeholder approach:

Could be Area (from GTD's Areas of Responsibility at 20,000 ft - "Health", "Household", "Finances")
Could be RoutineConcern or OngoingArea
Could be ImplicitProject (things that are project-like but too routine to formally track)

Advantages of placeholder node:

Can group related ExternalActions: all household deliveries under "Household" area
Can query: "What am I waiting for regarding work vs personal?"
Maintains graph structural integrity (no dangling edges)
Fits your preference for explicit types

Advantage of null:

Simpler - fewer nodes to maintain
Acknowledges some things truly are standalone

My instinct: Given your systems thinking and the OS scheduler analogy, I'd lean toward Area nodes. It maps to GTD's horizons and provides a clean bucket for "things I care about but aren't Projects." Thoughts?RetrySMIn some sense, "Area" nodes are advanced GTD. As-in you often won't have them when starting a system. So I don't want to require them. Let's say that we go with null for an MVP. But this is making me think of the deeper questions again. Are we set with the shallow solution?Interrogated whether external actions constitute type or state distinction.23sGood question. Let me think about what we've settled on for the "shallow" solution:
Node types:

Project
Action
ExternalAction

Connection types:

NextAction (Project -> Action/ExternalAction)
DependsOn (covers all blocking/prerequisite relationships)

What this handles:

Projects that need actions
Actions that block other actions
External dependencies
Null source for standalone waiting items

What might make us rethink this (the "deep" questions):

The GTD Review Lists perspective: In GTD, you have:

Projects list (reviewed weekly)
Next Actions by context (reviewed constantly)
Waiting For list (reviewed weekly)
Someday/Maybe (reviewed less frequently)

In our model, how do you generate the "Waiting For" review list? You'd query: "Show me all ExternalAction nodes that are DependsOn targets." But that's indirect.
The state vs. type question:

Is "ExternalAction" really a different TYPE than Action, or is it the same type with a different STATE?
In OS terms: a blocked process is still a process, just in blocked state
Similarly, a delegated action is still an action, just with state="delegated" and delegated_to="person"


The duplicate information problem:

If I delegate "Write report" to Bob, do I:
a) Keep my Action["Write report"], add DependsOn to ExternalAction["Bob writes report"]?
b) Transform Action into ExternalAction?
c) Keep Action but mark it as delegated/external?


The GTD processing question:

When processing inbox: "Is it actionable? Yes. Is it multi-step? No, it's single action. Can I do it? No, Bob should."
Do I create an Action or ExternalAction? Or does it start as Action and become External when delegated?



I'm wrestling with the complexity of representing external work. The system needs to capture the nuanced ways actions can be delegated or blocked, without becoming overly complicated. The key challenge is maintaining clarity while representing the different states and dependencies of actions.
The implicit hierarchy raises interesting questions about how we represent work that isn't directly under my control. External actions might appear atomic from my perspective, but they could be complex processes for the person responsible. This suggests we need a flexible model that can handle different levels of granularity depending on the viewer's context.
Queries become critical in making this system useful. I need to be able to quickly see my next actions, waiting items, and overall project progress without getting lost in the complexity of the underlying data model.
The fundamental design questions center on whether external work should be a type or a state, and how delegation fundamentally transforms an action's nature. The OS scheduler analogy is particularly compelling - it suggests that being "blocked" is a dynamic state, not a fixed categorization.Good instinct to pause. Let me articulate what I think the "deep" questions are:
1. Type vs. State:
In the OS scheduler analogy, a process blocked on I/O is still a process - it's just in a different state (blocked vs. ready vs. running).
Should we be thinking:

Action (type) with state = {mine, delegated, external_event}
Rather than separate Action and ExternalAction types?

2. The Delegation Transform:
When I delegate "Write report" to Bob:

Current model: Create new ExternalAction["Bob writes report"], link via DependsOn
Alternative: Keep same Action node, change owner/state field
GTD perspective: It leaves my Actions list and goes to Waiting For list

How should the graph transform when delegation happens?
3. Review List Generation:
GTD has these as first-class review surfaces:

Next Actions (by context)
Projects (all projects reviewed weekly)
Waiting For (all delegated/external reviewed weekly)
Someday/Maybe

In our model:

"Next Actions" = query for Actions that are NextAction targets with no blocking dependencies
"Waiting For" = query for... all ExternalActions? All DependsOn targets that are External?

Is the structure naturally supporting the review workflows?
4. What IS an ExternalAction ontologically?

Is it an action someone else will take? (But they might have their own project for it)
Is it an event I'm waiting for? (Like toothpaste delivery - nobody's "action")
Is it just "an outcome I need that I can't directly make happen"?

The fundamental tension: We're building a graph but GTD is organized around lists for different review contexts. Should the graph structure directly reflect those lists, or should the lists be derived queries?
What's your intuition on which of these feels most urgent to resolve?RetrySM1) I'd rather not have to look inside each object to figure out the states. If we had a type hierarchy I'd agree they shared a parent type. 2) Same as 1. 3) For waiting list reciew, all DependsOn targets with ExternalAction is correct I think. 4) Outcome is probably the best choice (deep end calling again). These aren't _mine_ so don't need the fine-grained typing that my stuff needs. To a large extent I should consider how the state I need to exist is brought about an implementation detail. <New Paragraph> I think the lists should be derived.2 / 2Reconciled structural typing with outcome-focused modeling approach.16sThis is really good clarification. Let me process what Scott is saying:

He wants types to be explicit/structural, not internal state. Fair - that's consistent with his systems thinking. In database terms, he wants normalized tables, not a single table with a type discriminator field.
Same reasoning - keep the types separate for clarity.
Good - so "Waiting For" review = query for all nodes that have incoming DependsOn connections where the target is ExternalAction.
This is the deep insight: ExternalAction is really about an outcome I need. I don't need to model the details of how it happens. If I delegate "Write report" to Bob, I don't need to know if Bob considers it a Project or an Action or if he breaks it into substeps. I just need to know "Report written by Bob" is the outcome I'm waiting for.

So ExternalAction might better be called ExternalOutcome or just Outcome?
And the shift is: I don't model OTHER people's action systems. I just model outcomes I depend on that aren't directly under my control.
The lists should be derived - that's clean. The graph is the source of truth, and we query it to generate the various review contexts.
So for shallow design:

Project (multi-step commitments)
Action (single steps I can take)
ExternalAction/ExternalOutcome (outcomes I need but can't directly cause)
Area (optional, for grouping)

Connections:

NextAction: Project --> Action or ExternalAction
DependsOn: (Action or Project) --> (Action or Project or ExternalAction)

Null allowed on source side of DependsOn for things like toothpaste.
Lists derived via queries:

Next Actions: Find all Actions that are NextAction targets and have no blocking DependsOn (or only satisfied DependsOn)
Waiting For: Find all ExternalActions (or find all DependsOn targets that are ExternalActions)
Projects: All Project nodes
Context-based lists: Filter Actions by context property

I sense Scott is exploring a more abstract conceptual framework. His emphasis on outcomes versus implementation details hints at a deeper modeling approach that transcends traditional task management systems.
The core insight seems to be separating what needs to happen from how it happens, creating a more flexible and outcome-oriented system. This approach allows for greater adaptability and focuses on the essential goals rather than getting lost in procedural details.Good, this clarifies a lot. Your point about "outcome" vs. implementation detail is key.
Shallow design summary:

Node types: Project, Action, ExternalAction (might rename to Outcome/ExternalOutcome?)
Connections: NextAction (Project → Action|ExternalAction), DependsOn ((Action|Project|null) → (Action|Project|ExternalAction))
Lists are derived queries:

Next Actions = Actions that are NextAction targets + no unsatisfied DependsOn
Waiting For = ExternalActions (or nodes with incoming DependsOn that are ExternalActions)
Projects = All Project nodes
By Context = Filter Actions by context attribute



This should work as an MVP.
But the "deep end" beckons when you say:

"These aren't mine so don't need the fine-grained typing that my stuff needs. To a large extent I should consider how the state I need to exist is brought about an implementation detail."

This makes me think:

Maybe Project and Action are just two types from a more general "commitment/outcome" hierarchy?
Projects are multi-step outcomes where you control/track the steps
Actions are single-step outcomes where you do the step
ExternalActions are outcomes where you DON'T control the implementation

Or put differently: Everything in GTD is tracking outcomes you're committed to, with different levels of control and decomposition.
Is that the direction you're heading? Do we need a more fundamental "Outcome" or "Commitment" abstraction?RetrySMTwo related points exemplify my misgivings. 1) As you alluded to, Projects and Actions may not be a natural division. GTD makes a point of saying a Project is defined by needing more than one Action. So is an Action just a Project with one step? Going the other way, large projects, in the conventional usage of the word, tend to have sub-projects, sub-sub-projects, ... so Projects are more naturally organized as a graph than a list. 2) Actions don't really, directly depend on other actions but on states of the world which may have been cause by actions. E.g. while we might say "eat dinner" depends on "pizza delivery" it is more precise to say "eat dinner" depends on "have pizza" which is brought about by "pizza delivery". Or in a software development workflow/SDLC where we might say one task depends on another it usually depends on an artifact (broadly defined) of another task.Reconciled hierarchical task structures with state-based dependency models.16sThis is excellent. Scott is identifying that the real ontology should be based on:

State-based dependencies, not action-based dependencies: Actions don't depend on other actions, they depend on states of the world (preconditions). Actions are just one way to achieve those states.
Projects are just composite actions: The only real difference between a Project and an Action in GTD terms is that Projects decompose into multiple steps. This suggests a hierarchical/recursive structure rather than two separate types.

Let me think through what this implies:
State-based dependency model:

Actions have preconditions (states that must be true)
Actions have postconditions (states they bring about)
"Eat dinner" depends on state "pizza is here"
"Pizza delivery" (external action) achieves state "pizza is here"
"Pick up pizza" (my action) also achieves state "pizza is here"

This is much more like how workflow systems, build systems (make/bazel), and planning systems (STRIPS, PDDL) work.
Hierarchical action model:

Everything is a "Commitment" or "Outcome" or "Task"
Some are atomic (leaf nodes = GTD Actions)
Some are composite (internal nodes = GTD Projects)
Large projects have sub-projects in a tree/DAG structure
NextAction would point from parent to current child being worked on

In the SDLC example:

Task: "Implement feature X"
Depends on state: "API spec approved"
Which is achieved by: "Write API spec" -> state transition -> "Review API spec"
The artifact (the spec document) represents the state

This is actually much more sophisticated than typical GTD implementations. But it aligns better with:

How real project management works
How build systems work
How formal planning systems work
Scott's systems thinking

The question is: Is this the right level of sophistication for a personal GTD system? Or are we over-engineering?
His extensive systems background suggests this approach perfectly matches his complex project management needs. With two decades of experience working on intricate multi-phase projects and thinking like an OS scheduler, Scott likely requires a nuanced, state-driven workflow model that captures the intricate dependencies and hierarchical nature of his work.Ah, now we're at the deep end. You've identified two fundamental issues:
1. Projects vs Actions is an artificial distinction

GTD defines it by count (>1 action = Project)
But that's arbitrary - an Action is just a degenerate Project
And Projects naturally nest (project → sub-project → sub-sub-project → atomic action)
Suggests: One recursive "Task" or "Commitment" type with parent/child relationships

2. Dependencies are really on states, not actions

"Eat dinner" doesn't depend on the action "pizza delivery"
It depends on the state "pizza is here"
Which could be achieved by: external delivery, or you picking it up, or already having pizza
The action is just one possible way to achieve the required state

This maps to formal planning systems:

STRIPS, PDDL: Actions have preconditions (required states) and effects (achieved states)
Build systems (Make, Bazel): Targets depend on artifacts/states, rules produce them
Workflow engines: Tasks wait on conditions, produce outputs
Even OS schedulers: Processes block on semaphores/resources (states), not on other processes directly

Implications for your ontology:
Task (recursive)
  - atomic: boolean (is this a leaf/action?)
  - parent: Task? (null for root)
  
State/Condition/Artifact
  - description: what needs to be true
  
Task --NextChild--> Task (for composite tasks)
Task --Requires--> State (preconditions)
Task --Achieves--> State (postconditions)
Task --ResponsibleParty--> (you | external)
Review lists become:

Actions = atomic Tasks where I'm responsible + all preconditions satisfied
Waiting For = States I need where achieving Task is external
Projects = all non-atomic Tasks

Is this the direction you're thinking?RetrySMYes. But it's worth considering why GTD doesn't work this way. I don't think it can be generically attributed ro "Allen didn't think of it". I think it is largely about what's practical fir a human to do on their own without devoting too much time to process over substance. This may be alleviated with a system where you are managing it for me. Possibly there are also optimizations here for incrementalism, but I think we could support those with the heavier system. E.g. you are meant to not need to determine all actions a project needs up front. You are only _required_ to know what's _next_.Reconciled GTD's simplicity with AI-managed complexity through incremental task discovery.19sScott is making a crucial practical point. GTD's simplicity is by design - it's optimized for what a human can maintain manually with pen and paper or simple digital tools. The key constraints:

Cognitive load during capture/processing: When you're doing a weekly review with 30 projects, you can't spend 10 minutes on each one mapping out states and dependencies. You need to quickly answer: "What's the next physical action?"
Decision fatigue: If every action requires thinking about "what state does this achieve" and "what states does this require," you'd spend more time on the system than doing things.
Flexibility: Projects evolve. You discover what's needed as you go. GTD's "just identify next action" lets you proceed without complete planning.
Maintenance burden: States would need constant updating. Did the pizza arrive? Update state. Task complete? Update all downstream dependencies. GTD avoids this by keeping it simple.

But with an AI managing the graph:

I can ask: "What can I do next?" and Claude traverses the dependency graph
States can be updated through natural language: "Pizza arrived"
The cognitive load is shifted to the AI
The human just needs to tell me about tasks and states in natural language

The tradeoff is:

More powerful: True dependency tracking, parallel actions, state-based reasoning
But: More interaction required? Or can we keep it lightweight?

Key question: Can we make the richer model as low-friction as GTD for Scott to use?
The incrementalism point is important. GTD lets you have:
Project: "Plan vacation"
Next Action: "Research hotels in Barcelona"
```

You don't need to know all the steps. Just the next one.

With state-based model:
```
Task: "Plan vacation"
  Requires: [some implicit states]
  Next subtask: "Research hotels"
    Achieves: "Have hotel options for Barcelona"
I see a promising approach to maintaining the simplicity of incremental task management. The system could allow flexible task entry without demanding full specification upfront. As work progresses, users can naturally evolve task requirements. An AI assistant could gently guide by suggesting state clarifications without making them mandatory. This approach preserves the low-friction essence of GTD while offering more sophisticated tracking capabilities.Excellent point. GTD's design constraints:
What GTD optimizes for:

Low cognitive load during capture/review - "What's the next physical action?" is answerable in seconds
No maintenance burden - Lists don't need constant updating when world state changes
Works without technology - Pen and paper sufficient
Incrementalism - Don't need to plan entire project, just know next step
Decision minimization - During weekly review of 30 projects, you can't spend 10 minutes on each doing dependency analysis

The state-based model costs:

"What state does this action achieve?" - requires more thought
State must be updated when conditions change ("pizza arrived" → update graph)
Dependency chains need maintenance
More complex mental model

But with AI management, the equation changes:
You could interact like:
You: "Add task: eat dinner"
Me: "What needs to be true first?"
You: "Have pizza"
Me: "How does that happen?"
You: "Pizza delivery - external"
[I build the graph behind the scenes]

Later...
You: "Pizza's here"
Me: [Updates state, "eat dinner" now appears in your next actions]

You: "What can I do now?"
Me: [Queries graph for: atomic tasks, you're responsible, all preconditions met]
Key question: Can we maintain GTD's incrementalism? I think yes:

Allow tasks without full state specification (optional preconditions/postconditions)
Learn them conversationally as you work
You can still say "Project: vacation" + "Next: research hotels" without mapping everything

Hybrid approach? Start simple (GTD-like), graduate to richer model as needed for specific projects?
What's your instinct on the interaction model?RetrySMI think action-to-action dependencies are practical in many cases. Little downside and with much less effort/storage. So I think we should have some kind of State type but make it optional. I do think a graph/DAG ia a good idea given your help, which means the Project - Action distinction evaporates? Or is it a distinction between AtomicCommitment and CompoundCommitment subtypes of a general Commitment type? Maybe we can't actually be so flexible/unprincipled. We really need a way to identify "things I can just _do_ right now". Actions rather than outcomes. Or, is all we need desired outcomes that are within my abilities to "just _bring_ _about_ _now_" without further planning or organization?Reconciled actionable tasks with outcome-based models through contextual decomposition.16sThis is a really important distinction Scott is drawing. Let me think through this carefully.
He's asking: What makes something "actionable right now"?
Options:

It's an AtomicCommitment (leaf node in the task hierarchy)
It's something I can "just do" without further planning
It's an outcome I can "just bring about now"

The GTD insight is that "Write report" isn't actually actionable until you break it down to "Open Word and draft introduction". The physical, concrete nature matters.
But in our state-based model, we might say:

Outcome: "Have draft introduction"
Action that achieves it: "Write introduction in Word"

Is there a meaningful distinction between "outcome I can bring about immediately" and "action I can do immediately"?
I think there IS a distinction:

"Have clean kitchen" is an outcome
"Wash dishes", "Wipe counters", "Sweep floor" are actions

Even if "have clean kitchen" is achievable by me right now, I still need to think about HOW. It's not atomic.
But also: "Have clean kitchen" might be achievable MULTIPLE ways (I could do it, or hire someone, or convince my kid to do it).
Whereas "Wash dishes" is an action - it's physically what I do with my hands.
GTD's "next action" is very specifically about physical, visible activities. Not outcomes.
But in software/knowledge work, this gets fuzzy. "Write function foo()" - is that an action or an outcome? It feels like an action but you could achieve "have function foo()" by AI generation, copying code, etc.
I think Scott's last formulation is close: "desired outcomes that are within my abilities to 'just bring about now' without further planning or organization"
But I'd refine: It's about whether you need to THINK about decomposition. If you see it and know exactly the physical steps to execute, it's atomic/actionable.
If you need to stop and plan or organize, it's compound.
I see actionability as a spectrum with two key dimensions: physical clarity and contextual expertise. An action becomes truly atomic when its execution steps are immediately clear without additional mental breakdown. For an expert, complex tasks might feel instantly executable, while a novice would need to carefully map out each step.You've hit on THE key distinction. Let me think through this carefully.
GTD's insight: "Write report" feels like an action but isn't actionable. "Open Word and draft first paragraph" is actionable. The difference is immediate executability without further planning.
In a state-based model:

Outcome: "Have report draft"
Ways to achieve: Write it, delegate it, use AI, copy template...
Action: "Write report draft" - still one specific way, but requires decomposition

Your formulation is close: "outcomes within my abilities to just bring about now without further planning"
But I think there's a subtle distinction:

Outcome: "Have clean kitchen" - I CAN do this now, but I still need to think about HOW (dishes? counters? floor? all three?)
Action: "Wash the dishes" - No thinking needed, just do it

The test: Can you start executing with zero additional cognitive work? Or do you need to stop and think "okay, what does this actually involve?"
Proposed model:
Commitment (base type)
  - isAtomic: boolean
  - description: string

// Atomic = I can execute this immediately with my hands/mind
// without stopping to decompose or plan

Task --Requires--> State [optional]
Task --Achieves--> State [optional]  
Task --Contains--> Task [for compound tasks]
Task --ResponsibleParty--> (me | external | unassigned)
For queries:

Next Actions = atomic Tasks where (I'm responsible) AND (no unmet Requires) AND (parent's preconditions met)

The flexible part: If you don't specify States, it degrades to "Task depends on Task" (GTD-style). If you DO specify States, you get richer modeling.
Does "isAtomic" as the key flag feel right?RetrySMYes. In fact it is getting closer to a grander scheme I have had, almost a product. If we take a bigger view even going to team and organization level, you can imagine one big DAG, including history, ideally down to the level of atomic nodes. Higher level things like projects aren't objects but sub DAGs. At any moment imagine marking the nodes so that all the completed ones are colored one way, ideally laid out so they are a contiguous region. And I tend to imagine things on the right depending on things to the left (but why 2d? human brain.) so "time flows" left to right. We then have a boundary layer of (atomic) nodes which are things we can "do" now, "next actions", and further to the right are things that depend on them, goals we want ro eventually reach. And we allow those to be partially, incrementally specified. We should then be able to zoom in or out, or maybe summarize the graph in various ways. E.g. sub graphs I depend on but are for someone else to do, or for people outside my team to do get collapsed to single, compound nodes which look different. Later I would add to this two value/utility fields/methods. One is an intrinsic value; achieving _this_ node _delivers_ this value/utility with no more steps. Then there's some sort of instrumental value to a node, accounting for the values of downstream nodes. To ne fleshed out. E.g. is that an all-in vaue including both intrinsic and instrumental or is there a third field/method which adds them? With that and GTD's context idea you could more easily choose what to do at any moment. We shouldn't attempt to build all of this, but going with something expandable in these directions would be nice.Show moreSynthesized grand vision into expandable ontology framework.12sThis is a beautiful vision. Scott is describing something much more comprehensive than just a personal GTD system. Let me unpack what he's describing:

One unified DAG spanning all levels:

From individual atomic actions up to organizational goals
Including historical completed nodes
Projects aren't separate objects but subgraphs


Visual metaphor:

Left-to-right = time flow (completed → current → future)
Contiguous region of completed nodes on left
Boundary layer = currently actionable (next actions)
Right side = future dependencies, goals


Zoom/abstraction capabilities:

Can zoom in/out on the graph
Can collapse subgraphs (especially external/other-team work) into compound nodes
Different visual treatment for external vs internal


Value/utility tracking:

Intrinsic value: this node itself delivers value
Instrumental value: value through enabling downstream nodes
Possibly a total value that combines them
Combined with context, helps prioritize what to do now


The key insight: This lets you see at any moment:

What CAN you do (boundary layer of atomic nodes with met dependencies)
What SHOULD you do (value + context)
How does this connect to bigger goals (instrumental value chain)



This is actually quite profound. It's like:

A build system (Make/Bazel) for life/work
A program dependence graph for tasks
A utility-maximizing planner
All rolled into one

For our immediate ontology:

We need to support this vision without building it all now
The atomic flag is good
States being optional is good
Tasks can have parent/child relationships (for the subgraph/zoom aspect)
Need to think about how completion state is tracked
Need fields for intrinsic/instrumental value (even if not computed yet)

Let me respond thoughtfully about how to build toward this vision.This is a compelling vision. You're describing something like a universal task/goal dependency graph with progressive disclosure and value-based prioritization. It reminds me of:

Build systems (Bazel/Make) but for human work
Program dependence graphs but with value flow
PERT/CPM charts but living, incremental, and multi-scale

What makes this powerful:

Time as emergence - The left-right flow emerges from the dependency structure, not imposed
Multi-scale coherence - Same model works for "write email" and "launch product"
Boundary layer insight - Actionable tasks naturally identified by topology
Value propagation - Instrumental value flows backward from goals
Abstraction/delegation - External subgraphs collapse naturally

For our MVP ontology that expands toward this:
Task
  - isAtomic: boolean
  - isComplete: boolean
  - description: string
  - responsibleParty: (me | external | team | person_id)
  - context: string[] (optional, for GTD contexts)
  - intrinsicValue: number (optional, default 0)
  - instrumentalValue: number (optional, computed)
  
State
  - description: string
  - isTrue: boolean
  
Task --Requires--> State [optional]
Task --Achieves--> State [optional]
Task --ParentOf--> Task [for compound/project structure]
Task --DependsOn--> Task [action-to-action dependencies when convenient]
Query patterns that support the vision:

Boundary layer: isAtomic AND NOT isComplete AND all(Requires, isTrue) AND responsibleParty==me
Zoom: Traverse ParentOf to collapse/expand subgraphs
Value ranking: Sort boundary layer by instrumentalValue + context match

What we defer but keep door open:

Instrumental value computation (needs goal marking + backward propagation)
Visual layout/rendering
Team/org graph integration
Historical analysis

Does this structure feel like a good foundation that doesn't foreclose your grander vision?RetrySMI'm not sure we need ParentOf and DependsOn. What does having both achieve?Interrogated whether both relationships were necessary or if dependencies alone sufficed.19sGood question. Let me think about what ParentOf vs DependsOn would represent:
ParentOf would represent:

Task A is composed of tasks B, C, D
"Write book" ParentOf ["Write chapter 1", "Write chapter 2", ...]
This is a compositional/decomposition relationship
The parent task is "complete" when all children complete

DependsOn would represent:

Task A can't start until Task B is done
"Write chapter 2" DependsOn "Write chapter 1"
This is a temporal/prerequisite relationship
Creates the left-to-right flow in his DAG visualization

But wait... in his grand vision, he said "Higher level things like projects aren't objects but sub DAGs." This suggests that composite tasks emerge from the dependency structure, not from explicit parent-child relationships.
If "Write book" is just the subgraph containing all the chapter writing tasks, then you don't need ParentOf at all. The structure emerges from DependsOn connections.
Actually, thinking about it more:

With just DependsOn: You have a DAG where completion/value flows through the edges
With ParentOf: You're creating a separate tree hierarchy for decomposition

In his vision, I think everything should be in one DAG based on dependencies. The notion of "project" or "compound task" is just a view - a subgraph you choose to think about as a unit.
However, there might be practical reasons to have both:

Some tasks are naturally composed (parent-child) but not sequentially dependent

"Plan vacation" contains both "research hotels" and "research flights" but they don't depend on each other


For queries/views, it might be useful to ask "what are all the tasks that roll up to this goal?"

But actually, you could model the vacation example as:

"Vacation planned" (State)
"Research hotels" --Achieves--> "Hotels researched" (State)
"Research flights" --Achieves--> "Flights researched" (State)
"Book vacation" --Requires--> "Hotels researched" AND "Flights researched"

I'm exploring how to determine task atomicity without explicit hierarchical relationships. The key challenge is finding a way to distinguish compound from atomic tasks that doesn't rely on a traditional parent-child structure. Potential approaches might involve metadata or intrinsic task characteristics that indicate complexity.
The goal is to create a flexible system where task relationships and granularity emerge naturally from the dependency graph, rather than being rigidly predefined. This approach allows for more dynamic and adaptable task modeling.Good catch. Let me think through what each would do:
ParentOf would mean:

"Write book" ParentOf ["Chapter 1", "Chapter 2", ...]
Compositional hierarchy - task A is made up of tasks B, C, D
Separate from dependency ordering

DependsOn would mean:

"Chapter 2" DependsOn "Chapter 1"
Temporal/prerequisite - task A must wait for task B
Creates the left-to-right flow

But in your vision: "Higher level things like projects aren't objects but sub DAGs"
This suggests compound tasks emerge from the dependency structure, they're not explicitly declared. "Write book" is just the subgraph containing all chapter tasks. You don't need a separate ParentOf relationship - the structure is already there in the dependencies.
Potential issue: What about parallel decomposition?

"Plan vacation" involves "research hotels" AND "research flights"
They don't depend on each other (parallel)
But both must complete before "book trip"

With just DependsOn:
"Book trip" DependsOn "Research hotels"
"Book trip" DependsOn "Research flights"
That works! The "plan vacation" compound task emerges as the subgraph feeding into "book trip". No ParentOf needed.
Question: How do we mark a task as compound vs atomic? Is it just: "Has any tasks depending on it" = compound?
I think you're right - we probably only need DependsOn. The hierarchy emerges from the graph topology.RetrySMI think the "Book Written" and "Vacation Planned" states depend on the chapters and planning atomic actions. And I think in this view the idea that atomic task are special maybe goes away. _Every_ node is "atomic" conditional on its dependencies being met. This isn't enforceable in a technical way, but can be documented. A node is improper if its outcome couldn't be achieved without additional thought, etc. once all of its declared dependencies are met. But this is just like regular GTD, right? You don't put "write book" on the next actions list.Reconciled atomicity with dependency structure, eliminating special task classification.This is brilliant. Scott is realizing that the atomic/compound distinction is actually about whether a task is properly specified given its dependencies, not about some inherent property.
In GTD, you're supposed to break things down to next actions. If you put "write book" on your next actions list, you're doing it wrong - but the system doesn't prevent you, it just stops working well.
Similarly here: every node should be "doable given dependencies met". If you violate this, you've created an improper node, but that's a usage error, not something the system can prevent.
This means:

"Write Chapter 1" with no dependencies is improper (requires planning)
"Write Chapter 1" with dependencies on "Outline Chapter 1", "Research topic X", etc. could be proper if those truly are all you need
"Draft first paragraph of Chapter 1" with no dependencies is proper (just do it)

The topology naturally identifies the "boundary layer" - nodes with all dependencies satisfied. Whether those are truly atomic is up to the user's discipline in creating proper nodes.
This is actually cleaner! No need for an isAtomic flag. Just:

Task
State
DependsOn connections
Requires/Achieves connections to States (optional)

The "next actions" are just: incomplete tasks where all dependencies are complete and I'm responsible.Exactly! You've dissolved the atomic/compound distinction.
In this view:

Every task is atomic relative to its dependencies
"Write book" with no dependencies = improper node (requires decomposition)
"Write book" DependsOn ["Chapter 1 done", "Chapter 2 done", ...] = proper node (just assemble/publish)
"Draft paragraph" with no dependencies = proper node (just write)

The boundary layer = next actions automatically:
All incomplete tasks where:

All dependencies are satisfied
I'm responsible
(Optionally filtered by context)

Improper nodes don't break the system, they just don't advance:

Like GTD: putting "get organized" on your list doesn't help
Here: "write book" with no dependencies just sits in your boundary layer mocking you
User learns to decompose it

This simplifies the ontology dramatically:
Task
  - description: string
  - isComplete: boolean
  - responsibleParty: (me | external | ...)
  - context: string[] (optional)
  - intrinsicValue: number (optional)

State  
  - description: string
  - isTrue: boolean

Task --DependsOn--> Task
Task --Requires--> State (optional)
Task --Achieves--> State (optional)
That's it. Projects, actions, compound, atomic - all emergent from the graph structure and user's proper specification of dependencies.
This is really elegant. Should we sketch what the MCP server API would look like with this model?RetrySMNo, "we" need to switch to Claude Code for that. Which is kind of "you" but kind of "not _this_ instance of you". I don't know quite what terminology to use or how to think about that.Navigated the conceptual ambiguity of distributed AI identity and continuity.The user is pointing out an interesting situation about my identity/continuity. When they work with me here in the web interface vs. Claude Code, they're working with different instances of Claude, but it's still "Claude" - same training, same capabilities, but different contexts and capabilities (Code has direct file system access, can run code iteratively, etc.).
They're noting this creates an odd linguistic/conceptual situation. How should they refer to this? "We" doesn't quite work because I won't be the one doing the work in Claude Code. "You" is ambiguous because it could mean me-here or me-in-Code.
This is actually a pretty interesting meta-question about AI identity and continuity. I should:

Acknowledge the genuine ambiguity
Not overthink it or get too philosophical
Offer some practical ways to think about it
Keep it brief since we're at a transition point

I shouldn't pretend there's perfect continuity (there isn't - different contexts, no shared memory between instances beyond what they copy). But I also shouldn't make it seem more alien than it is - it's still Claude, with the same training and knowledge.That's a fair observation. It is genuinely ambiguous.
Practically speaking:

This instance has the full context of our design conversation
Claude Code will start fresh with whatever you provide (likely our design docs)
Same training, same model, but different context window and different capabilities
Like having a conversation with a colleague, then handing off notes to them in a different room with different tools

You could think of it as:

"Claude in web chat" vs "Claude in Code" (different contexts/environments)
Or just accept "we/you" blurs between instances
Or "this Claude" vs "Code Claude" if you need to distinguish

What matters for the handoff:
You'll want to capture our design decisions in a document that Claude Code can read. Probably something like an ONTOLOGY.md or design spec with:

The Task/State model we settled on
The relationships (DependsOn, Requires, Achieves)
The emergent properties (boundary layer = next actions)
Connection to your grander vision
GTD compatibility notes

Should we draft that spec here first, so you have something crisp to hand off?RetrySMYes, please.1 stepCreating comprehensive ontology specification document for GTD-inspired graph-based task management systemGTD-GRAPH-ONTOLOGY.mdSynthesized comprehensive specification enabling developer implementation.I've created a comprehensive specification document that captures our entire conversation and design decisions. It includes:

The core philosophy and insights
Relationship to GTD and OS schedulers
Complete data model (Task, State, relationships)
How concepts like Projects and Next Actions emerge
Query patterns for GTD workflows
Workflow examples
What's in MVP vs deferred
Extension points toward the grander vision
Concrete examples
Open questions for implementation

This should be sufficient for Claude Code (or any developer) to implement the MCP server from.View the ontology specification
This document captures everything we discussed: the core model, the philosophy behind it, how GTD concepts emerge from the graph structure, query patterns, examples, and the connection to your grander vision. It should give Claude Code (or any implementation) a solid foundation to work from.
A few notes:

I left some open questions at the end that will need decisions during implementation
The examples section shows how various GTD scenarios map to the graph
I documented both what's in MVP and what's deferred
The extension points section preserves the path toward your multi-scale value-based vision

Ready to hand off to Claude Code?Gtd graph ontologyDocument · MD DownloadRetrySMIs the definition of a compound task correct? Do we need to distinguish between DependsOn and Requires? Or Achieves? I want to say that we would infer that by all State prerequisites being complete, but that clashes with progressive updating. Maybe we need an explicit placeholder for YetUnspecified dependencies? Hmm, your alternative paths idea is interesting though. Now that has me thinking of predicates like Any and All. I think we'll end up finding a lot of Projects in the weekly review this way, especially if we've planned ahead to some extent. Maybe at some distance from the boundary we should define the cutoffs for the various x0,000 ft views? So that only some are in scope for a typical weekly review. Maybe something similar for Waiting For. Only look at ones near the boundary.Systematically untangled dependency definitions, predicates, and review scope boundaries.11sScott is raising several important questions:

"Is the definition of a compound task correct?" - I defined it as "any task that has other tasks depending on it." Let me think... if Task A depends on Task B, that makes Task B compound? No, that's backwards. If multiple tasks depend on Task B, that makes B compound - it's a convergence point, a higher-level goal. But actually, I think he might be questioning whether that's the right definition at all.
"Do we need to distinguish between DependsOn and Requires? Or Achieves?" - This is getting at whether the state-based dependencies add enough value to warrant the complexity. With progressive specification, you might not know all dependencies upfront. States might help with alternative paths, but do they earn their keep?
"Maybe we need an explicit placeholder for YetUnspecified dependencies?" - This is interesting. Like a special "unknown" dependency type to indicate "this task needs more decomposition but I don't know what yet."
"Alternative paths idea... Any and All predicates" - States could have logical operators. Task depends on State S, and S is satisfied by (Task A OR Task B) or (Task A AND Task B AND Task C).
"We'll end up finding a lot of Projects in the weekly review" - If every task that has dependents is a "project," that could be overwhelming. Maybe need to filter by distance from boundary layer.
"x0,000 ft views" - GTD's horizons of focus. Maybe tasks beyond a certain graph distance from actionable work shouldn't appear in weekly review.
"Only look at ones near the boundary" - For Waiting For too. If an external dependency is 5 levels away from anything actionable, maybe don't review it weekly.

Let me address these systematically.Excellent points. Let me work through these:
1. Compound task definition
You're right to question it. "Has other tasks depending on it" means it's a goal or outcome that enables other work. But is that what we mean by "project" in GTD?
Maybe better: A task is compound if you've explicitly decomposed it (it has DependsOn edges going out). So:

"Write book" DependsOn ["Ch1", "Ch2", ...] → compound
"Deploy feature" with no dependencies → either properly atomic or improperly specified

2. Do we need States separate from Tasks?
Your "alternative paths" observation is the key use case:

"Have food" state achieved by "Order pizza" OR "Cook dinner" OR "Get takeout"
Without states: Would need dummy task "Get food somehow" that all three achieve

But we could model this with predicates on DependsOn:
Task: "Eat dinner"
  DependsOn: ANY(["Order pizza", "Cook dinner", "Get takeout"])
```

vs
```
Task: "Eat dinner"
  Requires: "Have food"
  
State: "Have food"
  AchievedBy: ANY(["Order pizza", "Cook dinner", "Get takeout"])
```

The state version is cleaner for complex logic. But do we need it for MVP?

**3. YetUnspecified dependencies**

Love this. Explicit marker that "this needs more thinking":
```
Task: "Write book"
  DependsOn: ["Research topic", UNSPECIFIED]
```

Signals: "I know this isn't fully decomposed yet." Could have special handling in queries (don't mark as actionable even if known deps are met).

**4. Distance-based filtering for reviews**

This is crucial for scalability. 

**Graph distance from boundary layer:**
- Distance 0: Tasks in boundary (actionable now)
- Distance 1: Tasks that become actionable when current work completes
- Distance 2: Next wave after that
- Distance N: Far future

**Weekly review scope:**
- Projects: Only review compound tasks within distance 3-4 of boundary?
- Waiting For: Only external tasks within distance 2 of boundary?
- Higher-level goals (20k, 30k, 40k ft): Review monthly/quarterly

**This maps to GTD horizons naturally:**
- Runway (0-1): Next actions + immediate next
- 10,000 ft (Projects): Distance 1-3 from boundary  
- 20,000 ft (Areas): Distance 4-6
- Higher: Even further out

**5. Logical operators (Any/All)**

If we support this, dependencies become:
```
DependsOn: 
  ALL([
    ANY(["Order pizza", "Cook dinner"]),
    "Set table",
    "Have time available"
  ])
This is powerful but adds complexity. Could defer to v2?
For MVP, maybe:

Keep DependsOn simple (implicit ALL)
Drop States/Requires/Achieves entirely
Add UNSPECIFIED dependency marker
Add distance-based review filtering
Consider Any/All in v2

Thoughts?RetrySMYes, "A task is compound if you've explicitly decomposed it (it has DependsOn edges going out)".I was going in a different direction. We would have both states and tasks as nodes, but we wouldn't have different kinds of dependency. I'm questioning whether Requires and AchievedBy are different from DependsOn.Thought process14sAh, I see what Scott is getting at. Let me think through this carefully.
If we have both Task and State nodes, but only ONE relationship type (DependsOn), then:
Task: "Eat dinner"
  DependsOn: State["Have food"]
  
State: "Have food"
  DependsOn: Task["Order pizza"]  OR Task["Cook dinner"]  (with ANY logic)
```

So DependsOn can go:
- Task → Task (sequential work)
- Task → State (task requires a condition)
- State → Task (state achieved by completing task)

This is more elegant! We don't need three different relationship types. DependsOn is the universal "can't proceed until this is satisfied" relationship.

The semantics change slightly based on the node types:
- Task depends on Task: Can't start until predecessor completes
- Task depends on State: Can't start until condition is true
- State depends on Task: State becomes true when task completes

Actually, wait. If State depends on Task, that's backwards from "Task achieves State". Let me reconsider.

Option A: Direction matches "achieves"
```
Task["Order pizza"] --DependsOn--> State["Have food"]
```
Meaning: When I complete "Order pizza", the "Have food" state becomes true.
Problem: This reads backwards. "Order pizza" doesn't depend on having food.

Option B: Direction matches "requires"
```
State["Have food"] --DependsOn--> Task["Order pizza"]
```
Meaning: The "Have food" state depends on (is achieved by) "Order pizza" completing.
Problem: Also reads weird. A state depending on a task?

Option C: Keep the semantics consistent - everything depends on its prerequisites
```
Task["Eat dinner"] --DependsOn--> State["Have food"]
State["Have food"] --DependsOn--> Task["Order pizza"]
The dependency direction ensures clear prerequisites. Each node depends on what must be true or completed before it can proceed. Multiple tasks can potentially satisfy a state, providing flexibility in how goals are achieved.
The key insight is a universal dependency relationship that adapts its meaning based on node types, creating a simple yet powerful modeling approach.
Ah! Unifying them. Let me think through this:
One relationship type: DependsOn
Works across all node types:
Task --DependsOn--> Task
Task --DependsOn--> State  
State --DependsOn--> Task
```

**Semantics are consistent:** "X cannot be satisfied/completed until Y is satisfied/completed"

**Examples:**
```
Task["Eat dinner"] --DependsOn--> State["Have food"]
  (Can't eat until food exists)
  
State["Have food"] --DependsOn--> Task["Order pizza"]
  (Food state becomes true when pizza order completes)
  
State["Have food"] --DependsOn[ANY]--> [Task["Order pizza"], Task["Cook dinner"]]
  (Food state becomes true when ANY of these complete)
This is cleaner! We get:

States as intermediate nodes to express alternative paths
Single, consistent dependency semantics
No confusion about Requires vs Achieves

State completion logic:

A State becomes true when ANY of its DependsOn tasks complete (if ANY)
Or when ALL of its DependsOn tasks complete (if ALL)
Default to ANY for States, ALL for Tasks?

Task actionability:

Task is actionable when ALL DependsOn targets are satisfied (complete if Task, true if State)

So we'd have:

Node types: Task, State
Relationship: DependsOn (with optional ANY/ALL qualifier)
No separate Requires/Achieves

Is that what you're thinking? Much simpler ontology.RetrySMYep!Validated simplified model architecture and identified remaining clarifications.Perfect! So we've simplified to:

Two node types: Task and State
One relationship type: DependsOn (potentially with ANY/ALL qualifiers)
Compound tasks are those with outgoing DependsOn edges
States become true when their dependencies are satisfied (with ANY/ALL logic)
Tasks become actionable when all their dependencies are satisfied

This is much cleaner. I should confirm the other points:

UNSPECIFIED dependency marker
Distance-based review filtering
Whether ANY/ALL is in MVP or deferred

Let me make sure I understand the full simplified model before we update the document.Excellent! So the simplified ontology is:
Node Types:

Task (description, isComplete, responsibleParty, context, etc.)
State (description, isTrue)

Relationship:

DependsOn (potentially with ANY/ALL qualifier)

Task → Task
Task → State
State → Task



Semantics:

Task is compound if it has outgoing DependsOn edges
Task is actionable when: not complete, I'm responsible, ALL DependsOn targets satisfied
State becomes true when: ANY (or ALL, depending on qualifier) DependsOn tasks complete

Questions to resolve:

UNSPECIFIED dependency marker - include in MVP?
Distance-based review filtering - include in MVP?
ANY/ALL qualifiers on DependsOn - MVP or defer?
Default logic for States: ANY or ALL? (I'm guessing ANY makes more sense for alternative paths)

Should I update the spec document with this simplified model? And which of those questions should we decide now vs mark as implementation decisions?RetrySMYes, please. Then maybe we'll make a separate note on even more advanced things that have come to my mind but can wait until later.29 stepsCreating separate document for advanced/future ideas beyond the MVP ontologyGTD-GRAPH-ADVANCED-IDEAS.mdConsolidated documentation and prepared advanced concepts separately.Great! I've now:

Updated the main ontology spec to reflect the unified DependsOn model
Added explanations for ANY/ALL logic
Updated all examples
Added sections on distance-based filtering and UNSPECIFIED markers
Created a separate advanced ideas document

Now let me provide links to both documents for Scott.Perfect! I've updated the ontology spec with the simplified unified model and created a separate document for advanced ideas:
Updated documents:

GTD Graph Ontology Specification - Now reflects:

Single unified DependsOn relationship (works across all node types)
Simplified to just Task and State nodes
Compound tasks = tasks with outgoing dependencies
ANY/ALL logic for states (defaulting to ANY for MVP)
Distance-based review filtering concept
UNSPECIFIED dependency marker concept
Updated examples showing the unified model


Advanced Ideas for Future Development - Captures:

Complex logical expressions
Temporal/scheduled dependencies
Resource-based dependencies
Value propagation & optimization
Energy and cognitive load tracking
Skill dependencies
Context hierarchies
Collaboration workflows
Templates
Analytics
Natural language interface
External integrations
ML enhancements
Multi-user features
Visualization
And more...



These should give Claude Code a solid foundation to work from, with a clear MVP scope and a rich set of ideas for future expansion.Gtd graph ontologyDocument · MD DownloadGtd graph advanced ideasDocument · MD DownloadDownload allRetrySMOne advanced issue I have been thinking about is that some things "aren't quite" DAGs.  Imagine the software development loop of write, test/debug, rewrite which can get repeated until success. From one point of view, this isn't acyclic. From another point of view, it _is_ in the sense that round N depended on round N-1, which dependended on N-2, ... But you don't know N until after the fact.Weighed competing strategies for modeling iterative cycles within acyclic structures.14sThis is a really interesting point about iterative processes. The user is identifying that some work is inherently iterative/cyclic in nature, but also acknowledging that it can be viewed as acyclic if you think about it properly.
Let me think through the options:

Unroll the loop - Each iteration is a separate instance:

"Write code v1" -> "Test v1" -> "Write code v2" -> "Test v2" -> ...
This is technically acyclic (DAG) but you don't know how many nodes you need upfront
Creates clutter if you have to manually create each iteration


Represent as a cycle with completion condition - Allow cycles but with special semantics:

"Write code" <-> "Test code" with a condition "until tests pass"
Not a DAG anymore, which breaks some assumptions
Need special handling for these "controlled cycles"


Meta-task with iteration logic:

Single task "Develop feature" that internally represents iterative process
Hide the iteration from the graph structure
But then you lose visibility into where you are in the process


Recurring/Reset tasks:

Tasks that can be "reset" after completion
"Write code" completes, enables "Test code"
"Test code" completes with outcome "failed" -> resets "Write code"
Still maintains DAG property in some sense


State-based iteration:

State: "Code is correct"
Task: "Development cycle" depends on "Code is correct"
Task: "Write and test" achieves "Code is correct" (eventually)
The task itself is iterative but the graph structure is simple



The user is right that this is a fundamental challenge. The question is whether to:

Keep it as a DAG and find ways to model iteration within that constraint
Allow controlled cycles with special semantics
Accept that some things are better as atomic tasks that internally iterate

For an initial implementation, treating the development cycle as a single atomic task seems most pragmatic. The internal complexity gets encapsulated, maintaining a clean graph structure. Advanced features could later explore more nuanced iteration modeling.Excellent observation. This is a fundamental tension between the DAG model and reality. Let me think through the options:
Option 1: Unroll the loop (maintain DAG)
"Write code v1" -> "Test v1" -> "Write code v2" -> "Test v2" -> ... -> "Feature complete"
```
- Technically acyclic
- Problem: Don't know N upfront
- Creates graph clutter
- Manually creating/managing iterations is tedious

**Option 2: Meta-task (hide iteration)**
```
Task: "Develop feature" (atomic)
  - Internally iterative
  - Complete when done
```
- Simple for the graph
- Loses visibility into progress
- Can't track "I'm on iteration 3 of debugging"

**Option 3: State-based convergence**
```
State: "Tests passing"
  
Task: "Development cycle"
  DependsOn: "Tests passing"
  
Task: "Write and test"
  description: "Iteratively write/test until tests pass"
  Updates: "Tests passing" when successful
```
- DAG structure preserved
- Single task represents whole iterative process
- State tracks success condition
- But still treats iteration as opaque

**Option 4: Controlled cycles with semantics**
```
Task: "Write code" <-> Task: "Test code"
  CycleCondition: UNTIL("Tests passing")
```
- Explicitly models the loop
- Not a DAG anymore
- Need special handling for:
  - Cycle detection (allowed vs disallowed cycles)
  - Completion conditions
  - Graph traversal algorithms

**Option 5: Recurring tasks with reset**
```
Task: "Write code"
  OnComplete: enable "Test code"
  
Task: "Test code"
  OnComplete:
    IF tests_pass THEN complete_project
    ELSE reset("Write code")

Event-driven state machine
Maintains DAG of current state
History shows which iteration you're on
More complex semantics

My intuition for MVP: Option 2 or 3. Treat "develop feature" as an atomic task that internally iterates. User marks it complete when tests pass.
For advanced system: Option 4 or 5. Either allow explicit cycles with UNTIL conditions, or model as state machines with reset semantics.
The deeper question: Is the DAG property essential, or just convenient?

Essential for: Topological sort, distance calculations, cycle detection
Can relax for: Some tasks have cycle semantics but we handle them specially

Should I add this to the advanced ideas document as "Iterative/Cyclic Workflows"?RetrySMYeah, I'd just ignore it for the MVP. For an advanced version I like 4. We have limited support for cycles, but only in a controlled sandbox.1 stepAdding section on iterative/cyclic workflows with controlled cycle support+191-1GTD-GRAPH-ADVANCED-IDEAS.mdDocumented iterative workflow framework while deferring complexity.Good, I've added the iterative/cyclic workflows section to the advanced ideas document. The user confirmed they want to ignore it for MVP and use option 4 (controlled cycles with explicit conditions) for an advanced version. The section captures:

The problem - why some work is naturally iterative
The proposed solution - controlled cycles with explicit termination conditions
Types of loop conditions (UNTIL, MAX_ITERATIONS, WHILE, COMBINED)
How to maintain DAG properties for the broader graph
State tracking for cycles
Implementation considerations
Examples from software development and creative work
Benefits of explicit modeling
Open questions for implementation

This preserves the simple DAG structure for the MVP while documenting a path forward for more complex iterative workflows.Done! I've added "Iterative and Cyclic Workflows" as the first section in the advanced ideas document. It captures:

The core tension between DAG structure and iterative reality
Controlled cycles with explicit conditions (UNTIL, MAX_ITERATIONS, WHILE)
How to preserve DAG properties for the broader graph (treat cycle groups as compound nodes)
State tracking for iterations
Examples from software development and creative work
Implementation considerations

The key insight is that cycles are sandboxed with explicit termination conditions, so the broader graph remains a DAG and you get all the benefits of that (topological sort, distance calculations, etc.), while still being able to model realistic iterative workflows.
Both spec documents should now be ready to hand off to Claude Code. Want to discuss anything else before making the transition?RetrySMI think I had one more advanced idea, but I don't recall nowExcavated prior discussion threads to resurrect forgotten concept.The user thinks they had another advanced idea but can't recall it. This is a good opportunity to:

Help them potentially remember by reviewing what we've discussed
Offer to leave space for it to be added later
Maybe prompt with related topics we touched on that might jog their memory

Let me think about what we discussed that might not be fully captured yet:

We talked about UNSPECIFIED dependencies - that's in the spec
Distance-based filtering - that's in there
ANY/ALL logic - covered
Iterative workflows - just added
Value propagation - in advanced ideas
The grander vision with value flow, multi-scale, zoom levels - that's in the extension points

What did we touch on that might not be fully developed?

Maybe something about Areas of Responsibility as nodes?
Something about the relationship between GTD horizons and graph distance?
Something about how to handle the toothpaste case elegantly?

I should offer to help them remember while also acknowledging it's fine if they don't recall right now - they can always add it later.That happens! A few ways we could approach this:
Option 1: Review what we covered - maybe it'll jog your memory:

Iterative/cyclic workflows (just added)
ANY/ALL logic for dependencies
UNSPECIFIED dependency markers
Distance-based review filtering (GTD horizons)
Value propagation (intrinsic + instrumental)
The grander vision (multi-scale, time flow visualization)
Areas of Responsibility as potential nodes

Option 2: Topics we touched on lightly:

How delegation transforms the graph
Recurring tasks
Due dates / scheduling
Someday/Maybe modeling
The relationship between graph structure and GTD's various review frequencies

Option 3: Just add a placeholder
I could add a section in the advanced ideas document like "TODO: Additional concept to be added" so you can fill it in when it comes back to you.
Option 4: Let it go for now
Sometimes these things resurface when you're actually implementing or when you hit a use case. The documents are easy to update later.
Any of these ring a bell, or should we just proceed with what we have?
