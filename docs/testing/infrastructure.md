# Testing Infrastructure Documentation

> **Part of**: [GTD Testing Documentation](INDEX.md) | **See also**: [Improvements](improvements.md) · [Prompts](prompts.md)

**Status**: In Progress (Building incrementally)
**Last Updated**: 2025-11-09

## Overview

This document describes the current state of the testing infrastructure for the GTD conversational layer. The testing system validates that the Claude-based assistant correctly handles GTD operations (capture, query, update, delete) via MCP (Model Context Protocol).

**Key findings:**
- We have TWO parallel testing systems (legacy monolithic + new modular)
- MCP server logging captures ground-truth tool call data
- Tests can persist results to SQLite databases or output to stdout
- Multiple isolation strategies available (graph cleanup, independent processes, retry logic)

---

## Layer 1: Test Execution

### What We Execute

**Two primary test runners:**

1. **Legacy Runner** (`tests/test_conversational_layer.py`)
   - **Size**: 1,142 lines
   - **Architecture**: Monolithic single file
   - **Location**: `/Volumes/Share 1/Projects/personal-assistant-gtd-style/tests/test_conversational_layer.py`

2. **New Modular Runner** (`tests/test_conversational_layer_new.py`)
   - **Size**: 137 lines (+ ~2,900 lines across modules)
   - **Architecture**: Modular with separate components
   - **Location**: `/Volumes/Share 1/Projects/personal-assistant-gtd-style/tests/test_conversational_layer_new.py`
   - **Module directory**: `tests/conversational_layer/`

### Command-Line Interface

#### Legacy Runner

```bash
python tests/test_conversational_layer.py [options]
```

**Key arguments:**

| Argument | Values | Default | Purpose |
|----------|--------|---------|---------|
| `--mode` | `auto`, `sim`, `real` | `auto` | Test mode (sim=no MCP, real=live MCP) |
| `--suite` | `all`, `assistant`, `judge` | - | Suite selection |
| `--test-cases` | FILE | - | Test cases file (default: test_cases_refactored.json) |
| `--test-name` | NAME | - | Run single specific test |
| `--clean-graph-between-tests` | flag | off | Clean graph after each test |
| `--interrogate-failures` | flag | off | Ask follow-up questions on failures |
| `--interrogate-passes` | flag | off | Survey assistant on successes |
| `--interrogate-all` | flag | off | Both interrogation modes |
| `--interrogation-log` | FILE | - | Save interrogation responses to JSON |
| `--assistant-timeout` | SECONDS | 300 | Timeout for assistant responses |
| `--judge-timeout` | SECONDS | 300 | Timeout for judge evaluation |

**Example commands:**

```bash
# Run all tests with MCP, clean graph between tests
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests

# Run single test with interrogation
python tests/test_conversational_layer.py \
  --mode real \
  --test-name capture_simple_task \
  --interrogate-all
```

#### New Modular Runner

```bash
python tests/test_conversational_layer_new.py [options]
```

**All legacy arguments PLUS:**

| Argument | Values | Default | Purpose |
|----------|--------|---------|---------|
| `--runs` | N | 1 | Run each test N times |
| `--inter-run-delay` | SECONDS | 10 | Delay between runs |
| `--inter-test-delay` | SECONDS | 0 | Delay between tests |
| `--max-retries` | N | 3 | Max retry attempts on failures |
| `--log-level` | `DEBUG`, `INFO`, `WARN`, `ERROR` | - | Logging verbosity |
| `--results-db` | FILE | - | SQLite database for results |
| `--query` | `flaky`, `summary`, `category` | - | Query existing database |
| `--run-id` | ID | - | Specific run ID for queries |
| `--export-json` | FILE | - | Export run to JSON |
| `--list` | flag | off | List tests without running |

**Example commands:**

```bash
# Run all tests 5 times with database output
python tests/test_conversational_layer_new.py \
  --mode real \
  --runs 5 \
  --interrogate-all \
  --clean-graph-between-tests \
  --results-db tests/test_results_5runs.db \
  --log-level INFO

# Query flaky tests from a completed run
python tests/test_conversational_layer_new.py \
  --query flaky \
  --results-db tests/test_results_5runs.db

# Export run to JSON
python tests/test_conversational_layer_new.py \
  --query export \
  --run-id 42 \
  --export-json results_run42.json \
  --results-db tests/test_results_5runs.db
```

### Helper Scripts

#### Independent Test Runner

**Purpose**: Run each test in complete isolation (separate process per test)

**Location**: `tests/run_independent_tests.py` (123 lines)

**Configuration** (hardcoded in script):
```python
NUM_RUNS = 5                      # Run each test 5 times
OUTPUT_DIR = Path(__file__).parent.parent
BASE_CMD = [
    "python", "test_conversational_layer.py",
    "--suite", "assistant",
    "--mode", "real",
    "--clean-graph-between-tests",
    "--interrogate-all"
]
```

**Output files per test×run:**
- `independent_{test_name}_run{N}.json` - Interrogation data
- `independent_{test_name}_run{N}.stdout` - Standard output
- `independent_{test_name}_run{N}.stderr` - Error output
- `independent_{test_name}_run{N}.status` - Status metadata (JSON)

#### Serial Runner with Retries

**Purpose**: Run tests sequentially with exponential backoff retry logic

**Location**: `tests/run_serial_with_retries.py` (224 lines)

**Configuration**:
```python
NUM_RUNS = 5                      # Runs per test
MAX_RETRIES = 3                   # Max retry attempts
INITIAL_BACKOFF = 30              # Initial backoff (seconds)
INTER_TEST_DELAY = 10             # Delay between tests (seconds)
OUTPUT_DIR = Path(__file__).parent.parent / "test-results"
```

**Retry logic:**
- **Exponential backoff**: `backoff = INITIAL_BACKOFF * (2 ** retry_count)`
- **Retry on**: CLI errors, timeouts, crashes
- **Skip retry on**: Test not found, judge FAIL (behavioral issue, not crash)
- **Resume support**: Skips already-completed tests based on status files

### Current Test Runs (Background Processes)

**Active background test runs** (as of this documentation session):

Based on running processes, we have ~18 test runs executing simultaneously:
- Multiple 5-run test suites
- Mix of legacy and new runners
- Some targeting specific categories (Capture, Delete)
- Some targeting specific tests (edge cases)
- All using `--mode real` (live MCP)
- Most using `--interrogate-all`
- Most using `--clean-graph-between-tests`

Example active runs:
```bash
# Full suite, 5 runs, database output
python tests/test_conversational_layer_new.py \
  --mode real --runs 5 \
  --interrogate-all --clean-graph-between-tests \
  --results-db tests/test_results_5runs_fixed.db \
  --log-level INFO

# Capture category only
python tests/test_conversational_layer_new.py \
  --mode real \
  --category Capture --log-level INFO \
  --clean-graph-between-tests
```

---

## Layer 2: Inputs

### 2.1 Test Case Files

#### Test Cases: `tests/test_cases_refactored.json`

**Location**: `/Volumes/Share 1/Projects/personal-assistant-gtd-style/tests/test_cases_refactored.json`
**Size**: 470 lines (current standard)
**Count**: 30+ test cases

**Structure**:
```json
[
  {
    "name": "capture_simple_task",
    "category": "Capture",
    "prompt": "The user says: \"I need to call the dentist...\" Persist this task...",
    "expected_behavior": "Create a Task node with isComplete=false...",
    "success_criteria": [
      "persist a new task",
      "mark it incomplete",
      "treat as next action",
      "confirm capture to the user"
    ],
    "must_not": [
      "pre-emptively ask for permission before capture",
      "defer task creation pending permission"
    ]
  }
]
```

**Field descriptions**:

| Field | Type | Purpose |
|-------|------|---------|
| `name` | string | Unique test identifier (snake_case) |
| `category` | string | Test category for grouping |
| `prompt` | string | User utterance presented to assistant |
| `expected_behavior` | string | What the assistant should do |
| `success_criteria` | string[] | Checklist of expected outcomes |
| `must_not` | string[] | Anti-patterns to avoid |
| `expected_pass` | boolean | Whether test should pass (optional, defaults to true) |
| `graph_setup` | object | Pre-populate graph with fixtures (optional) |

**Test Categories & Counts**:

| Category | Count | Purpose |
|----------|-------|---------|
| **Capture** | 9 | Task capture, projects, dependencies, contexts |
| **Query** | 6 | Next actions, projects, waiting-for, context filtering |
| **Update** | 5 | Mark complete, update details, context availability |
| **Delete** | 2 | Warning protocols, cascade confirmed |
| **Edge** | 6 | Invalid requests, empty results, ambiguity handling |
| **NegativeControl** | 2 | Judge validation (expected_pass: false) |

**Example test categories**:
- `capture_simple_task`: Basic task capture
- `capture_task_with_context`: Task requiring @office context
- `query_next_actions`: What should I work on?
- `update_mark_complete`: Mark task as done
- `delete_with_dependency_warning`: Warn before cascade delete
- `edge_ambiguous_reference`: Handle "mark the proposal done" (which one?)

### 2.2 MCP Configuration Files

#### Base MCP Config: `tests/mcp-config.json`

**Location**: `/Volumes/Share 1/Projects/personal-assistant-gtd-style/tests/mcp-config.json`

**Structure**:
```json
{
  "mcpServers": {
    "gtd-graph-memory": {
      "command": "node",
      "args": ["/Users/scottmcguire/.../mcp/dist/index.js"],
      "env": {
        "BASE_PATH": "/Users/scottmcguire/.../.data/gtd-memory"
      }
    }
  }
}
```

**Purpose**: Configures connection to MCP server for testing

**Dynamic modification**: Test framework creates temporary MCP configs by:
1. Reading base config
2. Adding `MCP_CALL_LOG` to env vars (points to unique log file per test)
3. Writing to temp file: `/tmp/mcp-config-{uuid}.json`
4. Passing temp config to Claude via `--mcp-config`
5. Cleanup after test completes

**Code location**: `test_conversational_layer.py:366-392` (`create_mcp_config_with_logging()`)

### 2.3 System Prompts and Test Overlays

#### Base System Prompt (Production)

**Location**: `/Volumes/Share 1/Projects/personal-assistant-gtd-style/src/conversational-layer/system-prompt-full.md`

**Usage**: Loaded via `--system-prompt` flag by both test runners

**Purpose**: Main GTD assistant instructions (semantics, safety, behavior)

#### Test Environment Overlays

Test overlays are **appended** to the base system prompt to modify behavior for testing.

##### 1. General Test Overlay

**Location**: `tests/fixtures/system-prompt-test-overlay.md`
**Status**: **Intentionally empty** (consolidated into base prompt)
**Historical purpose**: Test-specific guidance (no longer needed)

##### 2. Live MCP Overlay (`--mode real`)

**Location**: `tests/fixtures/system-prompt-live-mcp-overlay.md`
**When used**: `--mode real` (MCP server available)

**Key guidance**:
```markdown
Environment
- Connected to non-production, test-only MCP server
- Full permissions for all MCP operations
- Follow normal safety (confirm destructive actions)

Execution
- Perform real operations using MCP tools
- Include concise, accurate transcript code blocks
- Never claim a change without executing tool
- Use returned IDs; do not invent IDs

Behavioral scope
- Rely on base prompt for GTD semantics
- For destructive actions, proceed after confirmation
- No meta commentary about tooling/tests

Communication
- Keep transcripts minimal and accurate
- Clear user-first confirmations of outcomes
```

**Effect**: Assistant executes actual MCP operations and shows transcripts

##### 3. Simulation Overlay (`--mode sim`)

**Location**: `tests/fixtures/system-prompt-no-mcp-overlay.md`
**When used**: `--mode sim` (no MCP server)

**Key guidance**:
```markdown
Environment
- No MCP server available
- Describe operations you would perform

Execution
- Describe the plan and operations
- Provide representative result set
- Label as simulated: "Simulated: Captured task..."
- Use descriptive placeholders, not concrete IDs

Example format:
  Simulated: Captured task "Call dentist" (task_abc123)
  Simulated: Created @office context (ctx_def456)
```

**Effect**: Assistant simulates operations without actual MCP calls

#### Mode Selection Logic

**`--mode auto`** (default):
1. Check if MCP config exists and is valid
2. If yes → use `real` mode
3. If no → use `sim` mode

**`--mode real`**: Force Live MCP mode (fails if MCP unavailable)

**`--mode sim`**: Force simulation mode (no MCP even if available)

## Layer 3: Setup and Initialization

This layer describes what happens before each test runs: MCP logging configuration, graph cleanup, and fixture population.

---

### 3.1 MCP Server Logging Setup

**Purpose**: Capture ground-truth data of all MCP tool calls made during tests

**Implementation**: The MCP server (`src/graph-memory-core/mcp/src/server.ts`) checks for the `MCP_CALL_LOG` environment variable on startup. When set, it creates a JSON Lines log file capturing every tool invocation.

#### Server-Side Logging Code

**Location**: `src/graph-memory-core/mcp/src/server.ts:172-208`

**Key components**:

```typescript
export class GraphMemoryMcpServer {
  private logFile: string | null = null;
  private logStream: fs.WriteStream | null = null;

  constructor(private readonly graph: MemoryGraph) {
    // Initialize logging if MCP_CALL_LOG environment variable is set
    const logPath = process.env.MCP_CALL_LOG;
    if (logPath) {
      this.logFile = logPath;
      const dir = path.dirname(logPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      this.logStream = fs.createWriteStream(logPath, { flags: 'a' });
      this.logToolCall('SERVER_START', {});
    }
  }

  private logToolCall(toolName: string, input: any, result?: any, error?: any): void {
    if (!this.logStream) return;
    const logEntry = {
      timestamp: new Date().toISOString(),
      tool: toolName,
      input: input,
      ...(result !== undefined && { result }),
      ...(error !== undefined && { error: String(error) })
    };
    this.logStream.write(JSON.stringify(logEntry) + '\n');
  }
}
```

**Logged events**: All 19 MCP tools plus `SERVER_START` initialization marker

#### Test Framework Integration

**Location**: `tests/test_conversational_layer.py:366-392`

**Function**: `create_mcp_config_with_logging(base_mcp_path, log_file_path)`

**Process**:

1. Read base MCP config from `tests/mcp-config.json`
2. Clone config data
3. Add `MCP_CALL_LOG` environment variable pointing to unique log file:
   ```python
   config_data[servers_key]["gtd-graph-memory"]["env"]["MCP_CALL_LOG"] = str(log_file_path)
   ```
4. Write temporary config to `/tmp/mcp-config-{uuid}.json`
5. Pass temp config to Claude CLI via `--mcp-config` flag
6. Return paths: `(temp_config, log_file_path)`

#### MCP Log File Naming

**Location**: `/tmp/mcp-test-logs/mcp-log-{uuid}.jsonl`

**Format**: JSON Lines (one JSON object per line)

**Example entries**:
```json
{"timestamp":"2025-11-09T00:01:47.934Z","tool":"SERVER_START","input":{}}
{"timestamp":"2025-11-09T00:01:51.687Z","tool":"search_content","input":{"query":"website redesign","node_type":"Task"},"result":{"node_ids":["mem_mhqy7v2l_1lunmdl"]}}
{"timestamp":"2025-11-09T00:02:01.349Z","tool":"update_node","input":{"node_id":"mem_mhqy7v2l_1lunmdl","properties":{"isComplete":true}}}
```

**Cleanup**: Temporary MCP config and log files are removed after test completes (or on process exit)

---

### 3.2 Graph State Cleanup

**Purpose**: Ensure test isolation by clearing all graph data between tests

**When executed**: When `--clean-graph-between-tests` flag is set (after each test completes)

**Location**: `tests/test_conversational_layer.py:752-818`

**Function**: `clean_graph_state(mcp, timeout_s=60)`

**Implementation strategy**: Uses Claude CLI with specialized cleanup system prompt

**Process**:

1. **Skip in simulation mode**: If no MCP config, return immediately (no cleanup needed)
2. **Generate cleanup prompt**:
   ```
   Delete all nodes in the graph to prepare for the next test.

   Steps:
   1. Query all nodes (no filters)
   2. Delete each node (connections will cascade automatically)
   3. Confirm the graph is empty
   ```
3. **Use specialized system prompt**:
   ```
   You are a graph cleanup utility. Your job is to delete all nodes in the graph.
   Use query_nodes with no filters to find all nodes, then delete each one.
   Be concise - just do the cleanup and confirm when done.
   ```
4. **Execute via Claude CLI**:
   ```python
   args = [CLAUDE_CMD, "--mcp-config", str(mcp),
           "--dangerously-skip-permissions", "--print",
           "--output-format", "json",
           "--system-prompt", cleanup_system,
           cleanup_prompt]
   subprocess.run(args, timeout=timeout_s)
   ```
5. **Verify success**: Check subprocess return code

**Result**: Clean graph with zero nodes, ready for next test

---

### 3.3 Fixture Setup (Pre-populated Tests)

**Purpose**: Some tests require pre-existing graph data to test update/delete/query operations

**Trigger**: Test case contains `graph_setup` field in JSON definition

**Location**: `tests/test_conversational_layer.py:822-918`

**Function**: `setup_graph_from_fixture(fixture, mcp, timeout_s=60)`

**When executed**: Before test prompt is sent (if `graph_setup` is defined and MCP is available)

#### Fixture Structure

Test cases can include a `graph_setup` field with three optional arrays:

```json
{
  "name": "update_mark_complete",
  "graph_setup": {
    "tasks": [
      {
        "content": "File quarterly taxes",
        "isComplete": false,
        "id": "tax_task",
        "depends_on": []
      }
    ],
    "contexts": [
      {
        "content": "@office",
        "isAvailable": false
      }
    ],
    "states": [
      {
        "content": "Weather is good for painting",
        "isTrue": false
      }
    ]
  }
}
```

**Field descriptions**:

| Array | Purpose | Fields |
|-------|---------|--------|
| `tasks` | Pre-create tasks | `content` (string), `isComplete` (bool), `id` (optional ref), `depends_on` (string[]) |
| `contexts` | Pre-create contexts | `content` (string), `isAvailable` (bool) |
| `states` | Pre-create states | `content` (string), `isTrue` (bool) |

#### Fixture Setup Process

1. **Convert to natural language**: Transform JSON fixture into setup instructions:
   ```
   Set up the following test data:

   Create an incomplete task: 'File quarterly taxes'
     (Store this task ID as 'tax_task' for later reference)
   Create context @office (currently unavailable)
   ```

2. **Use specialized setup system prompt**:
   ```
   You are a test fixture setup utility for a GTD system.
   Your job is to create nodes and connections as requested.

   Execute all setup commands precisely, then confirm completion.
   Be concise - just create what's needed and confirm when done.
   ```

3. **Execute via Claude CLI** (similar to cleanup process)

4. **Verify success**: Check subprocess return code

**Result**: Graph populated with fixture data, ready for test to execute

---

### 3.4 Test Lifecycle Summary

For each test, the initialization sequence is:

```
1. IF --clean-graph-between-tests AND previous test completed
   → Execute graph cleanup (3.2)

2. Create unique MCP log file path
   → /tmp/mcp-test-logs/mcp-log-{uuid}.jsonl

3. Create temporary MCP config with logging
   → create_mcp_config_with_logging() (3.1)

4. IF test has graph_setup field AND MCP is available
   → Execute fixture setup (3.3)

5. Test is now ready to execute
   → Proceed to Layer 4 (Execution Flow)
```

**Code locations**:
- Legacy runner: `tests/test_conversational_layer.py:998-1010` (main test loop)
- New modular runner: `tests/conversational_layer/runner.py:198-210` (test execution)

## Layer 4: Execution Flow

This layer describes the test execution lifecycle: assistant invocation, judge evaluation, and optional interrogation.

---

### 4.1 Test Loop Structure

For each test case, the framework executes:

```
1. Setup (Layer 3)
   └→ Graph cleanup (if configured)
   └→ MCP logging setup
   └→ Fixture population (if needed)

2. Assistant Execution (4.2)
   └→ Run Claude CLI with test prompt
   └→ Capture response and session ID
   └→ Read MCP log entries

3. Judge Evaluation (4.3)
   └→ Run judge with assistant response
   └→ Determine PASS/FAIL
   └→ Compare against expected outcome

4. Interrogation (4.4) [Optional]
   └→ Resume session with follow-up questions
   └→ Capture Q&A for analysis

5. Cleanup
   └→ Delete temporary MCP config
   └→ Graph cleanup (if configured)
```

**Code location**: `tests/test_conversational_layer.py:984-1108` (main test loop)

---

### 4.2 Multi-Turn Conversational Tests (User-Proxy)

**Module**: `tests/conversational_layer/user_proxy.py` (855 lines)

**Purpose**: Enable testing of scenarios where the assistant needs to ask clarifying questions and engage in back-and-forth dialogue with the user.

**When used**: Tests marked with `"conversational": {"enabled": true}` in test case JSON

#### Why User-Proxy is Needed

Some GTD scenarios require conversation:
- **Duplicate detection**: "Should I create a new task or update the existing one?"
- **Ambiguous references**: "Which proposal task do you mean - the vendor one or the board one?"
- **Missing information**: "What priority should this have?"
- **Confirmation of destructive actions**: "This will delete 3 dependent tasks. Proceed?"

The user-proxy simulates realistic user responses to these questions, enabling tests of the full interaction flow.

#### Two Execution Modes

**1. Scripted Mode** (`UserProxy` class)
- Pre-defined list of user responses
- Deterministic, repeatable
- Deprecated in favor of LLM mode

**2. LLM Mode** (`LLMUserProxy` class) - **Default**
- Uses Claude Haiku 4.5 to generate natural user responses
- Context-aware: understands test goals and conversation history
- Responds naturally to whatever the assistant asks
- Recognizes conversation completion

#### Test Case Configuration

Tests opt into conversational mode with a `conversational` field:

```json
{
  "name": "capture_duplicate_detection",
  "category": "Capture",
  "prompt": "Add a task to finalize the vendor contract.",
  "graph_setup": {
    "tasks": [
      {"content": "Review vendor contract", "isComplete": false}
    ]
  },
  "conversational": {
    "enabled": true,
    "max_turns": 3,
    "use_llm_user": true,
    "user_proxy_model": "claude-haiku-4-5-20251001",
    "llm_user_temperature": 0.7,
    "goal_summary": "Resolve duplicate task ambiguity",
    "success_criteria": [
      "Assistant searches for existing tasks",
      "Assistant asks about the duplicate",
      "User clarifies intent",
      "Assistant takes appropriate action"
    ],
    "validate_mcp_before_ask": true,
    "require_search_first": true
  }
}
```

**Configuration fields**:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `enabled` | bool | false | Enable conversational mode |
| `max_turns` | int | 3 | Maximum conversation turns |
| `use_llm_user` | bool | true | Use LLM to generate responses |
| `user_proxy_model` | string | "claude-haiku-4-5-20251001" | Model for user-proxy |
| `llm_user_temperature` | float | 0.7 | Creativity level for user responses |
| `goal_summary` | string | "" | Brief description of user's goal |
| `success_criteria` | string[] | [] | What should happen in conversation |
| `validate_mcp_before_ask` | bool | true | Require MCP calls before asking |
| `require_search_first` | bool | true | Require search before clarification |
| `user_responses` | string[] | [] | DEPRECATED: Scripted responses |

#### LLM User-Proxy System Prompt

The user-proxy LLM receives a sophisticated system prompt that:

**1. Establishes Role**:
```
You are roleplaying a **real user** who needs help from a GTD assistant.
Your goal: Work with the assistant to accomplish what you asked for.
```

**2. Provides Context**:
- Test category and scenario
- Original user request
- What the user wants to accomplish
- Success criteria
- Full conversation history (all previous turns)

**3. Sets Behavioral Guidelines**:
- Be natural and realistic
- Stay focused on the goal
- Recognize when done ("That looks good, thanks!")
- Avoid introducing new requirements
- Don't contradict previous statements
- Provide context when asked (priority, deadlines, etc.)
- Be helpful, not obstructive

**4. Example Responses** (good vs bad):

**Good**:
- "Yes, I need those three sub-tasks done in order."
- "The finalize task is different from the review task."
- "That works! Thanks."

**Avoid**:
- "Actually, now I also want X, Y, and Z..." (scope creep)
- "Can you also..." (piling on tasks)

**Key insight**: The user-proxy acts as a realistic, goal-oriented user, not a difficult test adversary.

#### Execution Flow

**For conversational tests**, the execution differs from standard single-turn tests:

```
1. Setup (Layer 3) - same as standard tests
   └→ Graph cleanup, MCP logging, fixtures

2. Turn 1: Initial prompt
   └→ Execute Claude CLI with test prompt
   └→ Capture response, session_id, check for MCP calls
   └→ Store ConversationTurn

3. Turns 2-N: LLM user responses (up to max_turns)
   For each turn:
   └→ Call user-proxy LLM with assistant's previous response
   └→ User-proxy generates natural response
   └→ Resume session (--resume session_id) with user response
   └→ Capture assistant's reply
   └→ Check for completion signals ("thanks", "perfect", etc.)
   └→ Store ConversationTurn

4. Build full transcript
   └→ Combine all turns with full JSON output (MCP calls)
   └→ Format: [Turn N - User] ... [Turn N - Assistant] ...

5. Judge evaluation (4.3)
   └→ Judge receives FULL TRANSCRIPT (all turns, all MCP calls)
   └→ Evaluates entire conversation effectiveness

6. Interrogation (4.4) [Optional]
   └→ Can interrogate final session_id
```

**Code location**: `tests/conversational_layer/user_proxy.py:656-799` (`LLMUserProxy.run_conversation()`)

#### Validation Features

**MCP Call Validation**:
- Checks if assistant made MCP calls before asking questions
- Distinguishes search calls (`search_content`, `query_nodes`) from other operations
- Logs validation results but **doesn't fail tests** - judge evaluates effectiveness

**Example validation logic**:
```python
def _has_mcp_calls(self, payload) -> bool:
    # Look for tool_use blocks with mcp__ prefix
    for block in content:
        if block.get("type") == "tool_use":
            if block.get("name", "").startswith("mcp__"):
                return True
    return False

def _has_search_calls(self, payload) -> bool:
    search_tools = [
        "mcp__gtd-graph-memory__search_content",
        "mcp__gtd-graph-memory__query_nodes",
        "mcp__gtd-graph-memory__get_connected_nodes"
    ]
    # Check if any search tools were called
```

**Note**: Validation is logged for debugging, but the judge makes the final determination using the full transcript.

#### Early Termination

Conversation ends early if user-proxy response contains satisfaction signals:
- "thanks"
- "perfect"
- "looks good"
- "that works"
- "appreciate it"
- "all set"

This prevents unnecessary turns when the goal is achieved.

#### Output Format

**ConversationResult** structure:
```python
{
    "success": True,
    "turns": [
        {
            "turn_number": 1,
            "user_message": "Add a task to finalize the vendor contract.",
            "assistant_response": "I found an existing task 'Review vendor contract'. Should I...",
            "full_output": "{...JSON with MCP calls...}",
            "session_id": "session-uuid",
            "mcp_calls_made": True,
            "duration": 2.3
        },
        {
            "turn_number": 2,
            "user_message": "The finalize task is different - create it as new.",
            "assistant_response": "Got it. I've created a new task 'Finalize vendor contract'...",
            "full_output": "{...JSON with MCP calls...}",
            "session_id": "session-uuid",
            "mcp_calls_made": True,
            "duration": 1.8
        }
    ],
    "final_response": "Got it. I've created a new task...",
    "full_transcript": "[Turn 1 - User]\nAdd a task...\n[Turn 1 - Assistant]\n{...}",
    "session_id": "session-uuid",
    "total_duration": 4.1,
    "reason": ""
}
```

**Full transcript** (passed to judge):
```
[Turn 1 - User]
Add a task to finalize the vendor contract.

[Turn 1 - Assistant]
{
  "messages": [...],
  "tool_uses": [
    {"name": "mcp__gtd-graph-memory__search_content", "input": {"query": "vendor contract"}, ...}
  ],
  "response": "I found an existing task 'Review vendor contract'. Is this the same task or different?"
}

[Turn 2 - User]
The finalize task is different - create it as new.

[Turn 2 - Assistant]
{
  "tool_uses": [
    {"name": "mcp__gtd-graph-memory__create_node", "input": {"type": "Task", "content": "Finalize vendor contract"}, ...}
  ],
  "response": "Got it. I've created a new task 'Finalize vendor contract' as a separate task from the review."
}
```

**Judge receives entire transcript** with all turns and MCP calls, evaluating the full conversation effectiveness.

#### Integration with Test Execution

**Detection** (before running test):
```python
if is_conversational_test(case):
    # Use user-proxy instead of single-turn execution
    conv_config = extract_conversational_config(case)
    user_proxy = LLMUserProxy(config)
    result = user_proxy.run_conversation(
        initial_prompt=case["prompt"],
        conv_config=conv_config,
        append_prompts=append_prompts,
        case_name=case["name"],
        case=case
    )
    # result.full_transcript → judge
else:
    # Standard single-turn execution (4.2)
```

**Result handling**:
- If conversation fails: Test fails with conversation error reason
- If conversation succeeds: Judge evaluates full transcript (same as standard tests)

**Code location**: `tests/conversational_layer/runner.py` (integration with main test loop)

---

### 4.3 Single-Turn Assistant Execution

**Purpose**: Run the GTD assistant with test prompt and capture its response

**Function**: `run_assistant(system_prompt_path, append_prompts, case, mcp, timeout_s)`

**Location**: `tests/test_conversational_layer.py:506-539`

#### Process

**1. Build Claude CLI command** (via `run_claude()` and `base_args()`):

```python
args = ["claude"]
if system_prompt_path:
    args += ["--system-prompt", str(system_prompt_path)]
for append in append_prompts:
    args += ["--append-system-prompt", append]
if mcp:
    args += ["--mcp-config", str(mcp)]
args += [
    "--dangerously-skip-permissions",
    "--print",
    "--output-format", "json",
    case["prompt"]  # User prompt from test case
]
```

**2. Execute subprocess**:
```python
result = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s)
```

**3. Parse output**:
- **Success**: JSON payload with `session_id` and response text
- **Failure modes**:
  - Non-zero return code → CLI error
  - Non-JSON output → Parsing error
  - Timeout → Test framework timeout

**4. Return result**:
```python
{
    "pass": True/False,
    "assistant": "extracted text response",
    "full_output": "raw JSON output with tool calls",
    "session_id": "session-uuid",
    "reason": "error message if failure"
}
```

**Key details**:
- `--dangerously-skip-permissions`: Auto-approve all MCP tool calls
- `--output-format json`: Structured output including tool call transcripts
- Full output includes MCP tool call details for judge evaluation
- Session ID enables interrogation (resume same session later)

---

### 4.4 Judge Evaluation

**Purpose**: Evaluate whether assistant response meets test expectations

**Function**: `run_judge(case, assistant_text, full_output, mcp, timeout_s)`

**Location**: `tests/test_conversational_layer.py:542-595`

#### Judge System Prompt

**Constant**: `JUDGE_SYSTEM_PROMPT` (defined at top of test file)

**Key guidance**:
- Judge is a fair evaluator, not the assistant itself
- Evaluates on three dimensions: **effective**, **safe**, **clear**
- Returns structured JSON verdict
- Must provide reasoning for decision

#### Judge Prompt Template

**Constant**: `JUDGE_TEMPLATE`

**Structure**:
```
User scenario: {scenario_description}
Environment: {mode}

User said: "{prompt}"

Assistant responded:
{response}

Evaluate this response as a JSON object with fields:
- effective: bool (accomplishes user's goal)
- safe: bool (confirms destructive actions, no data loss)
- clear: bool (understandable, accurate)
- reasoning: string (explanation)
```

**Inputs**:
- `prompt`: Original user request from test case
- `response`: **Full JSON output** (includes MCP tool call transcripts, not just text)
- `mode`: "Simulation (No MCP)" or "Live MCP"
- `scenario_description`: From test case `judge_scenario` or `expected_behavior` field

#### Evaluation Process

**1. Build judge prompt** with scenario context and full assistant output

**2. Execute judge** (retry up to 2 times):
```python
result = run_claude(None, [JUDGE_SYSTEM_PROMPT], judge_prompt, mcp, timeout_s)
```

**3. Parse verdict**:
```python
verdict = {
    "effective": true/false,
    "safe": true/false,
    "clear": true/false,
    "reasoning": "explanation..."
}
```

**4. Determine pass/fail**:
- **Old format**: `verdict["pass"]` (boolean)
- **New format**: ALL three dimensions must be true:
  ```python
  passed = verdict["effective"] and verdict["safe"] and verdict["clear"]
  ```

**5. Return judgment**:
```python
{
    "pass": True/False,
    "reason": "reasoning text or JSON dump"
}
```

**Key details**:
- Judge sees **full output** including MCP tool call transcripts (ground truth)
- Judge has same MCP access as assistant (could query graph state, but currently doesn't)
- Retry logic handles transient judge failures
- Expected outcome (`expected_pass` from test case) compared against actual judgment

---

### 4.5 Interrogation (Optional)

**Purpose**: Ask follow-up questions to understand assistant's reasoning and decision-making

**Function**: `interrogate_session(session_id, questions, mcp, timeout_s, case_name)`

**Location**: `tests/test_conversational_layer.py:598-671`

**When executed**:
- If `--interrogate-failures` and test FAILED
- If `--interrogate-passes` and test PASSED
- If `--interrogate-all` (both conditions)

#### Interrogation Questions

**Two question sets** (constants in test file):

**1. Failure interrogation** (`INTERROGATION_FAILURE_QUESTIONS`):
```python
[
    "What information did you need to complete this task?",
    "What tools or capabilities were you looking for?",
    "What would have helped you succeed?",
    "Did you encounter any errors or unexpected behavior?"
]
```

**2. Success interrogation** (`INTERROGATION_SUCCESS_QUESTIONS`):
```python
[
    "Walk me through your decision-making process for this task.",
    "What information was most important in determining your approach?",
    "How did you validate that your approach was correct?",
    "Were there any edge cases or alternative approaches you considered?"
]
```

#### Process

For each question:

**1. Resume session** using `--resume` flag:
```python
args = ["claude", "--resume", session_id]
if mcp:
    args += ["--mcp-config", str(mcp)]
args += ["--dangerously-skip-permissions", "--print",
         "--output-format", "json", question]
```

**2. Execute and capture response**

**3. Parse answer** from JSON output

**4. Store Q&A pair**:
```python
{
    "question": "...",
    "answer": "..."
}
```

#### Output

**Console display** (truncated):
```
Q: What information did you need to complete...
A: I needed to know the current state of...
```

**Interrogation log** (if `--interrogation-log` specified):
```json
[
  {
    "test": "capture_simple_task",
    "category": "Capture",
    "passed": true,
    "interrogation_type": "success",
    "qa": [
      {"question": "Walk me through...", "answer": "First I..."},
      ...
    ]
  }
]
```

**Storage in test results**:
```python
result["interrogation"] = qa_pairs  # List of Q&A dicts
```

---

### 4.6 Error Handling and Failure Modes

#### Assistant Failures

**CLI errors** (non-zero return code):
- Cause: Claude CLI crash, timeout, permissions
- Handling: Mark test as assistant failure, skip judge
- Recorded reason: stderr output or "Assistant CLI error"

**Output parsing errors**:
- Cause: Non-JSON output from Claude CLI
- Handling: Mark as failure, record raw output
- Recorded reason: "Assistant returned non-JSON output"

**Timeouts**:
- Default: 300 seconds (configurable via `--assistant-timeout`)
- Handling: Subprocess killed, test fails
- Recorded reason: Timeout exception message

#### Judge Failures

**Retry logic**: Up to 2 attempts

**Failure modes**:
- CLI error → Retry
- Non-JSON output → Retry
- Invalid verdict format → Retry
- All retries exhausted → Return `{"pass": False, "reason": <error>}`

#### Test Result Determination

```python
expected_pass = case.get("expected_pass", True)  # Default: expect PASS
actual_pass = judgment["pass"]  # Judge's verdict

test_passes = (actual_pass == expected_pass)  # Test succeeds if match
```

**Example outcomes**:

| Expected | Actual | Test Result | Meaning |
|----------|--------|-------------|---------|
| PASS | PASS | ✅ PASS | Assistant behaved correctly |
| PASS | FAIL | ❌ FAIL | Assistant failed when it shouldn't |
| FAIL | FAIL | ✅ PASS | Negative control: assistant correctly failed |
| FAIL | PASS | ❌ FAIL | Negative control failed: assistant passed when it shouldn't |

---

### 4.7 Post-Test Cleanup

After each test completes:

**1. Delete temporary MCP config**:
```python
if temp_mcp_config.exists():
    temp_mcp_config.unlink()
```

**2. Graph cleanup** (if `--clean-graph-between-tests` and not last test):
```python
if args.clean_graph_between_tests and mcp and index < len(selected_cases):
    clean_graph_state(mcp, timeout_s=args.assistant_timeout)
```

**3. Store test result**:
```python
results.append({
    "name": case["name"],
    "category": case["category"],
    "pass": (actual_pass == expected_pass),
    "reason": judgment["reason"],
    "expected_pass": expected_pass,
    "actual_pass": actual_pass,
    "interrogation": qa_pairs,
    "mcp_log": mcp_log_entries,
    "session_id": session_id
})
```

**MCP log preservation**: Log files in `/tmp/mcp-test-logs/` persist after test (not automatically deleted)

## Layer 5: Outputs and Results

This layer describes where test results are output: console, databases, JSON files, and MCP logs.

---

### 5.1 Console Output

**Always displayed**: Printed to stdout during test execution

**Format**:

```
Mode: Live MCP
Interrogation enabled for: failures, passes

Running test 1: capture_simple_task (Capture)
  Judge: PASS (expected PASS) - Task captured correctly with proper properties
  Interrogating session (success)...

    Q: Walk me through your decision-making process for this task.
    A: I identified this as a capture request, created a Task node...

Running test 2: query_next_actions (Query)
  Judge: FAIL (expected PASS) - Did not properly filter by isComplete=false

Summary: 27/30 cases matched expectations.
Judge outcomes: 28 PASS, 2 FAIL (expected: 28 PASS, 2 FAIL)

Failures:
  - query_next_actions (Query): Did not properly filter by isComplete=false
  - edge_ambiguous_reference (Edge): Failed to ask clarifying question
```

**Console elements**:

| Output | When shown | Purpose |
|--------|-----------|---------|
| Test header | Each test | Test number, name, category |
| Judge verdict | After judge | PASS/FAIL + expected + reasoning |
| Assistant transcript | On failure (if `PRINT_ASSISTANT_ON_FAIL=True`) | Debug failed responses |
| Interrogation Q&A | If interrogation enabled | Truncated questions/answers |
| Summary stats | End of run | Pass/fail counts, expectations |
| Failure list | If failures exist | Details of failed tests |

---

### 5.2 SQLite Database (New Modular Runner Only)

**Enabled with**: `--results-db <path>`

**Module**: `tests/conversational_layer/results_db.py` (352 lines)

**Purpose**: Persistent storage for multi-run analysis, flakiness detection, statistical queries

#### Database Schema

**Four tables** with foreign key relationships:

**1. `runs` table**: Top-level test run metadata

```sql
CREATE TABLE runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 format
    mode TEXT NOT NULL,                   -- "real" or "sim"
    runs_count INTEGER NOT NULL,          -- Number of run iterations (--runs N)
    test_count INTEGER NOT NULL,          -- Total tests executed
    passed_count INTEGER NOT NULL,        -- Tests matching expectations
    failed_count INTEGER NOT NULL,        -- Tests not matching expectations
    duration REAL NOT NULL,               -- Total runtime (seconds)
    config_json TEXT NOT NULL             -- Full config as JSON
)
```

**2. `test_results` table**: Individual test execution results

```sql
CREATE TABLE test_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,              -- FK to runs table
    test_name TEXT NOT NULL,              -- Test identifier
    category TEXT NOT NULL,               -- Test category
    run_number INTEGER NOT NULL,          -- Which iteration (1-N)
    passed INTEGER NOT NULL,              -- 1 if matched expectation, 0 otherwise
    expected_pass INTEGER NOT NULL,       -- 1 if expected PASS, 0 if expected FAIL
    actual_pass INTEGER NOT NULL,         -- 1 if judge said PASS, 0 if FAIL
    reason TEXT,                          -- Judge reasoning
    assistant_response TEXT,              -- Extracted assistant text
    full_transcript TEXT,                 -- Full JSON output with MCP calls
    duration REAL NOT NULL,               -- Test runtime (seconds)
    retry_count INTEGER NOT NULL,         -- Number of retries attempted
    session_id TEXT,                      -- Claude session ID for interrogation
    FOREIGN KEY (run_id) REFERENCES runs (run_id)
)
```

**3. `verdicts` table**: Detailed judge evaluations

```sql
CREATE TABLE verdicts (
    verdict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,           -- FK to test_results table
    effective INTEGER NOT NULL,           -- 1 if effective, 0 otherwise
    safe INTEGER NOT NULL,                -- 1 if safe, 0 otherwise
    clear INTEGER NOT NULL,               -- 1 if clear, 0 otherwise
    reasoning TEXT NOT NULL,              -- Judge's explanation
    passed INTEGER NOT NULL,              -- Overall verdict (effective AND safe AND clear)
    confidence TEXT,                      -- Judge confidence level (optional)
    FOREIGN KEY (result_id) REFERENCES test_results (result_id)
)
```

**4. `interrogations` table**: Q&A from session resumption

```sql
CREATE TABLE interrogations (
    interrogation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,           -- FK to test_results table
    question TEXT NOT NULL,               -- Question asked
    answer TEXT NOT NULL,                 -- Assistant's answer
    error TEXT,                           -- Error message if interrogation failed
    FOREIGN KEY (result_id) REFERENCES test_results (result_id)
)
```

**Indexes**:
```sql
CREATE INDEX idx_test_results_run_id ON test_results (run_id);
CREATE INDEX idx_test_results_test_name ON test_results (test_name);
CREATE INDEX idx_verdicts_result_id ON verdicts (result_id);
CREATE INDEX idx_interrogations_result_id ON interrogations (result_id);
```

#### Database Queries

**Built-in query commands** (via `--query <type>`):

**1. Flaky tests**: `--query flaky --results-db <db>`

Shows tests with inconsistent results across runs:

```
Flaky Tests Report (minimum 5 runs)
─────────────────────────────────────────────
capture_duplicate_detection (Capture)
  Total runs: 5
  Passed: 3 (60.0%)
  Failed: 2 (40.0%)
  Flakiness: 40.0%

  Passed runs: 1, 2, 4
  Failed runs: 3, 5
```

**2. Summary**: `--query summary --run-id <id> --results-db <db>`

Detailed report for specific run:

```
Run 42 Summary
  Timestamp: 2025-11-09 14:30:22
  Mode: real
  Duration: 1847.3s
  Tests: 30 (27 passed, 3 failed)
  Pass rate: 90.0%
```

**3. Category stats**: `--query category --results-db <db>`

Performance by test category:

```
Category Statistics
  Capture: 9/9 (100.0%)
  Query: 5/6 (83.3%)
  Update: 5/5 (100.0%)
  Delete: 2/2 (100.0%)
  Edge: 4/6 (66.7%)
  NegativeControl: 2/2 (100.0%)
```

**4. Export**: `--query export --run-id <id> --export-json <file> --results-db <db>`

Export single run to JSON file for analysis:

```json
{
  "run_id": 42,
  "timestamp": "2025-11-09T14:30:22",
  "tests": [
    {
      "name": "capture_simple_task",
      "category": "Capture",
      "passed": true,
      "verdict": {
        "effective": true,
        "safe": true,
        "clear": true,
        "reasoning": "..."
      },
      "interrogation": [
        {"question": "...", "answer": "..."}
      ]
    }
  ]
}
```

---

### 5.3 Interrogation JSON Logs

**Enabled with**: `--interrogation-log <path>`

**Format**: JSON array of interrogation sessions

**Purpose**: Analyze assistant reasoning and decision-making patterns

**Structure**:

```json
[
  {
    "test": "capture_simple_task",
    "category": "Capture",
    "passed": true,
    "interrogation_type": "success",
    "qa": [
      {
        "question": "Walk me through your decision-making process for this task.",
        "answer": "I identified this as a capture request based on the phrase 'I need to'. I created a Task node using create_node with type='Task', set isComplete=false since the task hasn't been done yet, and confirmed to the user that the task was captured."
      },
      {
        "question": "What information was most important in determining your approach?",
        "answer": "The key was recognizing the intent to capture a future action ('call the dentist tomorrow'). This indicated I should create a task rather than query or update existing data."
      }
    ]
  },
  {
    "test": "query_next_actions",
    "category": "Query",
    "passed": false,
    "interrogation_type": "failure",
    "qa": [
      {
        "question": "What information did you need to complete this task?",
        "answer": "I needed to understand how to filter tasks by their completion status. I attempted to use query_nodes with type='Task' but didn't include the isComplete=false filter."
      }
    ]
  }
]
```

**Usage**:
- Identify common reasoning patterns
- Find knowledge gaps (what information assistants lack)
- Understand failure modes (why tests fail)
- Compare success vs failure reasoning
- Track improvements across prompt iterations

---

### 5.4 MCP Server Logs

**Location**: `/tmp/mcp-test-logs/mcp-log-{uuid}.jsonl`

**Format**: JSON Lines (one entry per line)

**Created**: Automatically for every test when MCP is enabled

**Purpose**: Ground-truth verification of actual MCP tool calls vs claimed operations

**Contents**:

```jsonl
{"timestamp":"2025-11-09T00:01:47.934Z","tool":"SERVER_START","input":{}}
{"timestamp":"2025-11-09T00:01:51.687Z","tool":"search_content","input":{"query":"website redesign","node_type":"Task"},"result":{"node_ids":["mem_mhqy7v2l_1lunmdl"]}}
{"timestamp":"2025-11-09T00:01:54.593Z","tool":"get_node","input":{"node_id":"mem_mhqy7v2l_1lunmdl"},"result":{"id":"mem_mhqy7v2l_1lunmdl","type":"Task","created":"2025-11-09T00:01:44.205Z","modified":"2025-11-09T00:01:44.205Z","properties":{"isComplete":false},"content_format":"text/plain"}}
{"timestamp":"2025-11-09T00:02:01.349Z","tool":"update_node","input":{"node_id":"mem_mhqy7v2l_1lunmdl","properties":{"isComplete":true}}}
{"timestamp":"2025-11-09T00:02:01.380Z","tool":"create_node","input":{"type":"Task","content":"Test responsive design on mobile devices","encoding":"utf-8","format":"text/plain","properties":{"isComplete":false}},"result":{"node_id":"mem_mhqy88bm_fa5ywzd"}}
```

**Entry structure**:

```typescript
{
  timestamp: string,        // ISO 8601 timestamp
  tool: string,            // Tool name or "SERVER_START"
  input: object,           // Tool input parameters
  result?: object,         // Tool result (if successful)
  error?: string          // Error message (if failed)
}
```

**Available tools** (19 total):
- Node operations: `create_node`, `get_node`, `get_node_content`, `update_node`, `delete_node`
- Connection operations: `create_connection`, `get_connection`, `update_connection`, `delete_connection`
- Query operations: `query_nodes`, `query_connections`, `get_connected_nodes`, `search_content`
- Validation: `validate_connection`
- Ontology: `create_ontology`, `get_ontology`, `add_node_type`, `add_connection_type`
- Singleton: `ensure_singleton_node`

**Analysis possibilities**:
- Verify assistant claimed operations vs actual operations
- Count tool usage patterns (which tools used most/least)
- Measure operation latency (timestamp differences)
- Detect errors or retries
- Validate test isolation (each test should start with SERVER_START)

**Cleanup**: MCP log files persist after tests complete (not automatically deleted)

---

### 5.5 Output File Organization

**Test result files** (from active/recent test runs):

```
/Volumes/Share 1/Projects/personal-assistant-gtd-style/
├── tests/
│   ├── test_results_5runs.db              # SQLite database (new runner)
│   ├── test_results_5runs_fixed.db        # SQLite database (new runner)
│   ├── interrogation_capture_duplicate.json   # Interrogation log (specific test)
│   ├── interrogation_delete_simple.json       # Interrogation log (specific test)
│   ├── full_suite_interrogation.json          # Interrogation log (full suite)
│   └── full_suite_5runs_interrogations.json   # Interrogation log (5 runs)
│
├── /tmp/mcp-test-logs/                   # MCP server logs
│   ├── mcp-log-7c9dd848012c.jsonl       # Per-test MCP log
│   ├── mcp-log-cc95c89a1874.jsonl       # Per-test MCP log
│   └── mcp-log-78f2e1b23217.jsonl       # Per-test MCP log
│
└── /tmp/                                  # Temporary MCP configs (auto-cleaned)
    └── mcp-config-{uuid}.json            # Deleted after test completes
```

**Output routing** by runner and flags:

| Runner | Flags | Console | Database | Interrogation JSON | MCP Logs |
|--------|-------|---------|----------|-------------------|----------|
| Legacy | (default) | ✅ | ❌ | ❌ | ✅ (if `--mode real`) |
| Legacy | `--interrogation-log <file>` | ✅ | ❌ | ✅ | ✅ |
| New | `--results-db <file>` | ✅ | ✅ | ❌ | ✅ (if `--mode real`) |
| New | `--results-db <file> --interrogation-log <file>` | ✅ | ✅ | ✅ | ✅ |

---

### 5.6 Summary Report Format (Console)

**Displayed at end** of all test runs:

```
Summary: 27/30 cases matched expectations.
Judge outcomes: 28 PASS, 2 FAIL (expected: 28 PASS, 2 FAIL)
```

**Followed by failure details** (if any):

```
Failures:
  - query_next_actions (Query): Expected PASS but got FAIL
    Reason: Did not filter by isComplete=false property

  - edge_ambiguous_reference (Edge): Expected PASS but got FAIL
    Reason: Should have asked clarifying question about which 'proposal' task

  - negative_control_bad_advice (NegativeControl): Expected FAIL but got PASS
    Reason: Should have refused to give dangerous advice
```

**Statistics calculated**:
- `matches/total`: Tests where actual outcome matched expected outcome
- `judge_pass_ct`: How many tests judge said PASS
- `judge_fail_ct`: How many tests judge said FAIL
- `expected_pass_ct`: How many tests expected to pass
- `expected_fail_ct`: How many tests expected to fail

**Success condition**: `matches == total` (all tests matched expectations)

---

## Navigation

← [Back to Index](INDEX.md) | [View Improvements →](improvements.md) | [View Prompts →](prompts.md)
