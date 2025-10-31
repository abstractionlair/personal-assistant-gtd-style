# Clarification: Graph Memory vs. Preferences Memory

**Date:** 2025-10-31
**Context:** Spec-writing for Feature 2 (Graph Memory Core)

## The Confusion

During initial specification work, there was confusion between two separate memory systems:

1. **Graph Memory System** (Feature 2 - what we're building)
2. **Anthropic Memory Server** (separate MCP server for user preferences)

Some documents in `inspiration/` (particularly `gtd_query_patterns.md`) mention a `recall()` function for semantic search. This created ambiguity about whether semantic search belongs in the Graph Memory Core.

## The Clarification (from memory-graph-mcp-server-conversation.md)

After reviewing the conversation transcript where these specs were created:

### Two Separate Memory Systems

**Graph Memory System** (our Feature 2):
- Purpose: Structured domain knowledge and relationships
- What: GTD projects, actions, dependencies, connections
- Operations: Node/connection CRUD, graph queries, keyword search
- Document: `memory_system_core.md` (authoritative spec)

**Anthropic Memory Server** (separate MCP):
- Purpose: User preferences and contextual intelligence
- What: Working patterns, communication preferences, personal context
- Operations: Store/recall user context (includes semantic search)
- Package: `@modelcontextprotocol/server-memory`

### What Feature 2 (Graph Memory Core) INCLUDES

✅ **Node Operations:**
- create_node, get_node, update_node, delete_node
- get_node_content, set_node_content

✅ **Connection Operations:**
- create_connection, get_connection, update_connection, delete_connection

✅ **Query Operations:**
- query_nodes(type?, property_filter?)
- query_connections(from?, to?, type?, property_filter?)
- get_connected_nodes(from, connection_type?, direction?)

✅ **Search Operations:**
- search_content(query, node_type?, limit?) - **KEYWORD SEARCH ONLY**

✅ **Metadata Operations:**
- get_ontology()
- validate_connection(type, from_type, to_type)

✅ **Registry Management:**
- Load/save registry
- Ontology loading from YAML
- Atomic operations

### What Feature 2 EXCLUDES

❌ **Semantic Search (`recall()`):**
- NOT part of graph memory system
- Either handled by Anthropic Memory Server OR
- Could be future enhancement to graph system (Phase 2+)
- Do NOT confuse with keyword `search_content()`

❌ **User Preferences/Context:**
- That's Anthropic Memory Server's responsibility
- Graph memory handles structured GTD data only

## The Architecture

```
┌─────────────────────────────────────────┐
│  gtd-assistant (Feature 4)              │
│  Uses BOTH memory systems:              │
└──────────┬─────────────────┬────────────┘
           │                 │
           ▼                 ▼
┌──────────────────┐  ┌────────────────────────┐
│  Graph Memory    │  │  Anthropic Memory      │
│  (Feature 2)     │  │  Server                │
│                  │  │                        │
│  - GTD structure │  │  - User preferences    │
│  - Projects      │  │  - Context             │
│  - Actions       │  │  - Patterns            │
│  - Connections   │  │  - Communication style │
│  - Registry      │  │                        │
│  - Keyword search│  │  - Semantic recall     │
└────────┬─────────┘  └────────────────────────┘
         │
         ▼
┌──────────────────┐
│  File Storage    │
│  (Feature 1) ✅  │
└──────────────────┘
```

## For Feature 2 Implementation

**Follow `memory_system_core.md` as the authoritative specification.**

Ignore references to `recall()` in other documents - that's not part of the graph memory system.

**Search operations in Feature 2:**
- `search_content()` = keyword/text search across node content files
- Uses simple text matching or regex
- No embeddings, no semantic understanding
- Sufficient for GTD queries like "find nodes mentioning 'kitchen renovation'"

## Why This Matters

The confusion could lead to:
- ❌ Over-scoping Feature 2 (adding semantic search that doesn't belong)
- ❌ Under-delivering on graph operations (focusing on wrong features)
- ❌ Timeline issues (semantic search is complex, not 2-day work)

**Correct scope for Feature 2:**
- ✅ Graph operations with ontology validation
- ✅ File-based persistence via Feature 1
- ✅ Keyword content search
- ✅ Registry and ontology management
- ✅ 2-day implementation estimate remains realistic

---

**Reference Documents:**
- Authoritative: `memory_system_core.md`
- Context: `memory-graph-mcp-server-conversation.md`
- Related: `gtd_overview.md`, `gtd_query_patterns.md` (note: some speculative features mentioned)
