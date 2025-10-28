# GTD Assistant Specification - README

## Overview

Complete specification for building an intelligent GTD (Getting Things Done) assistant using a graph-based memory system. The system acts as a collaborative coach, not just a task manager.

## All Documents

### ðŸ“š Start Here

**[gtd_overview.md](computer:///mnt/user-data/outputs/gtd_overview.md)** - Complete overview and navigation guide

**[gtd_specification_status.md](computer:///mnt/user-data/outputs/gtd_specification_status.md)** - What's included and completion status

### ðŸ—ï¸ Foundation Layer

**[memory_system_core.md](computer:///mnt/user-data/uploads/memory_system_core.md)** - Graph-based memory architecture
- Nodes, connections, registry
- Core operations and queries
- Ontology structure
- Invariants

**[file_storage_backend_interface.md](computer:///mnt/user-data/uploads/file_storage_backend_interface.md)** - File storage backend
- Six file operations (matching Anthropic spec)
- Local implementation
- Future Anthropic Memory Tool adapter

### ðŸŽ¯ GTD Application Layer

**[gtd_assistant_core.md](computer:///mnt/user-data/outputs/gtd_assistant_core.md)** - Core philosophy and ontology
- Design philosophy
- GTD node types (Project, Action, Context, Person, etc.)
- GTD connection types (NextAction, DependsOn, etc.)
- Properties vs content separation

**[gtd_interaction_principles.md](computer:///mnt/user-data/outputs/gtd_interaction_principles.md)** - How to interact
- 7 core principles
- Collaborative vs automated
- Active reasoning over retrieval
- Proactive coaching

**[gtd_query_patterns.md](computer:///mnt/user-data/outputs/gtd_query_patterns.md)** - How to compose queries
- Finding available actions
- Detecting stuck projects
- Identifying avoidance
- Context-based recommendations
- Code examples

**[gtd_coaching_guidelines.md](computer:///mnt/user-data/outputs/gtd_coaching_guidelines.md)** - How to coach effectively
- The coaching stance
- What to notice
- How to coach
- What to avoid
- Weekly/daily patterns

**[gtd_implementation_guide.md](computer:///mnt/user-data/outputs/gtd_implementation_guide.md)** - Implementation details
- System prompt template
- Anti-patterns to avoid
- Implementation notes
- Testing guidance
- Extension to other domains

## Quick Start

### For Developers

1. Read **memory_system_core.md** - understand architecture
2. Read **file_storage_backend_interface.md** - implement backend
3. Read **gtd_assistant_core.md** - understand GTD layer
4. Use patterns from **gtd_query_patterns.md**

### For Implementers

1. Read **gtd_overview.md** - get oriented
2. Read **gtd_interaction_principles.md** - understand approach
3. Copy system prompt from **gtd_implementation_guide.md**
4. Reference **gtd_coaching_guidelines.md** when coaching

### For Researchers

1. Read **gtd_assistant_core.md** - philosophy and rationale
2. Read **gtd_interaction_principles.md** - avoiding capability underutilization
3. Read **gtd_query_patterns.md** - composition over prescription

## Key Concepts

### The Core Principle

The memory system is the agent's **cognitive architecture**, not just a database.

The assistant:
- âœ… Reasons about patterns
- âœ… Notices what's avoided
- âœ… Makes connections
- âœ… Coaches proactively
- âŒ Doesn't just retrieve and report

### Avoiding Capability Underutilization

LLMs often give conventional answers even when capable of better.

**Solution:** Prime with system prompt to deploy full reasoning capabilities.

### Architecture

```
Graph Layer (nodes + connections)
       â†“
File Storage Backend (6 operations)
       â†“
Local Files / Anthropic Memory Tool
```

### GTD Ontology

**Nodes:** Project, Action, Context, Person, Reference, Note

**Connections:** NextAction, SubProject, DependsOn, Blocks, RequiresContext, WaitingFor, etc.

**Properties:** Minimal (in registry for fast queries)

**Content:** Rich (in files, loaded on demand)

## What's Complete

âœ… Complete architecture specification
âœ… Complete GTD ontology
âœ… Core principles and philosophy
âœ… Query patterns with code examples
âœ… Coaching guidelines
âœ… Implementation guide with system prompt
âœ… Anti-patterns documentation
âœ… Quick reference

## What's Reference

The uploaded **gtd_assistant_remaining_sections.md** provides additional guidance on:
- Extended conversation examples
- More query algorithm variations
- Additional pattern detection heuristics
- System prompt variations
- Detailed domain extensions

Use this as inspiration for training examples, documentation, and testing.

## Modular Design

Each document is focused and standalone:
- Easier to understand
- Simpler to maintain
- Avoids size limits
- Supports different audiences

## Next Steps

1. **Choose backend** (local files or Anthropic Memory Tool)
2. **Implement memory system** (from memory_system_core.md)
3. **Load GTD ontology** (from gtd_assistant_core.md)
4. **Use system prompt** (from gtd_implementation_guide.md)
5. **Test with real scenarios**
6. **Iterate using coaching guidelines**

## Extensions

The same architecture supports other domains:
- **Fitness coaching** (workouts, progression, injuries)
- **Finance** (accounts, budgets, transactions)
- **Learning** (topics, resources, knowledge gaps)

Pattern: primitive operations + domain ontology + intelligent coaching

## Success Criteria

The system works when:
- Users have natural GTD conversations
- Assistant notices patterns users don't
- Assistant provides insight, not just data
- Graph mechanics invisible to users
- Users feel supported, not managed

## Questions?

See **gtd_specification_status.md** for completion details and **gtd_overview.md** for comprehensive navigation.

---

**Version:** 1.0  
**Created:** 2025-10-16  
**Status:** Complete and usable
