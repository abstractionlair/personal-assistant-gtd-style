# Testing Infrastructure Improvements

> **Part of**: [GTD Testing Documentation](INDEX.md) | **See also**: [Infrastructure](infrastructure.md) · [Prompts](prompts.md)

**Status**: Collecting ideas as we document
**Last Updated**: 2025-11-09

This document captures improvements, issues, and potential changes discovered while documenting the current testing infrastructure.

---

## Priority Improvements

These are the **critical architectural changes** requested by the project owner, organized by urgency and impact.

### P0: Critical Test Framework Changes

#### Delete Legacy Test Runner

**Status**: ✅ Completed
**Previous state**: Two parallel test runners (legacy monolithic + new modular)

**Actions completed**:
- ✅ Analyzed legacy runner for unique features (none found - all features present in new system)
- ✅ Deleted `tests/test_conversational_layer.py` (1,142 lines)
- ✅ Updated documentation to reference only new modular system
- ✅ Verified test framework still works

**Benefit**: Single source of truth, reduced maintenance burden

#### Eliminate Simulation Mode Completely

**Status**: ✅ Completed
**Previous state**: Tests supported `--mode sim` (no MCP), `--mode real` (live MCP), `--mode auto`

**Actions completed**:
- ✅ Removed all `--mode sim` support from CLI
- ✅ Deleted `tests/fixtures/system-prompt-no-mcp-overlay.md`
- ✅ Updated config.py to only accept "real" mode
- ✅ Updated fixtures.py to remove sim mode checks
- ✅ Updated documentation to remove sim-mode references

**Benefit**: Tests only validate real MCP operations; no risk of sim-mode artifacts

#### Consolidate to Refactored Test Cases Only

**Status**: ✅ Completed
**Previous state**: Two test case files existed

**Actions completed**:
- ✅ Deleted `tests/test_cases.json`
- ✅ Updated `tests/test_cases_refactored.json` as the default
- ✅ Removed CLI shorthand support for old test cases

**Benefit**: Single source of truth for test definitions

### P1: Architectural Enhancements

#### Robust N-Run Process

**Status**: Design needed
**Current state**: `--runs N` executes N times but no inter-run delay configuration

**Required changes**:
- Support running all tests N times (e.g., 5) **serially**
- Add configurable delay between runs (e.g., `--delay-between-runs 5` for 5 seconds)
- Purpose: Identify variance and flaky behavior
- Must capture all data from all runs for variance analysis

**Implementation**:
```bash
python tests/test_conversational_layer_new.py \
  --mode real \
  --runs 5 \
  --delay-between-runs 5 \
  --results-db variance_analysis.db
```

**Benefit**: Systematic detection of non-deterministic behavior

#### User-Proxy Drives Assistant Session

**Status**: Major architectural change
**Current state**: Python orchestration alternates between user-proxy and assistant

**Required changes**:
1. **User-proxy directly drives assistant session**:
   - User-proxy Claude Code session calls `claude --resume <assistant-session-id>` via Bash tool
   - Use `--append-system-prompt` for user-proxy role instructions
   - Base system prompt helpful for enabling Claude Code tool use
   - More realistic: simulates real user interacting with assistant

2. **Standardize on user-proxy (make non-optional)**:
   - All tests use conversational mode by default
   - Single-turn tests are just conversational tests that finish in one turn
   - Eliminates distinction between test modes

3. **Dynamic conversation length (not fixed max_turns)**:
   - User-proxy stops when satisfied task is accomplished
   - No artificial `max_turns` limit
   - User-proxy evaluates goal completion after each turn
   - Can say "Thanks!" or similar to signal completion

4. **Refine user-proxy system prompt**:
   - **Critical**: Must clearly state it is testing the **assistant's instructions**, not the proxy itself
   - Must clearly state goal: get the **assistant to complete the task**
   - Should mention target number of rounds: "ideally N or fewer"
   - Fix grammar/phrasing in "Success Criteria" section

**Example prompt addition**:
```markdown
Your role is to test the ASSISTANT by simulating a realistic user.
You are NOT being tested yourself - you're the tester.

Your goal: Get the assistant to complete the user's task correctly.

Ideally complete the interaction in 3 or fewer turns, but continue
as long as needed until the task is accomplished or you determine
the assistant cannot help.
```

**Benefit**: More realistic conversation testing, simpler Python orchestration

#### Judge with Direct MCP Server Access

**Status**: Phase 1 Complete ✅ | Phase 2 Ready
**Current state**: Judge has MCP access and verifies basic operations

**Implementation Plan**: 📋 [judge-mcp-access.md](plans/judge-mcp-access.md)

**Phase 1 Completed (2025-11-09)**:
- ✅ Updated judge system prompt with MCP access guidance
- ✅ Tested with capture, update, and delete operations
- ✅ Judge successfully verifies actual graph state vs. claims
- ✅ Example verdicts: "Verified via MCP tools that task was marked complete (isComplete: true)"

**Summary**:
- **Goal**: Judge queries MCP server to verify actual graph state (ground truth validation)
- **Approach**: Pass `--mcp-config` to judge's Claude CLI subprocess
- **Phases**: 3 phases over 2-4 weeks (basic access → enhanced prompts → optional test case enhancements)
- **Success metrics**: >80% MCP usage, catches real bugs, <10% false positives, <30% performance impact

**Key benefits**:
- Catches silent MCP failures (assistant claims action but tool call failed)
- Verifies actual outcomes, not just claims
- Enables removing hardcoded Python assertions
- More flexible and intelligent validation

**Next Step**: Phase 2 - Enhanced judge prompts with detailed validation patterns

**See plan for**: Design decisions, implementation details, edge cases, testing strategy, rollout timeline

#### Interrogator Drives Session and Sees Judge Verdict

**Status**: High-impact architectural change
**Current state**: Fixed question lists, doesn't see judge verdict

**Required changes**:
1. **Interrogator drives session (like user-proxy)**:
   - Interrogator Claude Code session drives assistant via `--resume`
   - Use `--append-system-prompt` for interrogator role instructions
   - Same pattern as user-proxy

2. **Interrogator sees judge verdict**:
   - Provide judge's evaluation (PASS/FAIL + reasoning) to interrogator
   - Ask specifically about areas judge identified as weak
   - More targeted questioning based on actual issues

3. **Dynamic interrogation (not fixed questions)**:
   - Interrogator has more leeway to ask follow-up questions
   - Can adapt questions based on assistant responses
   - Conversational interrogation rather than questionnaire

4. **Interrogate all tests (not just failures)**:
   - Run full interrogation on every test
   - Understand reasoning patterns in both success and failure

**Benefit**: More insightful interrogation, better understanding of AI decision-making

### P2: Data Capture and Reporting

#### Capture Everything

**Status**: Partially implemented, needs enhancement
**Current state**: Captures JSON output, may miss important context

**Required changes**:
- Capture **all** data during test execution:
  - All JSON outputs (assistant, judge, interrogator, user-proxy)
  - **stdout and stderr** from all subprocess calls
  - Full MCP logs (already doing this)
  - **Crash dumps and stack traces** (critical for debugging)
  - Timing data for all operations
  - Environment state (Python version, model versions, etc.)
- **Robust buffers**: Ensure we don't lose data in buffers if test process crashes
- Store all captured data indexed by test run
- Separate "essential" vs "diagnostic" data (for storage efficiency)

**Benefit**: Complete forensics for any test run, easier debugging of crashes

#### Markdown Test Report with Specific Format

**Status**: New feature needed
**Current state**: SQLite database, console output only

**Required format**:
1. **Create single Markdown report** after test run
2. **Group tests by category** (Capture, Query, Update, Delete, etc.)
3. **Statistics at each level**:
   - Overall summary at top
   - Per-category statistics
   - Per-test statistics (across runs)
4. **For each test run**, provide **unified view** in this order:
   a. Initial **Prompt** (what user asked for)
   b. **Transcript** (complete conversation, formatted JSON with MCP calls)
   c. **Judge's Response/Verdict** (PASS/FAIL + reasoning)
   d. **Interrogation** (Q&A)
5. **Formatted JSON transcripts**:
   - Must be **human-readable** (pretty-printed)
   - Not compact/minified
   - Include MCP calls inline in conversation flow

**Example structure**:
```markdown
# Test Run Report: 2025-11-09

## Overall Statistics
- Total tests: 18
- Total runs: 90 (5 runs each)
- Pass rate: 87.8%
- Flaky tests: 2

## Category: Capture (4 tests, 20 runs)
Pass rate: 95%

### Test: capture_simple (5 runs)
Pass: 5/5 (100%)

#### Run 1: PASS
**Prompt:**
"Schedule dentist appointment"

**Transcript:**
```json
{
  "turn": 1,
  "user": "Schedule dentist appointment",
  "assistant": "I'll help you capture that task...",
  "mcp_calls": [
    {
      "tool": "create_node",
      "input": {"type": "Task", "content": "Schedule dentist appointment"},
      "result": {"node_id": "mem_xyz123"}
    }
  ]
}
```

**Judge Verdict:** PASS
Reasoning: Task successfully created with appropriate content...

**Interrogation:**
Q: Why did you choose create_node instead of searching first?
A: Since this was a new task capture...
```

**Benefit**: Easy human review, grouped by test/category, complete context for each run

### P3: Model and Interface Flexibility

#### Model/Interface Swapping for All Roles

**Status**: Needs implementation
**Current state**: Hardcoded to Claude models via `claude` CLI

**Required changes**:
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

**Configuration example**:
```yaml
test_roles:
  assistant:
    interface: claude
    model: claude-sonnet-4-5-20250929
  user_proxy:
    interface: claude
    model: claude-haiku-4-5-20251001
  judge:
    interface: codex  # Claude Code's codex CLI
    model: claude-sonnet-4-5-20250929
  interrogator:
    interface: openai
    model: gpt-5-preview
```

**Benefit**: Flexibility, comparison across models, cost optimization

---

## Additional Good Ideas

These are valuable improvements that complement the priority changes above.

### Layer 1: Test Execution

#### Flexible Test Lifecycle Configuration

**Current state**: Binary flag `--clean-graph-between-tests` applies cleanup uniformly

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
    }
  ]
}
```

**Benefits**:
- Tests can intentionally share state for sequential workflows
- Explicit control over cleanup timing
- Better performance (less unnecessary cleanup)

**Note**: This may be over-engineering. Evaluate after P0-P2 complete.

---

### Layer 2: Inputs

#### JSON Schema Validation

**Current state**: No validation of test case structure

**Proposed change**:
- Define JSON Schema for test cases
- Validate on load (fail fast if malformed)
- Schema versioning for backwards compatibility
- Helpful error messages for validation failures

**Benefits**:
- Catch test definition errors early
- Self-documenting test case format
- Easier test case authoring

**Example**:
```python
import jsonschema

test_schema = {
    "type": "object",
    "required": ["test_name", "category", "user_inputs"],
    "properties": {
        "test_name": {"type": "string"},
        "category": {"type": "string", "enum": ["Capture", "Query", "Update", ...]},
        "user_inputs": {"type": "array", "items": {"type": "string"}},
        ...
    }
}

jsonschema.validate(test_case, test_schema)
```

#### Shared Fixtures Library

**Current state**: Fixtures defined per test or globally

**Proposed change**:
- Reusable fixture library (e.g., `fixtures/library/`)
- Common patterns: "basic_tasks", "complex_project", "multiple_contexts"
- Composable fixtures (combine multiple)
- Fixture versioning

**Benefits**:
- Reduce duplication
- Consistent test setup
- Easier fixture maintenance

---

### Layer 3: Setup and Initialization

#### Direct Storage Deletion for Graph Cleanup

**Current state**: Graph cleanup uses Claude CLI with specialized cleanup prompt

**Issue**:
- Slower than direct filesystem operations
- Can timeout or fail if model makes mistakes
- Uses model for task that doesn't require intelligence

**Proposed change**:
- Delete storage directory and recreate fresh
- Options:
  1. `rm -rf .data/gtd-memory/test/* && mkdir -p .data/gtd-memory/test/`
  2. Python: `shutil.rmtree()` and recreate
  3. Direct graph API: `graph.delete_all_nodes()` method

**Benefits**:
- Much faster (milliseconds vs seconds)
- Guaranteed clean state
- No timeout or model failure modes

#### Programmatic Fixture Setup

**Current state**: Fixtures set up via Claude CLI with natural language

**Issue**:
- Model-based setup can fail or be inconsistent
- Slower than direct approach
- Setup is deterministic - doesn't need model intelligence

**Proposed change**:
- Use direct programmatic MCP client to create fixtures
- Example:
  ```python
  def setup_fixture(fixture: dict, mcp_client):
      for task in fixture.get("tasks", []):
          node_id = mcp_client.create_node(
              type="Task",
              content=task["content"],
              properties={"isComplete": task["isComplete"]}
          )
  ```

**Benefits**:
- Faster and more reliable
- Deterministic setup
- Easier to debug

---

### Layer 4: Execution Flow

#### Parallel Test Execution

**Current state**: Tests execute sequentially

**Proposed change**:
- Run independent tests in parallel (configurable parallelism)
- `--parallel N` flag to run N tests concurrently

**Benefits**:
- Faster test runs (could reduce 30 min → 5-10 min)
- Better resource utilization

**Considerations**:
- Need separate MCP server instances per test
- May complicate output formatting

**Note**: Evaluate need after measuring actual test suite duration

#### Better Error Recovery

**Proposed changes**:
1. **Transient error retry**:
   - Distinguish transient (network, timeout) from persistent errors
   - Automatic retry with exponential backoff
   - Report retry counts in results

2. **Graceful degradation**:
   - Continue test run even if some tests crash
   - Isolate failures (one crash doesn't kill suite)
   - Capture crash dumps for debugging

3. **Error categorization**:
   - Tag errors by type (MCP, judge, timeout, parsing)
   - Aggregate error patterns across runs

**Benefits**:
- More reliable test runs
- Better visibility into error patterns

---

### Layer 5: Outputs and Results

#### Unified Output Format

**Current state**: Multiple output formats (console, SQLite, JSON) with overlapping data

**Proposed change**:
- Define canonical output schema (e.g., JSON Schema)
- Generate all output formats from canonical representation
- Schema versioning for backwards compatibility

**Benefits**:
- Single source of truth
- Guaranteed consistency across outputs

#### Real-Time Test Dashboard

**Proposed change**:
- Web-based dashboard reading SQLite in real-time
- Features:
  - Live test progress
  - Pass/fail counts updating
  - Recent failures highlighted
  - Historical trends
  - Flakiness detection

**Implementation options**:
1. Simple Flask/FastAPI app reading SQLite
2. Static HTML + JavaScript polling
3. WebSocket-based live updates

**Benefits**:
- Better visibility during long runs
- Quick problem identification

**Note**: Nice to have, not urgent

#### MCP Log Analysis Tools

**Proposed changes**:
1. **Log aggregation and querying**:
   - Import all MCP logs into test results database
   - Query interface for finding patterns
   - Time-series analysis of tool usage

2. **Automated verification**:
   - Check MCP logs against expected tool call sequences
   - Validate claimed operations match actual logs

3. **Visualization**:
   - Timeline view of tool calls
   - Dependency graphs
   - Operation frequency heatmaps

**Benefits**:
- Deeper insights into assistant behavior
- Ground truth verification
- Pattern discovery

#### Test Result Visualization

**Proposed changes**:
1. **Charts and graphs**:
   - Pass rate trends over time
   - Per-category performance breakdown
   - Flakiness visualization
   - Test duration distributions

2. **Comparative analysis**:
   - Compare results across different runs
   - Compare different models (Sonnet vs Opus)
   - A/B testing support

3. **Regression detection**:
   - Highlight tests that recently started failing
   - Alert on degraded pass rates

**Benefits**:
- Easier to understand results at a glance
- Make data-driven decisions

#### Interrogation Analysis

**Proposed changes**:
1. **Reasoning pattern extraction**:
   - NLP analysis of interrogation responses
   - Cluster common reasoning patterns
   - Identify knowledge gaps

2. **Success vs failure comparison**:
   - Side-by-side comparison of reasoning
   - Identify what distinguishes successful approaches

3. **Automated insight generation**:
   - Summarize common failure modes
   - Suggest system prompt improvements

**Benefits**:
- Turn interrogation data into actionable insights
- Improve system prompts based on evidence

---

### Cross-Cutting Concerns

#### Configuration Management

**Current state**: Configuration scattered across CLI args, JSON, prompts

**Proposed change**:
- Unified configuration file format (YAML)
- Override hierarchy: defaults → config file → CLI args
- Configuration profiles ("quick", "comprehensive", "ci")
- Store full resolved configuration with each test run

**Benefits**:
- Reproducible test runs
- Clear documentation of test conditions

#### Performance Monitoring

**Proposed changes**:
1. **Performance baselines**:
   - Track expected duration for each test
   - Alert on unusually slow tests (>2x baseline)

2. **Performance profiling**:
   - Break down time spent in setup, assistant, judge, interrogation
   - Identify bottlenecks

3. **Resource monitoring**:
   - Track memory/CPU usage
   - Detect resource leaks

**Benefits**:
- Faster test runs through targeted optimization
- Early detection of performance issues

#### Test Maintenance Tools

**Proposed changes**:
1. **Test case management CLI**:
   - Add/update/delete tests via CLI
   - Bulk operations
   - Validation on save

2. **Test generation from examples**:
   - Record real user interactions → convert to tests
   - Generate edge cases automatically

**Benefits**:
- Easier test maintenance
- Faster test development

#### CI/CD Integration

**Proposed changes**:
1. **CI/CD configuration examples**:
   - GitHub Actions workflow
   - Pre-commit hooks for quick tests

2. **Test selection strategies**:
   - Run fast smoke tests on every commit
   - Run full suite nightly

3. **Result reporting**:
   - Post results to PR comments
   - Update status badges

**Benefits**:
- Automated testing on every change
- Prevents regressions from being merged

#### Versioning and History

**Proposed change**:
- Version test cases (semantic versioning)
- Version system prompts and overlays
- Store version info with each test run
- Maintain changelog for test modifications

**Benefits**:
- Reproducible test runs
- Clear history of test evolution

---

## Documentation Gaps

### Model Usage Documentation

**Status**: ✅ **COMPLETED** - See `docs/testing/prompts.md`

**What was documented**:
- For each test role (assistant, user-proxy, judge, interrogator):
  - Base system prompt (if any)
  - Appended system prompt content
  - User prompt template and variables
  - Model selection criteria
  - Complete CLI invocation examples

**Created**: `docs/testing/prompts.md` (629 lines)

### Architecture Decision Records

**Current gap**: No documentation of why certain design decisions were made

**What needs documentation**:
- Why LLM user-proxy instead of scripted responses?
- Why three-dimensional judge evaluation?
- Why interrogation vs just logs?
- Why Claude CLI subprocess vs direct API?
- Why SQLite vs other storage?

**Proposed format**: ADR (Architecture Decision Record)

**Where to document**: `docs/testing/architecture/` directory

**Benefits**:
- Preserve institutional knowledge
- Easier onboarding
- Can revisit decisions with full context

---

## Navigation

← [Back to Index](INDEX.md) | [View Infrastructure →](infrastructure.md) | [View Prompts →](prompts.md)
