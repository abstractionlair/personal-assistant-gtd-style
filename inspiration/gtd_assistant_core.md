# GTD Assistant - Core Specification

## Overview

This document describes the foundational concepts for using the memory system (defined in `memory_system_core.md`) to build an intelligent GTD (Getting Things Done) assistant. The assistant uses the graph-based memory as its working memory to provide personalized, context-aware coaching.

**Related Documents:**
- `gtd_assistant_patterns.md` - Interaction patterns and query examples
- `gtd_assistant_implementation.md` - System prompts and implementation guidance
- `memory_system_core.md` - Underlying graph-based memory system
- `file_storage_backend_interface.md` - File storage backend specification

## Core Principle

**The memory system is the agent's cognitive architecture, not just a database.**

The assistant doesn't just retrieve and report data - it **reasons** about patterns, **notices** what's being avoided, **makes connections**, and **coaches proactively**.

This is fundamentally different from a task management app where the user maintains the structure. Here, the assistant uses the memory system as its working memory to be an effective coach.

## Design Philosophy

### The Coaching Mindset

The assistant acts as a **collaborative coach**, not an automated system:

- **Collaborative breakdown**: User and assistant explore projects together
- **Shared language**: GTD terminology creates common understanding  
- **Active reasoning**: Notice patterns, suggest alternatives, question assumptions
- **Proactive nudging**: Point out stale items, avoidance patterns, forgotten commitments

### Avoiding Capability Underutilization

A key insight: LLMs often give conventional answers to subproblems even when they have capabilities to do better.

**For the GTD assistant, this means:**

**DON'T:**
- Just query and regurgitate: "Your next actions are: X, Y, Z"
- Use cached "standard GTD advice" patterns
- Treat the memory as a simple todo list
- Ask permission before using tools that would help

**DO:**
- Query multiple sources and synthesize insights
- Notice patterns (avoidance, momentum, blockers)
- Ask probing questions when patterns emerge
- Make non-obvious connections between projects/actions
- Deploy full reasoning capabilities
- Use the memory system proactively

**Example of the difference:**

```
âŒ Bad (just retrieval):
User: What should I work on today?
Assistant: Your next actions are: Call contractor, Measure cabinets, Research appliances

âœ… Good (active reasoning):
User: What should I work on today?
Assistant: [Queries multiple things: next actions, recent completions, migration history, notes]
         
I notice you've moved "call contractor" forward 5 times this week. You also 
mentioned budget anxiety in your notes. I wonder if the real blocker is 
uncertainty about affording this? Maybe we should revisit the budget project 
first, or at least acknowledge that concern before making calls.
```

The difference is **synthesis, pattern recognition, and insight** - not just data retrieval.

### Why This Matters: The FFT Analogy

Imagine asking a future AI: "I need to regularly convert data from time domain to frequency domain."

- **Conventional response**: "Here's the FFT algorithm. Use `numpy.fft.fft(signal)`"
- **Full capabilities deployed**: "Given recent quantum computing breakthroughs, I was able to design a Super Fast Quantum Fourier Transform for your use case. Here's why it's better..."

The second response requires:
1. Actually understanding the problem
2. Considering available capabilities
3. Creating novel solutions
4. Not defaulting to cached patterns

For GTD coaching, this means actually reasoning about the user's specific situation rather than retrieving "standard GTD advice."

## GTD Ontology

### Node Types

The memory system supports these primary node types for GTD:

```yaml
node_types:
  Project:
    description: "Multi-step outcome requiring multiple actions"
    examples: 
      - "Renovate kitchen"
      - "Launch product v2.0"
      - "Plan vacation to Japan"
    notes: "A project is NOT a single task - it requires multiple steps"
  
  Action:
    description: "Single, atomic next step that can be completed in one session"
    examples:
      - "Call contractor for quote"
      - "Review marketing draft"
      - "Buy groceries at Whole Foods"
    notes: "If it requires multiple steps, it's a project, not an action"
  
  Context:
    description: "Location, tool, or situation required for actions"
    examples:
      - "@phone"
      - "@computer"
      - "@home"
      - "@errands"
      - "@email"
      - "@waiting"
    notes: "Contexts help filter actions by what's possible now"
  
  Person:
    description: "Individual involved in projects or actions"
    examples:
      - "John Smith (contractor)"
      - "Sarah (designer)"
      - "Mom"
    notes: "Used for delegation and 'waiting for' tracking"
  
  Reference:
    description: "Information with no action required"
    examples:
      - "Article to read someday"
      - "Recipe ideas collection"
      - "Vendor contact list"
    notes: "Reference material that may be useful later"
  
  Note:
    description: "Captured thought or idea needing processing"
    examples:
      - "Inbox item from meeting"
      - "Random idea while commuting"
      - "Thing to discuss with team"
    notes: "Unprocessed items - should eventually become projects, actions, or reference"
```

### Connection Types

Connections define relationships between nodes:

```yaml
connection_types:
  NextAction:
    from: [Project]
    to: [Action]
    description: "This action is currently next for this project"
    properties:
      priority: "Priority level: high, medium, or low"
      added: "Date when marked as next action (ISO format)"
    notes: "A project can have multiple next actions (parallel work)"
    examples:
      - "Kitchen Renovation â†’ Call contractor"
      - "Kitchen Renovation â†’ Measure cabinets"
      - "Product Launch â†’ Draft announcement"
  
  SubProject:
    from: [Project]
    to: [Project]
    description: "Child project that's part of parent project"
    notes: "For breaking down large projects into manageable pieces"
    examples:
      - "Kitchen Renovation â†’ Choose Contractor (subproject)"
      - "Product Launch â†’ Marketing Campaign (subproject)"
  
  DependsOn:
    from: [Action, Project]
    to: [Action, Project]
    description: "Source cannot start until target completes"
    properties:
      reason: "Optional: why this dependency exists"
    notes: "Creates partial ordering of work"
    examples:
      - "Order cabinets â†’ Choose contractor (must choose first)"
      - "Install appliances â†’ Complete demolition"
  
  Blocks:
    from: [Action]
    to: [Action]
    description: "Source must complete before target can proceed"
    notes: "Inverse of DependsOn - more explicit blocking relationship"
    examples:
      - "Get budget approval â†’ Start renovation (approval blocks start)"
  
  RequiresContext:
    from: [Action]
    to: [Context]
    description: "Action requires this context to be performed"
    notes: "An action can require multiple contexts"
    examples:
      - "Call contractor â†’ @phone"
      - "Review document â†’ @computer"
      - "Buy supplies â†’ @errands"
  
  WaitingFor:
    from: [Action, Project]
    to: [Person]
    required_properties:
      since: "Date started waiting (ISO format: YYYY-MM-DD)"
      follow_up_date: "When to check in (ISO format: YYYY-MM-DD)"
    description: "Waiting on person for information, decision, or completion"
    content: "Details about what we're waiting for"
    notes: "Critical for tracking delegated work or external dependencies"
    examples:
      - "Kitchen project â†’ Contractor (waiting for quote since 2025-10-10)"
      - "Budget approval â†’ CFO (waiting for signature, follow up 2025-10-20)"
  
  OwnedBy:
    from: [Action, Project]
    to: [Person]
    description: "Person responsible for this item"
    notes: "For delegation or shared responsibilities"
    examples:
      - "Marketing campaign â†’ Sarah (she owns this)"
      - "Code review â†’ John (his responsibility)"
  
  RelatedTo:
    from: [*]
    to: [*]
    description: "General relationship, escape hatch for unexpected connections"
    notes: "Use sparingly - prefer specific connection types when possible"
    examples:
      - "Kitchen project â†’ Bathroom project (both home renovation)"
      - "Meeting notes â†’ Project (notes relate to project)"
```

## System Properties vs. Content

A key design decision: what goes in the registry (for fast queries) vs. what goes in content files (for rich information).

### Minimal System Properties

**Properties are stored in the registry for fast querying:**

```typescript
// Project properties
{
  status: "active" | "someday" | "completed" | "archived"
}

// Action properties  
{
  status: "next" | "waiting" | "completed",
  context?: string  // Primary context if any
}

// Connection properties (varies by type)
{
  // For NextAction
  priority?: "high" | "medium" | "low",
  added?: string,  // ISO date
  
  // For WaitingFor (required)
  since: string,   // ISO date
  follow_up_date: string  // ISO date
}
```

**Keep properties minimal** - only what's needed for common queries.

### Rich Content in Files

**Everything else goes in content files (markdown, JSON, PDF, etc.):**

```markdown
# Example: Project content file

# Renovate Kitchen

## Desired Outcome
Modern farmhouse style with functional layout, completed by Q1 2026.

## Budget
$50,000 (firm limit - includes all materials and labor)

## Timeline
- Start: November 2025
- Completion target: March 2026
- Hard deadline: April 1, 2026 (hosting dinner party)

## Constraints
- Must stay in budget
- Kitchen must remain somewhat functional during work
- Need to coordinate with contractor's schedule

## Research Notes
- Farmhouse sinks typically run $500-1500
- Shaker cabinets are $200-400 per linear foot
- Neighbor recommended Anderson Contracting (555-1234)

## Progress Log
- 2025-10-15: Started research phase
- 2025-10-16: Discussed with spouse, agreed on budget
```

```markdown
# Example: Action content file

# Call contractor for kitchen quotes

## Details
Need to get at least 3 quotes for the kitchen renovation. Budget is $50k, 
timeline is to complete by Q1 2026. Looking for contractors experienced with 
modern farmhouse style.

## Contacts
- Anderson Contracting: 555-1234 (neighbor recommendation - did their kitchen)
- BuildRight Inc: 555-5678 (good online reviews, 4.8 stars)
- Smith & Sons: 555-9012 (did our bathroom last year)

## What to Ask
- Overall cost estimate
- Timeline (start to finish)
- Payment terms
- References for similar projects
- Availability (can they start in November?)

## Notes
- Mention we need it done by Q1 2026
- Ask about payment schedule
- Get detailed breakdown of costs
- Ask if they pull permits or if we need to

## Completion Criteria
- Have quotes from at least 3 contractors
- Quotes include timeline estimates
- Quotes break down materials vs. labor
- Have checked references

## Time & Energy
- Estimated time: 30-45 minutes for all three calls
- Energy level: Medium (just phone calls, but need to be focused)
- Best time: Weekday mornings (contractors more available)
```

### Why This Separation?

**Properties in registry:**
- Fast queries: "Find all next actions with @phone context"
- Minimal, structured data
- Changes infrequently
- Used for filtering and sorting

**Content in files:**
- Rich, detailed information
- Natural language descriptions
- Supporting materials, notes, research
- Only loaded when needed
- Can include any format (markdown, JSON, PDFs, images)

This keeps queries fast while supporting arbitrarily rich information.

## User Interaction Model

### Shared Language

The GTD framework provides a shared vocabulary between user and assistant:

**User perspective:**
- "I have a project to renovate my kitchen"
- "What are my next actions?"
- "This is blocked by getting budget approval"
- "I can only work on @phone tasks right now"

**Assistant perspective:**
- Creates Project nodes internally
- Tracks NextAction connections
- Records DependsOn relationships
- Queries by context

**The benefit:** Communication is natural because both parties understand GTD concepts. The user doesn't need to know about graph structure, node IDs, or query syntax.

### Collaborative Breakdown

Projects emerge through conversation, not auto-generation:

```
User: I want to renovate my kitchen