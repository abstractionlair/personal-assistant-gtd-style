# Testing Infrastructure Improvements

> **Part of**: [GTD Testing Documentation](INDEX.md) | **See also**: [Infrastructure](infrastructure.md) · [Prompts](prompts.md)

**Status**: Collecting ideas as we document
**Last Updated**: 2025-11-09

This document captures improvements, issues, and potential changes discovered while documenting the current testing infrastructure.

---

## Layer 1: Test Execution

### 1.1 Delete Legacy Test Runner

**Current state**: Two parallel test runners (legacy `test_conversational_layer.py` + new modular system)

**Issue**: Maintenance burden of supporting two systems with overlapping functionality

**Proposed change**:
- Delete `tests/test_conversational_layer.py` (1,142 lines)
- Keep only the new modular system (`test_conversational_layer_new.py` + modules)
- Migrate any unique features from legacy to new system first

**Benefits**:
- Single source of truth
- Reduced code maintenance
- Clearer documentation
- No confusion about which runner to use

### 1.2 Replace `--clean-graph-between-tests` with Explicit Test Lifecycle Configuration

**Current state**: Binary flag `--clean-graph-between-tests` applies cleanup uniformly after every test

**Issue**: Inflexible - some test sequences should share state, others need isolation

**Proposed change**: Support explicit test lifecycle phases in test case configuration:

```json
{
  "test_sequences": [
    {
      "name": "query_sequence_with_shared_state",
      "setup": {
        "clean_graph": true,
        "fixtures": ["tasks", "contexts"]
      },
      "tests": [
        "query_next_actions",
        "query_projects",
        "query_waiting_for"
      ],
      "teardown": {
        "clean_graph": true
      }
    },
    {
      "name": "isolated_tests",
      "setup": {"clean_graph": true},
      "tests": ["capture_simple_task"],
      "teardown": {"clean_graph": true}
    }
  ]
}
```

**Benefits**:
- Tests can intentionally share state when testing sequential workflows
- Explicit control over when cleanup happens
- Better performance (less unnecessary cleanup)
- Test intent is clearer in configuration
- Supports complex test scenarios (setup → test sequence → teardown)

**Migration path**:
- Current `--clean-graph-between-tests` behavior = every test is its own sequence with cleanup
- New default: tests in same sequence share state, sequences are isolated

---

## Layer 2: Inputs

### 2.1 Consolidate to Refactored Test Cases Only

**Current state**: Two test case files exist:
- `tests/test_cases.json` (380 lines, 30 tests)
- `tests/test_cases_refactored.json` (untracked, appears to be newer iteration)

**Issue**: Redundancy and potential for divergence between two test definitions

**Proposed change**:
- Delete `tests/test_cases.json`
- Keep only `tests/test_cases_refactored.json`
- Possibly update refactored test cases based on findings
- Remove CLI shorthand support for old test cases

**Benefits**:
- Single source of truth for test definitions
- No confusion about which test file to use
- Easier maintenance and updates
- Clear migration path

### 2.2 Eliminate Simulation Mode

**Current state**: Three test modes supported:
- `--mode auto` (detect MCP availability)
- `--mode real` (live MCP server)
- `--mode sim` (no MCP, simulated operations)

**Issue**: Simulation mode risks accidentally training or testing assistant with incorrect behavior patterns

**Proposed change**:
- Remove `--mode sim` support entirely
- Remove `tests/fixtures/system-prompt-no-mcp-overlay.md`
- Remove simulation mode logic from test runners
- Remove CLI arguments and documentation references
- Keep only `--mode real` (or simplify to no mode flag at all)

**Benefits**:
- Tests only validate real MCP operations
- No risk of sim-mode artifacts in assistant responses
- Simpler test infrastructure (one less code path)
- Clearer testing intent (always test real behavior)

**Files to modify**:
- `tests/test_conversational_layer.py` (legacy, will be deleted anyway)
- `tests/test_conversational_layer_new.py`
- `tests/fixtures/system-prompt-no-mcp-overlay.md` (delete)
- Documentation files

---

## Layer 3: Setup and Initialization

### 3.1 Direct Storage Deletion for Graph Cleanup

**Current state**: Graph cleanup uses Claude CLI with specialized cleanup prompt to delete all nodes

**Implementation**:
- Calls Claude with system prompt: "You are a graph cleanup utility..."
- Relies on model to query all nodes and delete each one
- Can timeout or fail if model makes mistakes

**Issue**:
- Slower than direct filesystem operations
- Adds complexity (subprocess, timeout handling, error checking)
- Uses model for task that doesn't require intelligence
- Can fail in unexpected ways

**Proposed change**:
- Delete storage directory and recreate fresh
- Or use direct programmatic API to clear graph
- Options:
  1. `rm -rf .data/gtd-memory/test/* && mkdir -p .data/gtd-memory/test/`
  2. Python: `shutil.rmtree()` and recreate
  3. Direct graph API: `graph.delete_all_nodes()` method

**Benefits**:
- Much faster (milliseconds vs seconds)
- Guaranteed clean state (no possibility of incomplete cleanup)
- Simpler code (no subprocess, prompts, or model interaction)
- No timeout or model failure modes
- More reliable test isolation

### 3.2 Judge Direct Access to MCP Server State

**Current state**: Judge only evaluates assistant response text and MCP call logs (files)

**Issue**:
- Logs capture what was called, but not final graph state
- If model calls wrong tool or uses wrong parameters, logs show the error but judge may not validate final state
- No direct verification of graph state matches expectations

**Proposed change**:
- Allow judge to query MCP server directly
- Judge can verify actual graph state after test completes
- Examples:
  - "Task should exist" → Judge queries for task, confirms it exists
  - "Task should be marked complete" → Judge reads task properties
  - "Two tasks should have dependency" → Judge queries connections

**Benefits**:
- Ground truth validation of actual state vs claimed state
- Catches cases where assistant called tools but state is wrong
- More robust test validation
- Can verify both process (logs) and outcome (state)

**Implementation options**:
1. Judge gets same MCP config as assistant
2. Judge uses Python MCP client library directly
3. Judge uses dedicated read-only validation tools

### 3.3 Programmatic Fixture Setup

**Current state**: Fixtures set up via Claude CLI with natural language instructions

**Implementation**:
- Converts JSON fixture to natural language: "Create an incomplete task: 'File quarterly taxes'"
- Uses Claude with system prompt: "You are a test fixture setup utility..."
- Relies on model to interpret and execute setup

**Issue**:
- Model-based setup can fail or be inconsistent
- Slower than direct programmatic approach
- Adds complexity and potential failure modes
- Setup is deterministic data - doesn't need model intelligence
- Can timeout or produce unexpected results

**Proposed change**:
- Use direct programmatic MCP client to create fixtures
- Python code that directly calls MCP tools
- Example:
  ```python
  def setup_fixture(fixture: dict, mcp_client):
      for task in fixture.get("tasks", []):
          node_id = mcp_client.create_node(
              type="Task",
              content=task["content"],
              properties={"isComplete": task["isComplete"]}
          )
          # Handle dependencies...
  ```

**Benefits**:
- Faster and more reliable
- Deterministic setup (same input = same state)
- Easier to debug (Python stack traces vs model behavior)
- No timeouts or model failure modes
- Clearer code - see exactly what's being created
- Can return created node IDs for test assertions

**Migration path**:
- Implement programmatic setup first
- Run both approaches in parallel to verify equivalence
- Switch over once validated
- Remove model-based setup code

---

## Layer 4: Execution Flow

### 4.1 Parallel Test Execution

**Current state**: Tests execute sequentially, one after another

**Issue**:
- Slow for large test suites (30 tests × 5 runs = 150 sequential executions)
- Underutilizes available CPU/memory resources
- Long feedback cycles for developers

**Proposed change**:
- Run independent tests in parallel (configurable parallelism)
- Options:
  1. `--parallel N` flag to run N tests concurrently
  2. Automatic parallelism detection based on CPU cores
  3. Smart scheduling based on test duration history

**Benefits**:
- Faster test runs (could reduce 30 min run to 5-10 min)
- Better resource utilization
- Maintains isolation (each test has own MCP server instance)

**Considerations**:
- Need to ensure graph isolation (separate storage paths per test)
- May complicate output formatting (interleaved console output)
- Need to handle parallel MCP server instances

### 4.2 Enhanced Judge Evaluation

**Current state**: Judge evaluates three dimensions (effective, safe, clear) but only sees text output and logs; Python code does simple validation like `_has_mcp_calls()`

**Proposed changes**:

1. **Judge-driven validation (not hardcoded Python logic)**:
   - Remove hardcoded checks like `_has_mcp_calls()` from Python
   - Judge model decides what to look for based on test scenario
   - More flexible: judge can adapt validation to specific test requirements
   - Example: Judge determines if search was needed before asking question, not fixed rule

2. **Judge direct MCP server access**:
   - Judge can query MCP server to verify final graph state
   - Not just logs (what was called) but actual outcomes (what resulted)
   - Examples:
     - "Verify task exists with correct properties"
     - "Confirm dependency connection was created"
     - "Check that context has correct isAvailable state"
   - Ground truth validation: claimed vs actual state

3. **Multiple judge models for consensus**:
   - Run 2-3 different models as judges
   - Require majority agreement or flag disagreements
   - Helps identify borderline cases

4. **Judge confidence scoring**:
   - Judge reports confidence level (0-1 scale)
   - Low confidence triggers manual review or re-evaluation
   - Track confidence trends over time

5. **Semantic similarity evaluation**:
   - Compare assistant response to reference implementations
   - Use embedding-based similarity for fuzzy matching
   - Helps detect correct but differently-worded responses

**Benefits**:
- More robust evaluation (reduce false positives/negatives)
- Better handling of edge cases
- Visibility into evaluation uncertainty
- Simpler Python code (less hardcoded validation logic)
- More accurate: validate outcomes not just process

### 4.3 User-Proxy Enhancements

**Current state**: LLM user-proxy generates responses but uses single persona; conversational mode is optional

**Proposed changes**:

1. **Standardize on user-proxy (make non-optional)**:
   - All tests should use conversational mode by default
   - Single-turn tests are just conversational tests with one turn
   - Eliminates distinction between test modes
   - Simpler, more consistent testing approach

2. **User-proxy drives assistant session (not Python alternation)**:
   - Instead of Python code alternating between user-proxy and assistant
   - User-proxy Claude Code session directly "drives" assistant Claude Code session
   - User-proxy calls `claude --resume <assistant-session-id>` via Bash tool
   - Use `--append-system-prompt` for user-proxy role instructions (base system prompt helpful for calling Claude Code)
   - More realistic: simulates real user interacting with assistant

3. **Dynamic conversation length (not fixed max_turns)**:
   - User-proxy should stop when satisfied task is accomplished
   - No artificial max_turns limit
   - User-proxy evaluates goal completion after each turn
   - More natural conversation flow

4. **User persona simulation**:
   - Configure user expertise level (novice, intermediate, expert)
   - Simulate user frustration/impatience after multiple turns
   - Vary communication style (terse, verbose, unclear)

5. **Adversarial user mode**:
   - Intentionally unclear or contradictory responses
   - Edge case handling (typos, ambiguous references)
   - Stress testing conversation handling

6. **User goal tracking**:
   - Explicit goal state machine
   - Track goal progress across turns
   - Validate goal achievement at end

**Benefits**:
- More realistic conversation testing
- Better coverage of user behavior variations
- Improved robustness to difficult users
- Simpler architecture (no Python orchestration logic)
- More flexible conversation lengths

### 4.4 Enhanced Interrogation

**Current state**: Interrogation uses fixed question lists; interrogator doesn't see judge verdict

**Proposed changes**:

1. **Interrogator drives session (like user-proxy)**:
   - Interrogator Claude Code session drives assistant session via `--resume`
   - Use `--append-system-prompt` for interrogator role instructions
   - Same pattern as user-proxy driving assistant

2. **Dynamic interrogation (not fixed questions)**:
   - Interrogator model has more leeway to ask follow-up questions
   - Can adapt questions based on assistant responses
   - Conversational interrogation rather than questionnaire

3. **Interrogator sees judge verdict**:
   - Provide judge's evaluation to interrogator
   - Ask specifically about areas judge identified as weak
   - More targeted questioning based on actual issues

4. **Context-aware questioning**:
   - Interrogator sees test scenario and expected behavior
   - Can probe specific decisions or trade-offs
   - Adaptive depth (ask more about problematic areas)

**Benefits**:
- More insightful interrogation results
- Better understanding of failure modes
- Adaptive questioning based on context
- Simpler Python orchestration code

### 4.5 Better Error Recovery

**Current state**: Errors cause immediate test failure

**Proposed changes**:

1. **Transient error retry**:
   - Distinguish transient (network, timeout) from persistent errors
   - Automatic retry with exponential backoff
   - Report retry counts in results

2. **Graceful degradation**:
   - Continue test run even if some tests crash
   - Isolate failures (one test crash doesn't kill suite)
   - Capture crash dumps for debugging

3. **Error categorization**:
   - Tag errors by type (MCP, judge, timeout, parsing)
   - Aggregate error patterns across runs
   - Identify systemic issues vs one-off failures

**Benefits**:
- More reliable test runs
- Better visibility into error patterns
- Reduced manual intervention

---

## Layer 5: Outputs and Results

### 5.1 Unified Output Format

**Current state**: Multiple output formats (console, SQLite, JSON) with overlapping data

**Issue**:
- Data duplication across formats
- Inconsistent schemas between formats
- Hard to maintain multiple output paths

**Proposed change**:
- Define canonical output schema (e.g., JSON Schema)
- Generate all output formats from canonical representation
- Schema versioning for backwards compatibility

**Benefits**:
- Single source of truth for test results
- Easier to add new output formats
- Guaranteed consistency across outputs

### 5.2 Real-Time Test Dashboard

**Current state**: Only console output during runs; SQLite for post-run analysis

**Proposed change**:
- Web-based dashboard that reads SQLite database in real-time
- Features:
  - Live test progress (which test running, estimated time remaining)
  - Pass/fail counts updating in real-time
  - Recent failures highlighted
  - Historical trends (success rate over time)
  - Flakiness detection and alerts

**Benefits**:
- Better visibility during long test runs
- Quick identification of problems
- Easier sharing of results with team

**Implementation options**:
1. Simple Flask/FastAPI app reading SQLite
2. Static HTML + JavaScript polling SQLite
3. WebSocket-based live updates

### 5.3 MCP Log Analysis Tools

**Current state**: MCP logs are JSON Lines files, manually inspected

**Proposed changes**:

1. **Log aggregation and querying**:
   - Import all MCP logs into test results database
   - Query interface for finding patterns (e.g., "all tests that call update_node")
   - Time-series analysis of tool usage

2. **Automated verification**:
   - Check MCP logs against expected tool call sequences
   - Validate that claimed operations match actual logs
   - Flag discrepancies automatically

3. **Visualization**:
   - Timeline view of tool calls
   - Dependency graphs (which nodes/connections were created/modified)
   - Operation frequency heatmaps

**Benefits**:
- Deeper insights into assistant behavior
- Ground truth verification without manual inspection
- Pattern discovery across test runs

### 5.4 Test Result Visualization

**Current state**: Text-based summary reports only

**Proposed changes**:

1. **Charts and graphs**:
   - Pass rate trends over time
   - Per-category performance breakdown
   - Flakiness visualization
   - Test duration distributions

2. **Comparative analysis**:
   - Compare results across different runs
   - Compare different models (Sonnet vs Opus)
   - Compare different system prompt versions
   - A/B testing support

3. **Regression detection**:
   - Highlight tests that recently started failing
   - Alert on degraded pass rates
   - Track improvements over time

**Benefits**:
- Easier to understand test results at a glance
- Identify trends and patterns
- Make data-driven decisions about prompt/model changes

### 5.5 Interrogation Analysis

**Current state**: Interrogation data stored but not analyzed systematically

**Proposed changes**:

1. **Reasoning pattern extraction**:
   - NLP analysis of interrogation responses
   - Cluster common reasoning patterns
   - Identify knowledge gaps by analyzing what information assistants request

2. **Success vs failure comparison**:
   - Side-by-side comparison of reasoning for passed vs failed tests
   - Identify what distinguishes successful approaches
   - Extract best practices from successful reasoning

3. **Automated insight generation**:
   - Summarize common failure modes
   - Suggest system prompt improvements based on patterns
   - Generate training examples from successful interrogations

**Benefits**:
- Turn interrogation data into actionable insights
- Improve system prompts based on evidence
- Build knowledge base of effective reasoning patterns

### 5.6 Comprehensive Data Capture

**Current state**: Tests capture JSON output from assistant, but may miss important context

**Issue**:
- May not capture all relevant data (stdout, stderr, crashes)
- Hard to diagnose test failures without complete picture
- Missing context when tests crash or behave unexpectedly

**Proposed change**:
- Capture everything during test execution:
  - All JSON outputs (assistant, judge, interrogator, user-proxy)
  - stdout and stderr from all subprocess calls
  - Full MCP logs (already doing this)
  - Crash dumps and stack traces
  - Timing data for all operations
  - Environment state (Python version, model versions, etc.)
  - Resource usage (memory, CPU at key points)
- Store all captured data indexed by test run
- Separate "essential" vs "diagnostic" data (for storage efficiency)

**Benefits**:
- Complete forensics for any test run
- Easier debugging of intermittent failures
- Can reconstruct exact test conditions
- Better understanding of system behavior under load

---

## Cross-Cutting Concerns

### 6.1 Configuration Management

**Current state**: Configuration scattered across CLI args, test case JSON, system prompts, overlays

**Issue**:
- Hard to understand full configuration for a test run
- Difficult to reproduce specific test conditions
- No versioning of configuration changes

**Proposed change**:
- Unified configuration file format (e.g., YAML)
- Override hierarchy: defaults → config file → CLI args
- Configuration profiles (e.g., "quick", "comprehensive", "ci")
- Store full resolved configuration with each test run

**Benefits**:
- Reproducible test runs
- Easier configuration management
- Clear documentation of test conditions

### 6.2 Test Dependencies and Sequencing

**Current state**: Tests are independent by design; some could benefit from shared state

**Issue**:
- Related tests (e.g., create → update → delete) repeat setup
- No way to express test dependencies
- Inefficient for testing workflows

**Proposed change**:
- Test sequence definitions (already proposed in 1.2)
- Explicit dependency declarations
- Shared fixtures within sequences
- Support for both isolated and sequential modes

**Benefits**:
- More efficient testing of workflows
- Better modeling of real user sessions
- Reduced test execution time

### 6.3 Performance Monitoring

**Current state**: Duration tracked but not systematically analyzed

**Proposed changes**:

1. **Performance baselines**:
   - Track expected duration for each test
   - Alert on unusually slow tests (>2x baseline)
   - Identify performance regressions

2. **Performance profiling**:
   - Break down time spent in setup, assistant, judge, interrogation
   - Identify bottlenecks (e.g., graph cleanup taking too long)
   - Optimize slowest operations

3. **Resource monitoring**:
   - Track memory usage, CPU usage
   - Detect resource leaks (memory not freed between tests)
   - Optimize resource utilization

**Benefits**:
- Faster test runs through targeted optimization
- Early detection of performance issues
- Better understanding of cost (API calls, time)

### 6.4 Test Maintenance Tools

**Current state**: Manual editing of test case JSON files

**Proposed changes**:

1. **Test case management CLI**:
   - Add/update/delete tests via CLI
   - Bulk operations (e.g., "update all Capture tests")
   - Validation on save (schema checking)

2. **Test case migration tools**:
   - Automated migration when schema changes
   - Version conversion (old format → new format)
   - Validation and reporting

3. **Test generation from examples**:
   - Record real user interactions → convert to tests
   - Generate edge cases automatically
   - Expand test coverage systematically

**Benefits**:
- Easier test maintenance
- Reduced errors from manual editing
- Faster test development

### 6.5 CI/CD Integration

**Current state**: No documented CI/CD integration

**Proposed changes**:

1. **CI/CD configuration examples**:
   - GitHub Actions workflow
   - GitLab CI configuration
   - Pre-commit hooks for quick tests

2. **Test selection strategies**:
   - Run fast smoke tests on every commit
   - Run full suite nightly or on release branches
   - Flaky test isolation (don't block CI on flaky tests)

3. **Result reporting**:
   - Post results to PR comments
   - Update status badges
   - Send notifications on failures

**Benefits**:
- Automated testing on every change
- Faster feedback for developers
- Prevents regressions from being merged

### 6.6 Versioning and History

**Current state**: No explicit versioning of test artifacts

**Issue**:
- Can't reproduce old test results (test cases change)
- Hard to understand why results changed over time
- No audit trail for test modifications

**Proposed change**:
- Version test cases (semantic versioning)
- Version system prompts and overlays
- Version expected results (baseline updates)
- Store version info with each test run
- Maintain changelog for test modifications

**Benefits**:
- Reproducible test runs (pin to specific versions)
- Clear history of test evolution
- Easier debugging (compare current vs old versions)

### 6.7 Model and Interface Swapping

**Current state**: Test roles (user-proxy, judge, interrogator) are hardcoded to use specific Claude models via `claude` CLI

**Issue**:
- Can't easily swap models for different roles
- Can't use non-Claude models (e.g., GPT-5 Codex, Gemini)
- Can't use different Claude interfaces (e.g., `codex` CLI)
- Hard to compare model performance across roles

**Proposed change**:
- Abstract model interface for each test role:
  - Assistant: already configurable (system under test)
  - User-proxy: configurable model/interface
  - Judge: configurable model/interface
  - Interrogator: configurable model/interface
- Support multiple interfaces:
  - `claude` CLI (current default)
  - `codex` CLI (Claude Code interface)
  - OpenAI API (GPT models)
  - Anthropic API (direct)
  - Other APIs (Gemini, etc.)
- Configuration examples:
  ```yaml
  test_roles:
    assistant:
      interface: claude
      model: claude-sonnet-4-5-20250929
    user_proxy:
      interface: claude
      model: claude-haiku-4-5-20251001
    judge:
      interface: codex  # Use Claude Code's codex CLI
      model: claude-sonnet-4-5-20250929
    interrogator:
      interface: openai
      model: gpt-5-preview
  ```

**Benefits**:
- Flexibility to use best model for each role
- Can compare different models as judges
- Can use specialized interfaces (e.g., codex for code-aware judging)
- Future-proof as new models/interfaces emerge
- Cost optimization (use cheaper models where appropriate)

---

## Documentation Gaps

### 7.1 Model Usage Documentation

**Status**: ✅ **COMPLETED** - See `docs/testing/prompts.md`

**What was documented**:
- **For each test role** (assistant, user-proxy, judge, interrogator):
  - Base system prompt (if any)
  - Appended system prompt content (full text)
  - User prompt template and variables
  - Model selection criteria
  - Temperature and other parameters
  - Complete CLI invocation examples
  - Code references for each component

**Created**: `docs/testing/prompts.md` (1,095 lines)

**Contents**:
1. Assistant (System Under Test) - base prompt, test overlays, configuration
2. User-Proxy - dynamic system prompt generation, user prompts, configuration
3. Judge - evaluation criteria, prompt template, configuration
4. Interrogator - failure vs success questions, session resumption
5. Complete conversational test flow example
6. Prompt evolution and versioning notes
7. Open questions and future work

**Benefits**:
- Complete transparency into what each model sees
- Easy debugging of unexpected model behavior
- Reproducible prompt configurations
- Foundation for systematic prompt iteration
- Addresses improvements.md proposals #4.3 (user-proxy enhancements) and #4.4 (interrogation enhancements)

### 7.2 Architecture Decision Records

**Current gap**: No documentation of why certain design decisions were made

**What needs documentation**:
- Why LLM user-proxy instead of only scripted responses?
- Why three-dimensional judge evaluation (effective/safe/clear)?
- Why interrogation vs just looking at logs?
- Why Claude CLI subprocess calls vs direct API?
- Why SQLite database vs other storage options?

**Proposed format**: ADR (Architecture Decision Record) template
```markdown
# ADR-001: LLM User-Proxy for Conversational Tests

**Status**: Accepted

**Context**:
Testing conversational scenarios requires simulating user responses...

**Decision**:
Use LLM (Claude Haiku) to generate user responses dynamically...

**Consequences**:
- Positive: More realistic, flexible, covers edge cases
- Negative: Non-deterministic, uses API calls, adds cost
- Mitigation: Cache common scenarios, use temperature control
```

**Where to document**: `docs/testing/architecture/` directory with numbered ADRs

**Benefits**:
- Preserve institutional knowledge
- Easier onboarding for new contributors
- Can revisit decisions with full context

---

## Navigation

← [Back to Index](INDEX.md) | [View Infrastructure →](infrastructure.md) | [View Prompts →](prompts.md)
