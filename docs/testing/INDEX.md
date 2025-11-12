# GTD Testing Documentation Index

**Last Updated**: 2025-11-09
**Status**: Active

Welcome to the GTD conversational layer testing documentation. This index provides navigation and quick reference for the complete testing infrastructure.

---

## Quick Start

### Run Your First Test

```bash
# Run a single test with live MCP
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --test-name capture_simple \
  --clean-graph-between-tests

# Run all tests with graph cleanup between tests
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --clean-graph-between-tests \
  --log-level INFO
```

### View Test Results

```bash
# Check latest test run
sqlite3 test_results.db "SELECT * FROM test_results ORDER BY timestamp DESC LIMIT 10;"

# View MCP tool calls
cat /var/folders/.../mcp-test-logs/mcp-log-*.jsonl
```

### Common Test Categories

| Category | Tests | Purpose |
|----------|-------|---------|
| **Capture** | 4 tests | Task creation, duplicate detection |
| **Query** | 3 tests | Next actions, projects, searching |
| **Update** | 3 tests | Completing tasks, adding notes, changing properties |
| **Delete** | 2 tests | Task deletion, dependency handling |
| **Project** | 2 tests | Project breakdown, dependency management |
| **Context** | 2 tests | Context creation, availability tracking |
| **Edge** | 4 tests | Ambiguous references, undefined contexts, conflicts |

---

## Documentation Map

### 🧭 Plans
- [plans/judge-mcp-access.md](plans/judge-mcp-access.md) — Judge with direct MCP access
- [plans/api-harness-multi-provider.md](plans/api-harness-multi-provider.md) — API-driven, multi-provider test harness
- [plans/mcp-tool-gateway.md](plans/mcp-tool-gateway.md) — Generic MCP bridge + clients repo plan
- [plans/provider-fast-paths-todo.md](plans/provider-fast-paths-todo.md) — Provider fast paths (OpenAI Agents, xAI remote MCP) TODOs
- [plans/mcp-tool-gateway.md](plans/mcp-tool-gateway.md) — Generic MCP bridge + clients repo plan

### 📘 [infrastructure.md](infrastructure.md)
**Current implementation details** (1,653 lines)

Complete documentation of the existing testing system across 5 layers:
- **Layer 1**: Test execution (runners, CLI, modes)
- **Layer 2**: Test inputs (test cases, fixtures, configuration)
- **Layer 3**: Test setup (MCP server, graph initialization, environment)
- **Layer 4**: Test flow (execution loop, roles, conversational testing)
- **Layer 5**: Test outputs (SQLite results, logs, interrogation data)

**When to read**: Understanding how tests currently work, debugging test failures, configuring test runs

### 📗 [improvements.md](improvements.md)
**Planned enhancements and issues** (825 lines)

Catalog of 28+ proposed improvements organized by layer:
- Test execution improvements (delete legacy runner, flexible lifecycle)
- Test input improvements (schema validation, shared fixtures)
- Setup improvements (automatic path handling, faster cleanup)
- Flow improvements (parallel execution, failure recovery)
- Output improvements (HTML reports, performance metrics)
- Cross-cutting concerns (comprehensive integration, CI/CD)

**When to read**: Planning future work, understanding known issues, proposing changes

### 📕 [prompts.md](prompts.md)
**AI model configurations** (621 lines)

Complete documentation of all prompts used in testing:
- **Assistant prompts**: Base system prompt + test overlays
- **User-proxy prompts**: Conversational user simulation
- **Judge prompts**: Three-dimensional evaluation criteria
- **Interrogator prompts**: Post-test reasoning questions

**When to read**: Modifying test behavior, understanding AI decision-making, debugging unexpected responses

---

## Architecture Overview

### Five-Layer Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Test Execution                                      │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ test_conversational_layer_new.py (modular runner)     │   │
│ │ - CLI argument parsing                                │   │
│ │ - Test orchestration                                  │   │
│ │ - Multi-run support (--runs N)                        │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Test Inputs                                         │
│ ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│ │ Test Cases       │  │ Fixtures         │  │ Config     │ │
│ │ (refactored.json)│  │ (tasks.json)     │  │ (mcp-conf) │ │
│ └──────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Test Setup                                          │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ MCP Server Launch                                     │   │
│ │ - gtd-graph-memory MCP server                         │   │
│ │ - Environment: MCP_CALL_LOG=/tmp/mcp-log-*.jsonl     │   │
│ │ - Graph cleanup (--clean-graph-between-tests)        │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Test Flow                                           │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│ │ User-    │  │ Assistant│  │ Judge    │  │ Interrogator│  │
│ │ Proxy    │→ │ (SUT)    │→ │ (Eval)   │→ │ (Questions) │  │
│ │ (Haiku)  │  │ (Sonnet) │  │ (Sonnet) │  │ (Sonnet)    │  │
│ └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Test Outputs                                        │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│ │ SQLite DB    │  │ MCP Logs     │  │ Interrogation    │   │
│ │ (4 tables)   │  │ (JSON Lines) │  │ (reasoning.json) │   │
│ └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Test Execution Mode

Tests always run in **Live MCP mode** (`--mode real`):

| Mode | MCP Server | Purpose |
|------|------------|---------|
| `real` | Yes (live) | Integration testing with real MCP operations |

**Note**: Simulation mode has been removed to ensure tests validate actual MCP behavior.

### Four AI Roles

```
User-Proxy (Haiku)
    │ "Can I see my next actions?"
    │
    ↓
Assistant (Sonnet + MCP)
    │ Uses search_content, query_nodes
    │ "Here are your 3 next actions..."
    │
    ↓
Judge (Sonnet)
    │ Evaluates: effective? safe? clear?
    │ Returns: pass/fail + reasoning
    │
    ↓
Interrogator (Sonnet)
    │ "Why did you choose search_content?"
    │ "What made you confident?"
    │
    ↓
Reasoning captured in interrogation logs
```

---

## Test Categories Reference

### Capture Tests
Test task creation and duplicate detection.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `capture_simple` | "Schedule dentist appointment" | Creates single Task node |
| `capture_multiple` | "Call mom, email boss, buy groceries" | Creates 3 separate Task nodes |
| `capture_with_context` | "Email the report when I'm atOffice" | Creates Task + Context + DependsOn connection |
| `capture_duplicate_detection` | "Schedule dentist" (already exists) | Detects duplicate, asks to clarify |

### Query Tests
Test retrieval and search operations.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `query_next_actions` | "What should I do next?" | Returns Tasks with no outgoing dependencies |
| `query_projects` | "Show my projects" | Returns Tasks with outgoing DependsOn connections |
| `query_search` | "Find all tasks about the report" | Uses search_content, returns matching Tasks |

### Update Tests
Test task modification operations.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `update_complete_simple` | "Mark dentist appointment as done" | Sets isComplete=true on existing Task |
| `update_add_note` | "Add note to report task: needs review" | Updates Task content or properties |
| `update_change_context` | "Move report to atHome instead of atOffice" | Updates DependsOn connections |

### Delete Tests
Test task removal operations.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `delete_simple` | "Delete the dentist task" | Removes Task node + connections |
| `delete_with_dependencies` | "Delete project with subtasks" | Handles cascading deletion safely |

### Project Tests
Test project creation and breakdown.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `project_breakdown` | "Website redesign project: design, code, deploy" | Creates parent Task + 3 child Tasks + DependsOn |
| `project_query` | "What's next for website redesign?" | Returns next available subtask |

### Context Tests
Test context creation and availability.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `context_create` | "Create atOffice context" | Creates Context node |
| `context_available` | "atOffice is available now" | Sets isTrue=true |

### Edge Cases
Test ambiguous or error-prone scenarios.

| Test Name | User Input | Expected Behavior |
|-----------|------------|-------------------|
| `edge_ambiguous_reference` | "Update the task" (multiple exist) | Asks user to clarify which task |
| `edge_undefined_context` | "Do this @gym" (@gym doesn't exist) | Creates Context or asks to confirm |
| `edge_conflicting_update` | "Mark dentist as done and not done" | Handles contradiction gracefully |
| `edge_empty_query` | "Show me" (incomplete request) | Asks for clarification |

---

## Common Tasks

### Running Tests

#### Run single test
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --test-name capture_simple \
  --clean-graph-between-tests
```

#### Run test category
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --category Capture \
  --clean-graph-between-tests
```

#### Run full suite (5 runs each)
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --runs 5 \
  --clean-graph-between-tests \
  --results-db test_results_5runs.db
```

#### Run with interrogation
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --interrogate-all \
  --interrogation-log interrogation_results.json
```

### Analyzing Results

#### Query SQLite results
```bash
# Overall pass rate
sqlite3 test_results.db "
  SELECT
    COUNT(*) as total,
    SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) as passed,
    ROUND(100.0 * SUM(CASE WHEN passed=1 THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
  FROM test_results;
"

# Results by test
sqlite3 test_results.db "
  SELECT test_name, COUNT(*) as runs, SUM(passed) as passed
  FROM test_results
  GROUP BY test_name
  ORDER BY test_name;
"

# View specific test failure
sqlite3 test_results.db "
  SELECT test_name, error_message, assistant_transcript
  FROM test_results
  WHERE passed=0 AND test_name='capture_duplicate_detection'
  LIMIT 1;
"
```

#### View MCP logs
```bash
# Find latest MCP log
ls -lt /var/folders/*/T/mcp-test-logs/ | head -5

# View specific log
cat /var/folders/.../mcp-test-logs/mcp-log-abc123.jsonl | jq '.'

# Count tool calls by type
cat /var/folders/.../mcp-test-logs/mcp-log-abc123.jsonl | jq -r '.tool' | sort | uniq -c
```

#### View interrogation results
```bash
# Pretty-print interrogation JSON
cat interrogation_results.json | jq '.'

# Extract specific reasoning
cat interrogation_results.json | jq '.[] | select(.test_name=="capture_simple") | .reasoning'
```

### Debugging Test Failures

#### 1. Check assistant transcript
```bash
sqlite3 test_results.db "
  SELECT assistant_transcript
  FROM test_results
  WHERE test_name='failing_test'
  LIMIT 1;
" | less
```

#### 2. Check MCP tool calls
```bash
# Verify tools were called
cat /var/folders/.../mcp-test-logs/mcp-log-*.jsonl | grep search_content
```

#### 3. Run interrogation
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --test-name failing_test \
  --interrogate-failures \
  --interrogation-log debug_interrogation.json
```

#### 4. Check graph state
```bash
# View graph contents after test
sqlite3 /path/to/gtd-memory/_system/registry.json
```

### Adding New Tests

#### 1. Add test case to JSON
Edit `tests/test_cases_refactored.json`:
```json
{
  "test_name": "my_new_test",
  "category": "Capture",
  "user_inputs": [
    "Schedule team meeting"
  ],
  "assertions": [
    {
      "type": "node_exists",
      "node_type": "Task",
      "content_match": "team meeting"
    }
  ]
}
```

#### 2. Run the new test
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --test-name my_new_test \
  --clean-graph-between-tests
```

#### 3. Verify with interrogation
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --test-name my_new_test \
  --interrogate-all \
  --interrogation-log my_test_reasoning.json
```

### MCP Server Configuration

#### Launch MCP server manually
```bash
BASE_PATH=/path/to/gtd-data \
MCP_CALL_LOG=/tmp/mcp-manual-test.jsonl \
node /path/to/graph-memory-core/mcp/dist/index.js
```

#### Configure for tests
The test runner handles this automatically when using `--mode real`, but you can override:
```bash
# Use custom MCP config
python tests/test_conversational_layer_new.py \
  --mode real \
  --test-cases refactored \
  --mcp-config my_custom_mcp_config.json
```

### Graph Cleanup

#### Manual cleanup between tests
```bash
# Delete all test data
rm -rf /path/to/gtd-test-data/*

# Or use the --clean-graph-between-tests flag
python tests/test_conversational_layer_new.py \
  --mode real \
  --clean-graph-between-tests
```

#### Verify graph is clean
```bash
# Check registry
cat /path/to/gtd-test-data/_system/registry.json

# Should show minimal/empty state
```

---

## File Locations

### Test Infrastructure
- **Test runner**: `tests/test_conversational_layer_new.py`
- **Test modules**: `tests/conversational_layer/`
- **Test cases**: `tests/test_cases_refactored.json`
- **Fixtures**: `tests/fixtures/`
- **MCP config**: `tests/mcp-config.json`

### System Under Test
- **MCP server**: `src/graph-memory-core/mcp/dist/index.js`
- **Base system prompt**: `src/conversational-layer/system-prompt-full.md`
- **Test overlays**: `tests/fixtures/system-prompt-*.md`

### Outputs
- **Test results**: `test_results.db` (or custom via `--results-db`)
- **MCP logs**: `/var/folders/.../mcp-test-logs/mcp-log-*.jsonl`
- **Interrogation**: Custom path via `--interrogation-log`
- **Transcripts**: Embedded in SQLite `test_results` table

---

## Additional Resources

### Related Documentation
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)**: General contribution guidelines
- **[System Prompt](../../src/conversational-layer/system-prompt-full.md)**: Production GTD assistant behavior
- **[MCP Server README](../../src/graph-memory-core/README.md)**: Graph memory implementation

### External References
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **GTD Methodology**: Getting Things Done by David Allen
- **Claude CLI**: https://docs.claude.com/

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-09 | Initial comprehensive documentation |

---

## Navigation

- 📘 **[Current Implementation →](infrastructure.md)**
- 📗 **[Planned Improvements →](improvements.md)**
- 📕 **[AI Prompts & Configuration →](prompts.md)**
