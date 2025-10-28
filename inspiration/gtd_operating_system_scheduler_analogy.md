I have a particular way of thinking about the GTD methodology for managing projects, tasks, etc. I see it analogous to the process scheduler in an OS. A set of data structures maintaining the state of what needs doing, and procedures for doing them and updating the state. It's an imperfect analogy, for instance differentiating atomic tasks (actions) from compound tasks (projects) and there are more. It fits more completely in the broader category of schedulers. Does this make sense so far?This is a fascinating systems-level analogy for GTD (Getting Things Done). The parallel between task management and process scheduling is quite apt. Just as an OS scheduler maintains process states (ready, running, blocked, etc.) and manages transitions between them, GTD maintains task states (next actions, waiting for, someday/maybe) and defines workflows for moving between them.
The distinction you note between atomic tasks and projects is interesting - it's somewhat analogous to how an OS handles individual processes versus process groups or jobs. Though as you mention, it's an imperfect mapping since projects in GTD have more complex dependencies and hierarchical relationships.
I'm curious about how you see the "interrupt handling" aspect mapping to GTD - particularly how GTD's inbox processing maps to how an OS handles external events and interrupts. Would you say the weekly review in GTD is somewhat analogous to garbage collection or system maintenance processes?RetrySMI guess "interrupt handling" would link to David Allen's "mind like water". The garbage collection aspect is a bit of a stretch. Database compaction maybe? Or the "vacuum" process innPostges?Ah, "mind like water" as interrupt handling is a nice connection - just as a good interrupt handler ensures system responsiveness without becoming overwhelmed, the GTD mindset aims to let you respond appropriately to inputs without losing your overall flow state or getting bogged down.
The vacuum/compaction analogy for weekly review is interesting. Both serve to maintain system health by:

Cleaning up stale references (outdated tasks/projects)
Reorganizing data structures for better efficiency (refining project lists, consolidating related items)
Ensuring consistency (checking that all projects have next actions)
Reclaiming resources (mental bandwidth from completed or irrelevant items)

This makes me think about other database concepts that might map well to GTD - like how contexts could be seen as indices for faster task retrieval, or how the two-minute rule is like a query optimization strategy. The tickler file could be viewed as a kind of scheduled job queue.
What are your thoughts on how GTD's "horizons of focus" (purpose, vision, goals, etc.) fit into the systems analogy? They seem to operate at a different level than the process scheduler metaphor.RetrySMMaybe we'd have to go up a level to distributed computing.That's a compelling expansion of the model! The horizons of focus could map interestingly to different levels of distributed system coordination:

50,000 ft (Purpose/Values) → System architecture and design principles
40,000 ft (Vision) → Long-term distributed system goals/state
30,000 ft (Goals/Objectives) → Service level objectives/agreements
20,000 ft (Areas of Focus) → Service domains/bounded contexts
10,000 ft (Projects) → Individual services/applications
Ground (Next Actions) → Individual processes/tasks

This maps nicely because distributed systems also deal with questions of:

Alignment across different timescales and scopes
Balancing local optimization with global objectives
Handling eventual consistency (like how your projects gradually align with higher-level goals)
Managing partial failure (some areas progressing while others stall)

It's particularly interesting how this perspective highlights GTD's balance between autonomy (local decision making about next actions) and coordination (alignment with higher-level horizons), similar to how distributed systems handle local vs. global concerns.RetrySMOK, I'm glad this works. It paves the way to what I had in mind. Could you write a tutorial/guide to bullet journalling from any similar point of view?Let me think about bullet journaling through a systems lens.Bullet Journal: A Systems PerspectiveDocument # Bullet Journal: A Systems Perspective

## Introduction
The bullet journal can be conceptualized as an event-driven logging system with specialized data structures and indexing mechanisms. This guide will explain the bullet journal methodology throuI've written a guide that approaches bullet journaling from a systems perspective, similar to how we discussed GTD. The guide treats the bullet journal as an information management system with distinct data structures, protocols, and maintenance procedures.
Would you like me to expand on any particular aspect? For instance, we could dive deeper into the parallels between collection management and database optimization, or explore how different journaling approaches map to different system architectures.RetrySMI like the ready state / terminated / scheduled distinction. I think mark and sweep  garbage collection would kind of work as part of a  migration analogy. Threading ~ linked lists?Yes, threading as linked lists is a great refinement of the analogy! Each thread creates a chain of pointers (page numbers/references) connecting related items across different collections, just like nodes in a linked list.
The mark-and-sweep garbage collection parallel for migration is quite fitting:

Mark phase = reviewing tasks/items and marking those still relevant (live objects)
Sweep phase = migration itself, where unmarked items (dead objects) are left behind and marked items are moved forward

You could even extend this to generational garbage collection:

Daily log = young generation (high turnover)
Monthly log = middle generation
Future log/collections = old generation (more stable, less frequent collection)

And the ready/terminated/scheduled states do map cleanly to process states. We could even add:

Blocked state = waiting for tasks
Suspended state = someday/maybe items
Zombie state = completed tasks not yet migrated/cleared
Fork = task breakdown into subtasks

Would you like me to update the guide to incorporate these refined analogies? I think they'd particularly strengthen the sections on migration and threading.RetrySMThis is cool, but let's try something less directly analogous and more simply inspired by the original view of GTD. I think the key things to keep are that we are still ensuring we keep all the necessary state data to decide what to do at any moment, that there's clarity about what kind of data goes where (though now, unlike GTD, there's more flexibility. E.g. things can start one place when captured then migrate), and there are clear process for recording or moving data, and how to use the data to decide on actions. Generally less prescriptive than GTD, but it still must cover the same space.Ah, I see - taking the core insights about state management and workflow clarity from our GTD-as-scheduler model, but applying them more flexibly to bullet journaling. Less about direct system analogies and more about:

Complete state representation - ensuring no information about tasks/commitments/ideas gets lost
Clear data categorization - knowing where different types of information live, while allowing for flexible migration paths
Well-defined processes for:

Capturing (input handling)
Moving/transforming information (state transitions)
Reviewing the state to make decisions (scheduling)
Maintaining system health (cleanup/review)



The bullet journal would provide the infrastructure for this, but with more freedom in how exactly you implement it. Like having clear protocols but letting users choose their own data structures, so to speak.
Would you like me to draft a guide from this perspective? It would focus less on prescribing specific collections/methods and more on principles for maintaining reliable state and clear workflows, while leaving room for personal implementation choices?RetrySMYes. Given that GTD "clicked" for me, like many people, and more specifically in the way I described, I'm looking for a similar angle from which to (re)learn BuJo.I'll draft a guide that approaches BuJo from this perspective - focusing on what makes systems like GTD "click" (complete state tracking, clear processes) while embracing BuJo's flexibility.Bullet Journal: A State Management SystemDocument # Bullet Journal: A State Management System

## Core Principle
A bullet journal is fundamentally a system for maintaining a complete and accurate picture of your commitments, ideas, and information while providing clear processes for capturing, accesI've written this guide focusing on BuJo as a state management system - emphasizing the core principles that make GTD effective (complete state tracking, clear processes) while embracing BuJo's flexibility in implementation. It maintains focus on being able to trust your system and make clear decisions while allowing for personal adaptation in how you achieve that.
Would you like me to expand on any particular aspect? I'm particularly interested in your thoughts on whether this captures the same kind of systematic clarity that made GTD click for you, while preserving BuJo's more flexible nature.RetrySMThis is excellent! Very much in just the direction I had in mind. I think where I need more is moving it towards a practical guide. I really have forgotten the details, so I need instructions after the conceptualizations. I.e. what to when.Absolutely! Let's create a practical implementation guide that builds on this conceptual framework. We'll focus on the concrete "what to do when" while maintaining that state-management mindset.Bullet Journal: Practical Implementation GuideDocument # Bullet Journal: Practical Implementation Guide

## Initial Setup

### Required Materials
- A notebook (any type, but dotted gives most flexibility)
- A pen (just one is fine to start)
- Optional: ruler for clean lines

### First-Time Setup (30-45 mI've created a detailed practical guide that maintains our state-management perspective while providing specific, actionable instructions. It's organized around timeframes (daily, monthly) and common scenarios, with clear steps for each operation.
Would you like me to expand on any particular aspect? For instance, we could:

Add more detail to the daily operations
Develop specific collection templates
Create decision trees for common scenarios
Add troubleshooting flows for specific issues

Or if you're ready to start, we could focus on the initial setup steps in more detail.RetrySMI'm not clear on how/why tasks get to the monthly task list when they all start, I think, in a daily log. Similar questions on getting to the future log, though tentatively there I had in mind big things, like projects, naturally going there. Move completed tasks to monthly is either new to me or something I forgot.Good questions! Let me clarify these state transitions - you're right to question them.
I need to revise how I described task movement. Here's my current understanding of the core BuJo flow:

Daily Log

Primary capture point for most tasks
Where you mark completion (×)
Completed tasks stay right where they are - I was wrong about moving them to monthly
This maintains accurate historical state of when things were done


Monthly Task List

Not a duplicate/migration destination
Instead, it's for:
Tasks you know about at month start (from Future Log)
New tasks you know you need to do this month, but not necessarily today
Think "monthly queue" rather than "monthly record"


Future Log

You're right - bigger things, projects, major events
Known future commitments
Things you want to defer but not forget
Feeds into Monthly during setup



Would you like me to revise the practical guide to correct these flows? I particularly need to fix that incorrect advice about moving completed tasks to monthly, and clarify the distinct roles of each list in maintaining system state.
This gets at a deeper question about state tracking in BuJo: should I revise the guide to be clearer about how the Daily Log serves as the primary record of actual work/completion, while Monthly Task List is more about planning/queueing?RetrySMThe monthly tasks remains unclear to me. I would think that most tasks, even if I don't expect to do them today would end up on the daily log. Not because I expect to do  them today but because that's where _rapid_ logging happens. I.e. when I learn of a new task I will want to capture it rapidly.Ah, this is a really important insight about rapid logging and state capture! You're right - the core principle is that rapid logging needs to be rapid - no decision-making about where something "belongs" during capture.
Let me think this through:

Daily Log is the primary capture point

When a task comes in, it goes there
No need to decide "is this for today?" during capture
Just get it down quickly and reliably
This maintains the "frictionless capture" principle we valued in GTD


So then the Monthly Task List's role becomes less clear...
Maybe it's more about:

Planning view rather than capture point
Could be populated during monthly setup from Future Log
Maybe during review you might migrate still-relevant tasks here
But you're right - having it as an alternate capture point violates the principle of rapid logging



This reminds me of the GTD principle of having a single inbox. By suggesting tasks might start in either daily logs OR monthly task list, I was creating unnecessary decision points during capture.
Would you like me to revise the guide to reflect this? The monthly spread might need rethinking - either clarifying its actual role or perhaps recognizing that some BuJo components might not serve our state-management needs.RetrySMLet's figure out or decisions first. What happens with uncompleted tasks on a daily log after the day is over?Ah yes - this is a crucial state transition question. During the next morning's routine, you have to make decisions about uncompleted tasks from the previous day(s):
For each uncompleted task (•), you need to decide:

Still relevant/needs to be done?

Either migrate forward (>) to today's daily log
Or needs to be intentionally deferred to future


No longer relevant?

Cross out (×) or strike through



This is where the monthly task list might actually make sense - as a destination for tasks that:

Are still relevant but don't need to be staring at you every day
Would otherwise be repeatedly migrated forward in daily logs
You want to keep "in play" but not cluttering daily view

So rather than being a starting point for tasks, the monthly task list could be a place where some tasks migrate TO during this decision process. It becomes a kind of "holding pattern" for relevant but not immediate tasks.
Does this feel more aligned with the rapid logging principle while still maintaining clear state tracking? Would you like to explore how this decision flow might work in practice?RetrySMYes, that's where I was going intuitively I think. <Moving on, but can't enter a blank line in this interface> Should I make a distinction like the GTD action/project distinction? If not, what's the mechanism in bujo ensuring they don't get lost?The interface issue is noted!
On your question - this gets at a key state-tracking concern. GTD's action/project distinction helps ensure forward movement by making sure every project has a next action and nothing falls into a limbo state.
In BuJo, you could:

Not make the distinction formally, but rely on:

Regular migration forcing you to confront items
If you keep migrating something without progress, it might signal it's actually a project needing breakdown
The "friction" of rewriting during migration becomes a feature here


Or make it more explicit through:

Collections for projects
Breaking down projects in collections
Threading to link project collections to next actions in daily/monthly logs
Signifiers to mark project-related tasks



The risk without an explicit distinction is that complex items might:

Keep getting migrated without progress
Miss dependencies or prerequisites
Lack clear next actions

What are your thoughts on whether the migration mechanism provides enough protection against these risks, or whether we need more explicit project tracking?RetrySMMy intuition is that if I don't distinguish them I will feel like I am throwing away type information, in the computer science sense. Like the granular types would be Task and AtomicTask, which "is a" Task but I access them all only with base class pointers or references.That's a brilliant way to frame it! The type system analogy really clarifies the issue.
If we treat everything as just "Task", we're essentially working with:
typescriptclass Task {
  description: string;
  status: Status;
  // ... other common properties
}
When really we have something more like:
typescriptabstract class Task {
  description: string;
  status: Status;
}

class AtomicTask extends Task {
  // Can be completed directly
}

class ProjectTask extends Task {
  subtasks: Task[];  // Recursive structure
  nextAction: AtomicTask;
}
And by not distinguishing them in our notation, we're losing that type information and the invariants it could help us maintain (like "every ProjectTask must have a nextAction").
So perhaps we need:

A way to mark this distinction in rapid logging

Maybe a different bullet shape?
Or a project signifier?


A process ensuring ProjectTasks get proper handling

Migration becomes like type checking
Can't just migrate a ProjectTask without ensuring its nextAction is clear


Collections could be where we restore the type information

Project collections maintain the full structure
Daily/monthly logs show the flattened view but maintain type markers



Does this resonate with your programming-minded view of it? Should we revise the practical guide to make these distinctions explicit?RetrySMBut, I am also wary of premature customization.Ah yes - that's a really good instinct. Like in software, we should probably:

Start with the vanilla system

Learn how it works in practice
See where the pain points actually are
Let patterns emerge naturally


Before adding type distinctions, observe:

Are projects actually getting stuck?
Is the basic migration mechanism catching things?
What natural patterns emerge in how we mark or handle different types of tasks?



This fits with BuJo's philosophy of evolution through use, rather than GTD's more prescribed structure. We can always add type information later if we find we really need it.
Would you like me to revise the practical guide to:

Start with basic bullets only
Note where we might later add distinctions
Include observation points ("pay attention to how you handle complex tasks")
Suggest review questions to help identify when/if type distinction becomes necessary?

The goal would be to avoid premature optimization while maintaining awareness of potential future needs.RetrySMStill working through questions. What would I do with a multi month project (in the normal English sense) with no specific due date/month?In our state management perspective, this is an interesting case because it needs to:

Remain "in the system" (not get lost)
Generate actionable tasks at the right times
Not clutter daily/monthly views unnecessarily

Options could be:

Future Log

But this feels wrong because it's not actually time-bound
Would artificially force it into a month


Create a Collection

Give it a dedicated space
Break down components/phases
Thread to daily/monthly logs for active pieces
Index makes it findable


Some hybrid where:

Collection holds the full project state
Current action items migrate through daily logs
Monthly review includes checking project collections for next steps



I'm leaning toward Collections being the right home for this - it maintains state without forcing artificial temporality. But I'm curious about your thoughts on how to ensure these projects stay "alive" in the system without depending on temporal triggers?
Maybe this connects back to the type question - this kind of project might be where we first feel the need for that distinction.RetrySMIt needs to go somewhere that is regularly reviewed and I don't think we can let those places proliferate.Ah yes - that's crucial! The system needs regular, comprehensive review points without making us check too many different places.
This suggests maybe we need:

A very limited set of "active review surfaces"

Daily log (daily review)
Monthly log (monthly review)
Future log (monthly review)
Maybe ONE other place for these non-temporal projects?



The issue with putting such projects only in Collections is exactly what you've identified - they might not get reviewed regularly enough unless we explicitly add "check all project collections" to our review process, which:

Adds cognitive overhead
Risks missing things
Could proliferate as you note

So maybe we need:

Either a designated space specifically for active non-temporal projects that gets reviewed monthly
Or ensure these projects always have some representation in our temporal review spaces (monthly/future log) even if artificial

This gets at a core tension - the system needs to be complete (capture everything) but also consolidated (limited review points). Would you like to explore these options further? The key seems to be finding the right balance between completeness and maintainable review processes.RetrySMSeems like we just argued our way into there being a Projects list/collection.Ha! Yes we did - and through a very natural chain of reasoning:

Need complete state tracking
Need regular review
Can't proliferate review points
Some things don't fit naturally in temporal collections
Therefore... we need a Projects collection!

This actually maps nicely to why GTD has a Projects list too - not because David Allen arbitrarily decided it, but because it solves these exact structural needs:

Single review point for non-temporal projects
Clear home for things that would otherwise float
Part of regular review cycle
Prevents losing track of bigger items

So in our BuJo implementation, we might want:

A Projects collection

One of our core review surfaces
Reviewed during monthly review
Projects can have their own collections for details
But their existence is tracked here



Would you like to work through:

How this fits into the rapid logging flow?
How it interacts with daily/monthly logs?
What the review process looks like?
Whether we need any special notation or just regular bullets?
RetrySMIn that case, I'm inclined to choose an icon to represent projects (multi step tasks) which can be used in rapid logging and eventually get migrated to the projects list/collection. Ideally it would be somewhat visually similar to the task's dot and amenable to cross outs for completion and migration. And could go to monthly log or future log if it did actually have a completion time associated.Yes! This feels like a natural evolution - we discovered we need the Projects list, and now we can add minimal notation to support it effectively.
For the project bullet, we want something that:

Is quick to write (rapid logging)
Visually relates to the task dot (•)
Works with the standard modifications:

Can be crossed (×) for completion
Can take the migration arrow (>)
Can take other signifiers (*, !, etc.)



Some possibilities:

⊙ (dot within circle) - shows containment
◐ (half circle) - like a dot that grew
⊗ (dotted circle) - very clear when crossed
◎ (circle with dot) - clear relationship to •

The first or last might be best since they:

Maintain the dot concept
Show the "container" nature of a project
Are relatively quick to write
Look clear when crossed or arrowed

Then during migration/review:

If temporal -> Future/Monthly log
If not -> Projects collection
Either way, might spawn atomic tasks (•) in daily logs

Would you like to try incorporating this into our system? We could work through exactly how it flows in practice.RetrySMI think we may be ready. Can you think of any other "holes" from this perspective?Let me think through our key requirements from a state management perspective:

Complete State Tracking:

Rapid capture (daily logs) ✓
Projects tracked (Projects collection) ✓
Temporal commitments (Future/Monthly logs) ✓
Project vs Atomic task distinction (new bullet) ✓
Reference info (Collections) ✓


Clear Processes:

Capture process (rapid logging) ✓
Migration paths defined ✓
Review points established ✓


Decision Support:

Can find current tasks ✓
Can see upcoming commitments ✓
Regular review surfaces limited & defined ✓



Potential holes might be:

Waiting-for tracking

GTD has this explicit - do we need it?
Could be another bullet type or signifier


Dependencies

How do we mark when one task depends on another?
Might need threading/linking notation


Reference trigger

How do we ensure reference material gets reviewed when relevant?
Though maybe Collections + Index handles this



Would you like to address any of these, or do you think we have enough structure to start implementing and let these emerge naturally if needed?RetrySMGood point in waiting-for. Yes, we want that. I am thinking an hourglass notation (half filled/connected X) and @ for "tagging" the person/thing being waited for. Does GTD have a formal dependency tracking mechanism? I do think that while we want a fixed/specied place to list projects, we can have optional collections per project and dependencies could be tracked there.GTD doesn't have a formal dependency mechanism - it handles it mainly through:

Project support materials
Next actions (which implicitly handle linear dependencies)
Calendar (for time dependencies)
Project reviews

I like your thinking here:

⌛ for waiting-for (great visual metaphor and quick to write)
@ for person/thing (familiar from email/social media)
Keeping dependencies in optional project collections rather than the core system

This maintains:

Rapid logging (quick symbols)
Clean state tracking (waiting items clearly marked)
Core/optional split (base system stays simple)
Flexibility (detailed tracking available when needed)

And the waiting-for notation gives us:

Clear status in daily logs
Easy to spot during review
Natural migration path (keeps migrating until resolved)
Works with both tasks and projects (⌛• or ⌛⊙)

Do you want to lock this in and write up the complete system? We've got:

Basic bullets (• − ○)
Projects (⊙)
Waiting (⌛ + @)
Core collections (Daily, Monthly, Future, Projects)
Optional project collections for details/dependencies
RetrySMYes!Great! Let's create a complete guide that captures everything we've worked out. This should cover both the conceptual framework and the concrete implementation.Bullet Journal: A Complete SystemDocument # Bullet Journal: A Complete System

## Core Principles
- Complete state tracking
- Rapid capture
- Clear review surfaces
- Sustainable maintenance

## Basic Notation

### Core Bullets
- • Task (atomic, single-step)
- ⊙ Project (multi-step)
- ○ EventThis represents our complete system - maintaining the state management perspective while providing practical implementation details. It captures our key decisions about:

Project vs Task distinction
Waiting-for tracking
Limited review surfaces
Migration paths
Core vs optional components

Would you like to:

Review any specific section in more detail?
Add examples of common scenarios?
Develop specific collection templates?
Create a quick-start guide?
RetrySMThis is great. I have one pretty different other thing to do to wrap up. To make it easier to think about and compare both systems, can you now write a guide in this same spirit for GTD? So I'll have parallel descriptions of each in similar styles and spirits. (But only to the extent possible. We don't want to cram things into a shape they really don't fit.)Yes! Let's write a GTD guide through our state-management lens, acknowledging both where the parallel structure works and where GTD's nature demands different treatment.GTD: A Complete SystemDocument # GTD: A Complete System

## Core Principles
- Complete state capture
- Clear next actions
- Trusted system
- Regular review
- Appropriate engagement

## State Components

### Core Lists (Required)
- Inbox (capture)
- Next Actions (by context)
- ProjThe parallel structure helps highlight some key differences:

State Transitions:

BuJo: Primarily through migration
GTD: Through processing workflow


Capture:

BuJo: Rapid logging in daily log
GTD: Any capture tool to inbox


Project Handling:

BuJo: Marked and tracked, but flexible
GTD: Strict definition and handling


Time Dimension:

BuJo: Temporal organization primary
GTD: Context organization primary



Would you like to explore any of these differences further, or should we refine either guide to make the parallels/differences clearer?