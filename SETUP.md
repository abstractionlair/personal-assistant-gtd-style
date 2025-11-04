# Personal Assistant GTD Setup Guide

## Overview

This guide helps you set up the Personal Assistant GTD system for interactive use in Claude Code/Claude Desktop.

## Prerequisites

- Node.js 18+ installed
- Claude Desktop or Claude Code installed
- This repository cloned

## Setup Steps

### 1. Build the MCP Server

The Graph Memory Core MCP server needs to be built before use:

```bash
cd /Volumes/Share\ 1/Projects/personal-assistant-gtd-style/src/graph-memory-core/mcp
npm install
npm run build
```

This creates the server executable at `dist/index.js`.

### 2. Create Data Directory

Create a directory to store your GTD graph data:

```bash
mkdir -p ~/personal-assistant-data/gtd-graph
```

This directory will contain:
- `_system/registry.json` - Graph structure (nodes, connections, properties, ontology)
- `_content/nodes/` - Individual node content files (Task descriptions, State conditions, etc.)

### 3. Configure Claude Code

Add the graph-memory-core MCP server using the Claude Code CLI:

```bash
claude mcp add gtd-graph-memory --scope user \
  -e BASE_PATH=/Users/scottmcguire/personal-assistant-data/gtd-graph \
  -- node "/Volumes/Share 1/Projects/personal-assistant-gtd-style/src/graph-memory-core/mcp/dist/index.js"
```

**Scope explanation:**
- `--scope user` makes the server available across all Claude Code sessions (recommended for GTD)
- Alternatively, use `--scope local` for project-specific setup

### 4. Verify Configuration

Check that the server is configured and connected:

```bash
claude mcp list
```

You should see:
```
gtd-graph-memory: node ... - ✓ Connected
```

### 5. Test the System

In this Claude Code conversation (or start a new one), test the GTD system:

**Test 1: Verify MCP tools are available**

Type `/mcp` to see available MCP servers and their tools. You should see `gtd-graph-memory` with tools like:
- `create_node`
- `query_nodes`
- `create_connection`
- etc.

**Test 2: Create your first task**

```
Create a task: "Test the GTD system"
```

Claude should use the graph-memory-core tools to create a Task node.

**Test 3: Verify persistence**

```
What tasks do I have?
```

Claude should query the graph and find the task you just created.

## Usage Patterns

Once set up, you can interact naturally:

### Capturing Tasks
- "I need to call the dentist"
- "Add a task to review the quarterly report"

### Creating Projects (tasks with dependencies)
- "I'm working on the website redesign. It depends on finishing the wireframes."

### Querying
- "What projects do I have?"
- "What should I work on next?"
- "Show me my Next Actions"

### Updating Status
- "I finished calling the dentist"
- "Mark the wireframes as complete"

### Weekly Review
- "Show me my weekly review"

## Troubleshooting

### Server shows as disconnected
1. Run `claude mcp list` to check status
2. Check the path to `dist/index.js` is correct
3. Verify the server built successfully: `ls src/graph-memory-core/mcp/dist/index.js`
4. Try rebuilding: `cd src/graph-memory-core/mcp && npm run build`
5. Remove and re-add the server:
   ```bash
   claude mcp remove gtd-graph-memory
   # Then add it again with the command from step 3
   ```

### "Tool not found" errors
1. Type `/mcp` in Claude Code to verify tools are listed
2. Check that BASE_PATH directory exists: `ls ~/personal-assistant-data/gtd-graph`
3. Try `claude mcp list --debug` for detailed diagnostics

### Data not persisting
1. Check BASE_PATH is set correctly: `echo $BASE_PATH` won't work (it's set in MCP config), instead check:
   ```bash
   cat ~/.claude.json | grep -A 5 gtd-graph-memory
   ```
2. Verify `_system/registry.json` exists after creating first task:
   ```bash
   ls -la ~/personal-assistant-data/gtd-graph/_system/
   ```
3. Check file permissions on the data directory:
   ```bash
   ls -ld ~/personal-assistant-data/gtd-graph
   ```

## Data Location

All GTD data is stored in: `~/personal-assistant-data/gtd-graph/`

To backup your data:
```bash
tar -czf gtd-backup-$(date +%Y%m%d).tar.gz ~/personal-assistant-data/gtd-graph
```

To view your raw data:
```bash
cat ~/personal-assistant-data/gtd-graph/registry.yaml
ls ~/personal-assistant-data/gtd-graph/nodes/
```

## Next Steps

After setup is complete, proceed to the **Validation Period** (Phase 1, Feature 5 in ROADMAP.md):

Use the system for 3-5 days of real GTD usage to validate:
- Memory reliability (no data loss)
- Conversational naturalness
- Persistence across sessions

See ROADMAP.md for validation criteria and checkpoint decision-making.
