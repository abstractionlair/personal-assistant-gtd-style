# GTD Assistant - Complete Specification

## Overview

This specification describes how to build an intelligent GTD (Getting Things Done) assistant using a graph-based memory system. The assistant acts as a collaborative coach, not just a task manager.

## Document Structure

The specification is organized into focused modules:

### Foundation Documents

**1. Memory System Core** (`memory_system_core.md`)
- Graph-based memory architecture
- Nodes, connections, registry
- Core operations and queries
- Backend-agnostic design

**2. File Storage Backend** (`file_storage_backend_interface.md`)
- Six file operations (view, create, str_replace, insert, delete, rename)
- Local file implementation
- Anthropic Memory Tool compatibility

### GTD-Specific Documents

**3. GTD Assistant Core** (`gtd_assistant_core.md`)
- Core philosophy and principles
- GTD ontology (node and connection types)
- Properties vs content separation
- User interaction model

**4. Interaction Principles** (`gtd_interaction_principles.md`)
- Collaborative vs automated approach
- Shared GTD language
- Active reasoning over retrieval
- Proactive coaching
- Transparent memory management

**5. Query Patterns** (`gtd_query_patterns.md`)
- Composing primitive queries
- Finding available actions
- Detecting stuck projects
- Identifying avoidance patterns
- Context-based recommendations

**6. Coaching Guidelines** (`gtd_coaching_guidelines.md`)
- The coaching stance
- What to notice (avoidance, stuck projects, energy mismatches)
- How to coach effectively
- Weekly review patterns
- Executive assistant mode

**7. Implementation Guide** (`gtd_implementation_guide.md`)
- System prompt template
- Anti-patterns to avoid
- Implementation notes
- Testing guidance
- Extension to other domains

## Key Concepts

### The Core Principle

**The memory system is the agent's cognitive architecture, not just a database.**

The assistant doesn't retrieve and report - it reasons, notices, connects, and coaches.

### Avoiding Capability Underutilization

LLMs often give conventional answers even when capable of better.

**Apply this to GTD:**
- Don't retrieve "standard advice"
- Query specific user data and synthesize insights
- Use memory as working memory for understanding the person
- Deploy full reasoning capabilities

### Shared Language

GTD provides common vocabulary:
- Projects = multi-step outcomes
- Actions = single next steps
- Contexts = where/how work happens
- Next Actions = available now
- Waiting For = delegated/blocked

### Query Composition

Use primitive operations flexibly:
```typescript
// Primitives
query_nodes(type?, filter?)
query_connections(from?, to?, type?)
get_connected_nodes(from, type?)
search_content(query)
recall(query)  // Semantic search

// Compose them creatively based on question
// Think about results, don't just return them
```

### Coaching Patterns

**Notice:**
- Avoidance (migrated 3+ times)
- Stuck projects (no activity)
- Energy mismatches
- Overdue commitments

**Coach:**
- Ask questions
- Offer perspective
- Respect agency
- Provide insight

## Getting Started

1. **Read Foundation**
   - memory_system_core.md
   - file_storage_backend_interface.md

2. **Understand GTD Layer**
   - gtd_assistant_core.md
   - gtd_interaction_principles.md

3. **Learn Patterns**
   - gtd_query_patterns.md
   - gtd_coaching_guidelines.md

4. **Implement**
   - gtd_implementation_guide.md
   - Use system prompt template
   - Avoid anti-patterns

## Quick Reference

### Node Types
- Project, Action, Context, Person, Reference, Note

### Connection Types
- NextAction, SubProject, DependsOn, Blocks
- RequiresContext, WaitingFor, OwnedBy, RelatedTo

### Properties (minimal)
- Project: {status: "active" | "someday" | "completed" | "archived"}
- Action: {status: "next" | "waiting" | "completed", context?: string}

### Content (rich)
- Descriptions, notes, details, research
- Stored in markdown/JSON/PDF files
- Only loaded when needed

## Success Criteria

**The system works when:**
- Users have natural GTD conversations
- Assistant notices patterns users don't
- Assistant provides insight, not just data
- Graph mechanics are invisible to users
- Users feel supported, not managed

## Extension to Other Domains

Same architecture supports:
- **Fitness coaching**: Workouts, exercises, progression
- **Finance**: Accounts, transactions, budgets
- **Learning**: Topics, resources, knowledge gaps

The pattern: primitive memory operations + domain ontology + intelligent coaching

## Summary

The GTD assistant combines:
1. **Flexible memory system** (graph + files)
2. **GTD ontology** (shared language)
3. **Intelligent coaching** (full reasoning capabilities)

Result: A coach that understands users' work holistically and helps them stay organized and productive.

## Additional Resources

See the uploaded "remaining sections" document for additional detail on:
- Extended conversation examples
- Advanced query compositions
- Specific avoidance detection algorithms
- Complete system prompt variations
- Domain extension patterns

---

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Status:** Complete
