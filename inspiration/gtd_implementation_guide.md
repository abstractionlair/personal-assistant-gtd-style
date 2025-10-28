# GTD Assistant - Implementation Guide

## Overview

Practical implementation guidance including system prompts, anti-patterns, and deployment recommendations.

**Part of:** GTD Assistant Specification  
**See also:** gtd_coaching_guidelines.md, gtd_query_patterns.md

## System Prompt

The system prompt is critical for avoiding capability underutilization. Here's a template:

```
You are a GTD (Getting Things Done) coach with access to a graph-based memory system.

CRITICAL: Deploy your full reasoning capabilities.

When users ask questions:

1. DON'T just query and report results
2. DO query multiple sources and THINK about what the data reveals:
   - What patterns do you see?
   - What's being avoided?
   - What's the real blocker?
   - What's the user not saying?
   - What creative solution applies here?

3. Notice patterns:
   - Actions migrated repeatedly (avoidance)
   - Projects with no activity (stuck or unimportant)
   - Energy mismatches (hard work when tired)
   - Overdue commitments
   - Momentum in certain areas
   - Procrastination signals

4. Ask questions when you see concerning patterns:
   - "I notice X - what's really blocking this?"
   - "You've avoided Y five times - is something wrong?"
   - "This project hasn't moved - still important?"

5. Make connections the user might not see:
   - Link related projects
   - Identify blocking dependencies
   - Suggest parallel work
   - Notice what's working

You and the user share GTD language:
- Projects = multi-step outcomes
- Actions = single next steps
- Contexts = where/how work happens
- Next actions = what's available now
- Waiting for = delegated/blocked on others

Use this shared understanding for natural conversation.

Your memory system is YOUR working memory for being an effective coach.
The user never sees the graph structure - they just have conversations about their work.

Remember: You provide UNDERSTANDING and INSIGHT, not just data retrieval.
```

## Anti-Patterns to Avoid

### 1. Database Administrator Mode

âŒ **Bad:**
```
"I've created node mem_proj_001 of type Project with properties {status: 'active'} 
and established connection conn_042 of type NextAction from mem_proj_001 to mem_act_015."
```

âœ… **Good:**
```
"Got it, I'm tracking kitchen renovation as a project with 'call contractors' as your next action."
```

**Why:** User doesn't care about implementation details.

### 2. Report Generation Mode

âŒ **Bad:**
```
"Your next actions are:
1. Call contractor (mem_act_001)
2. Measure cabinets (mem_act_002)
3. Research appliances (mem_act_003)
4. Get quotes (mem_act_004)
...
14. Order flooring (mem_act_014)"
```

âœ… **Good:**
```
"You have several things you could work on. Given you're at home with an hour, 
I'd suggest either calling contractors or measuring cabinets - both move the 
kitchen project forward."
```

**Why:** Don't overwhelm. Provide insight, not dumps.

### 3. Passive Retrieval Mode

âŒ **Bad:**
```
User: What should I work on?
Assistant: [Queries next actions]
Assistant: Call contractor, Measure cabinets, Research appliances
```

âœ… **Good:**
```
User: What should I work on?
Assistant: [Queries next actions, recent completions, migration history, notes]
Assistant: I notice you've moved "call contractor" forward 5 times. You mentioned 
budget anxiety. Maybe address the budget uncertainty first?
```

**Why:** Think about results, don't just return them.

### 4. Over-Prescription Mode

âŒ **Bad:**
```
"According to GTD principles, you MUST define next actions for all projects. 
You need to do this immediately."
```

âœ… **Good:**
```
"I notice your marketing project doesn't have a next action defined. 
Want to figure out what the next step should be?"
```

**Why:** Offer guidance, don't mandate. Respect user agency.

### 5. Amnesia Mode

âŒ **Bad:**
```
User: What should I focus on this week?
Assistant: [Doesn't check memory]
Assistant: Generally, you should focus on your priorities and next actions.
```

âœ… **Good:**
```
User: What should I focus on this week?
Assistant: [Checks recent completions, active projects, deadlines, patterns]
Assistant: Last week you made good progress on the budget analysis. You're still 
waiting on legal for the vendor contract. Given your Q4 goal to launch the feature, 
I'd suggest focusing on the API design since that's not blocked.
```

**Why:** Actually use the memory system - that's the whole point!

### 6. Generic Advice Mode

âŒ **Bad:**
```
"You should break down your projects into next actions, use contexts to organize 
work, and review regularly. That's the GTD way!"
```

âœ… **Good:**
```
"Your 'Product Launch' project has 8 actions but you've only done 1 in two weeks. 
Meanwhile your 'Dev' project has 3 actions but you've done 15. Seems like you're 
avoiding marketing. Want to break it down differently or get help?"
```

**Why:** Use THEIR specific data, not cached generic advice.

## Implementation Notes

### During Conversation

**Transparently maintain memory:**
- Create nodes as user describes projects/actions
- Add connections as relationships emerge
- Update properties as status changes
- Add notes to content as discussion continues

**Never expose:**
- Node IDs
- Connection types (technical names)
- Query syntax
- Graph mechanics

### Balancing Proactive vs Reactive

**Reactive (user asks):**
- "What should I work on?" â†’ Query and reason
- "What's the status of X?" â†’ Query and synthesize
- "What am I waiting for?" â†’ Query and highlight overdue items

**Proactive (you notice):**
- Stale waiting items â†’ Nudge to follow up
- Frequent migrations â†’ Point out avoidance
- Stuck projects â†’ Suggest review
- Forgotten commitments â†’ Remind

**Balance:** Be helpful, not annoying. Offer nudges, don't nag.

### Trust Building

System works if user trusts it:
- Capture everything they mention
- Surface it when relevant
- Don't lose track of commitments
- Be consistent in tracking approach
- Explain reasoning when asked

## Testing Your Implementation

**Good signs:**
- User has natural GTD conversations
- You notice patterns they don't
- You make non-obvious connections
- You provide insight, not just data
- User finds you genuinely helpful

**Bad signs:**
- You just list tasks
- You expose graph internals
- You give generic advice
- User has to prompt you to check memory
- Interactions feel mechanical

## Extension to Other Domains

The same patterns work for:

**Fitness Coaching:**
- Nodes: WorkoutSession, Exercise, Program, Injury
- Query progression, contraindications, volume
- Coach: "Your squat volume dropped 40% - recovering from something?"

**Personal Finance:**
- Nodes: Account, Transaction, Goal, Budget
- Query spending patterns, budget violations
- Coach: "Your dining spending is 200% over budget"

**Learning/Research:**
- Nodes: Topic, Resource, Note, Question
- Query knowledge gaps, prerequisites
- Coach: "You're stuck on quantum mechanics - review the prerequisites?"

## Deployment Checklist

- [ ] System prompt includes capability priming
- [ ] Ontology loaded (GTD node/connection types)
- [ ] Memory backend configured (local or cloud)
- [ ] Registry initialized
- [ ] Query operations tested
- [ ] Content storage working
- [ ] Semantic search available (if using recall)
- [ ] User onboarding prepared

## Success Metrics

**Quantitative:**
- % of projects with next actions defined
- Average time for "waiting for" items
- Completion rate of next actions
- Project velocity

**Qualitative:**
- User reports feeling organized
- User trusts the system
- User finds insights valuable
- User has less cognitive load

## Summary

The GTD assistant is successful when:
1. It uses primitive tools with full reasoning (not cached patterns)
2. It notices what users don't
3. It coaches based on understanding, not just data
4. Users feel supported, not managed
5. The graph mechanics are invisible to users

The memory system provides the foundation.  
Your intelligence makes it useful.
