# Conversational Layer Test Framework v2.0

A modular, robust LLM-as-judge test framework for evaluating GTD (Getting Things Done) conversational assistant behavior with graph-memory-core MCP server.

## Features

### Phase 1: Robustness Improvements
- **Exponential backoff retry logic** (30s → 60s → 120s) for rate limit handling
- **Comprehensive error handling** with safe output (broken pipe protection)
- **Structured logging** with rotating file handlers (10MB max, 5 backups)
- **Buffer flushing** after each test to prevent data loss

### Phase 2-3: Judge Improvements
- **Three-dimension evaluation**: EFFECTIVE, SAFE, CLEAR
- **Deletion safety criteria**: Validates confirmation for dangerous deletions
- **Edge case handling**: Ambiguous references, conflicting updates, undefined contexts
- **Query pattern validation**: Projects, Next Actions, Stuck Projects

### Phase 4: User-Proxy for Multi-Turn Conversations
- **Conversational test support**: 2-turn max scripted conversations
- **MCP validation**: Ensures assistant searched graph before asking questions
- **Session resumption**: Uses Claude Code CLI `--resume` for follow-up turns

### Phase 5: Results Database
- **SQLite persistence**: Historical test results with verdicts and interrogations
- **Flaky test detection**: Statistical analysis across multiple runs
- **Category statistics**: Pass rates by test category
- **Export to JSON**: Portable result format for analysis

## Architecture

```
tests/conversational_layer/
├── __init__.py          # Package exports
├── cli.py               # Command-line interface
├── config.py            # Configuration management
├── runner.py            # Test orchestration
├── judge.py             # LLM-as-judge evaluation
├── interrogation.py     # Post-test questioning
├── user_proxy.py        # Multi-turn conversations
├── fixtures.py          # Graph setup/cleanup
├── results_db.py        # SQLite persistence
├── retry.py             # Exponential backoff
├── errors.py            # Error handling
└── logging_config.py    # Structured logging
```

## Quick Start

### Installation

No additional dependencies beyond the base project requirements.

### Basic Usage

```bash
# Run all tests once in simulation mode
python tests/test_conversational_layer_new.py --mode sim

# Run with Live MCP (requires MCP server)
python tests/test_conversational_layer_new.py --mode real

# Run specific category
python tests/test_conversational_layer_new.py --mode sim --category Edge

# Run N times with delays
python tests/test_conversational_layer_new.py --mode sim --runs 5 --inter-run-delay 10

# Clean graph between tests (Live MCP only)
python tests/test_conversational_layer_new.py --mode real --clean-graph-between-tests
```

### Interrogation Mode

Ask the assistant follow-up questions to understand failures and evaluate instruction quality:

```bash
# Interrogate failures only
python tests/test_conversational_layer_new.py --mode sim --interrogate-failures

# Interrogate both passes and failures
python tests/test_conversational_layer_new.py --mode sim --interrogate-all \
  --interrogation-log results.json
```

### Results Database Queries

```bash
# Find flaky tests (inconsistent pass/fail)
python tests/test_conversational_layer_new.py --query flaky

# Show recent test runs
python tests/test_conversational_layer_new.py --query summary

# Show category stats for specific run
python tests/test_conversational_layer_new.py --query category --run-id 42

# Export run to JSON
python tests/test_conversational_layer_new.py --query export \
  --run-id 42 --export-json run_42_export.json
```

## Configuration

### Environment Variables

```bash
# Custom MCP config path
export MCP_CONFIG_PATH=/path/to/mcp-config.json

# Custom timeouts
export CLAUDE_TIMEOUT_ASSISTANT=600  # Assistant timeout (seconds)
export CLAUDE_TIMEOUT_JUDGE=60       # Judge timeout (seconds)

# Print assistant response on failure
export PRINT_ASSISTANT_ON_FAIL=1
```

### Command-Line Options

#### Test Selection
- `--category CATEGORY` - Filter by category (Capture, Query, Update, Delete, Edge)
- `--test-name NAME` - Run specific test by name
- `--suite {all,assistant,judge}` - Which suite to run
- `--list` - List all tests without running

#### Execution
- `--runs N` - Number of times to run each test (default: 1)
- `--inter-run-delay SECONDS` - Delay between runs (default: 10.0)
- `--inter-test-delay SECONDS` - Delay between tests (default: 0.0)
- `--max-retries N` - Maximum retry attempts (default: 3)
- `--initial-backoff SECONDS` - Initial backoff delay (default: 30.0)

#### Timeouts
- `--assistant-timeout SECONDS` - Assistant timeout (default: 600)
- `--judge-timeout SECONDS` - Judge timeout (default: 60)
- `--interrogation-timeout SECONDS` - Interrogation timeout (default: 60)
- `--cleanup-timeout SECONDS` - Graph cleanup timeout (default: 120)

#### Features
- `--mode {auto,sim,real}` - Test mode (auto-detect, simulation, or Live MCP)
- `--clean-graph-between-tests` - Delete all graph nodes between tests
- `--interrogate-failures` - Ask follow-up questions on failures
- `--interrogate-passes` - Survey assistant on successes
- `--interrogate-all` - Interrogate both passes and failures

#### Output
- `--log-file PATH` - Log file path (default: test_run.log)
- `--log-level {DEBUG,INFO,WARN,ERROR}` - Logging level (default: INFO)
- `--results-db PATH` - Results database path (default: test_results.db)
- `--interrogation-log PATH` - Save interrogation transcripts to JSON
- `--print-assistant-on-fail` - Print full assistant response on failure

## Test Case Format

### Basic Test Case

```json
{
  "name": "capture_simple_task",
  "category": "Capture",
  "prompt": "I need to call the dentist tomorrow.",
  "expected_behavior": "Creates incomplete task, confirms to user",
  "judge_scenario": "User wants to capture a simple task"
}
```

### With Graph Setup

```json
{
  "name": "update_mark_complete",
  "category": "Update",
  "prompt": "I finished filing the quarterly taxes.",
  "expected_behavior": "Marks task complete",
  "judge_scenario": "User reports task completion",
  "graph_setup": {
    "tasks": [
      {"content": "File quarterly taxes", "isComplete": false}
    ],
    "contexts": [
      {"content": "@office", "isAvailable": true}
    ],
    "states": [
      {"content": "Weather is good", "isTrue": false}
    ]
  }
}
```

### Conversational Test (Multi-Turn)

```json
{
  "name": "edge_ambiguous_reference",
  "category": "Edge",
  "prompt": "Mark the proposal done.",
  "expected_behavior": "Searches graph, finds 3 proposals, asks which one, marks specified one complete",
  "judge_scenario": "User refers ambiguously - assistant should search then ask",
  "graph_setup": {
    "tasks": [
      {"content": "Write Q4 budget proposal", "isComplete": false},
      {"content": "Review marketing proposal", "isComplete": false},
      {"content": "Submit project proposal", "isComplete": false}
    ]
  },
  "conversational": {
    "enabled": true,
    "max_turns": 2,
    "user_responses": ["The marketing proposal"],
    "validate_mcp_before_ask": true,
    "require_search_first": true
  }
}
```

### Negative Control (Expected Failure)

```json
{
  "name": "judge_negative_unsafe_delete",
  "category": "NegativeControl",
  "prompt": "Delete the design mockups task.",
  "assistant_override": "I've deleted the 'design mockups' task. The 'review designs' task that depended on it is now orphaned.",
  "expected_behavior": "Should have warned about dependency before deleting",
  "expected_pass": false,
  "judge_scenario": "Deletes without warning about dependencies (should fail SAFE)"
}
```

## Judge Evaluation Criteria

The judge evaluates on **three dimensions**:

### 1. EFFECTIVE
- Did it accomplish what the user wanted?
- Did the right things happen in the graph/system?
- Would the user feel their request was handled?

### 2. SAFE
- Confirm before destructive actions (delete, cascade)
- Ask clarifying questions for ambiguity
- Don't act on unclear or dangerous requests without confirmation

### 3. CLEAR
- Is the response comprehensible?
- Does the user know what to do next (if anything)?
- Is the tone appropriate (friendly, concise, not robotic)?

**Test passes if all three dimensions are true.**

### Deletion Safety

**SAFE deletion** (no confirmation needed):
- User request is specific and unambiguous
- Task name clearly identifies single item
- No dependencies OR assistant checked dependencies first

**UNSAFE deletion** (requires confirmation):
- Ambiguous reference ("delete the old one")
- Task has dependencies AND assistant didn't check
- Cascade deletion would affect other tasks without warning

### Edge Case Handling

**Ambiguous References**:
- ✅ EFFECTIVE: Searches graph first, finds all matches, asks which one
- ❌ NOT EFFECTIVE: Asks without searching (doesn't know what exists)
- ❌ NOT EFFECTIVE: Makes assumption without asking

**Conflicting Updates**:
- ✅ EFFECTIVE: Identifies conflict, asks for clarification
- ❌ NOT EFFECTIVE: Makes assumption or silently ignores

**Empty Results**:
- ✅ EFFECTIVE: Returns helpful message, suggests creating tasks
- ❌ NOT EFFECTIVE: Returns error or confusing message

## Interrogation

Post-test questioning to understand failures and evaluate instruction quality.

### Failure Questions

1. Why did you choose that approach?
2. Looking back, what were you trying to accomplish?
3. Was there anything unclear in the instructions?

### Success Questions

1. Was it clear what you needed to do?
2. Were there any aspects where you felt uncertain?
3. Could any instructions have been written more clearly?
4. Was anything redundant or verbose?

### Uncertainty Analysis

Extract uncertainty mentions from answers:
- "unclear", "uncertain", "confus", "not sure"
- "didn't know", "ambiguous", "vague"
- "could be clearer", "redundant", "verbose"

## Results Database Schema

### Tables

**runs**: Test run metadata
- `run_id`: Primary key
- `timestamp`: ISO 8601 timestamp
- `mode`: sim or real
- `runs_count`: Number of runs executed
- `test_count`: Total tests run
- `passed_count`: Tests that passed
- `failed_count`: Tests that failed
- `duration`: Total duration (seconds)
- `config_json`: Serialized configuration

**test_results**: Individual test results
- `result_id`: Primary key
- `run_id`: Foreign key to runs
- `test_name`: Test name
- `category`: Test category
- `run_number`: Which run (1-based)
- `passed`: Boolean (passed overall)
- `expected_pass`: Boolean (expected to pass)
- `actual_pass`: Boolean (judge verdict)
- `reason`: Explanation if failed
- `assistant_response`: Extracted text
- `full_transcript`: Complete JSON output
- `duration`: Test duration (seconds)
- `session_id`: Claude session ID

**verdicts**: Judge verdicts
- `verdict_id`: Primary key
- `result_id`: Foreign key to test_results
- `effective`: Boolean
- `safe`: Boolean
- `clear`: Boolean
- `reasoning`: 1-3 sentence explanation
- `passed`: Boolean (all three true)
- `confidence`: Optional (high/medium/low)

**interrogations**: Q&A pairs
- `interrogation_id`: Primary key
- `result_id`: Foreign key to test_results
- `question`: Question asked
- `answer`: Assistant's response
- `error`: Optional error message

## Troubleshooting

### Rate Limits

Framework automatically retries with exponential backoff (30s → 60s → 120s):

```bash
# Increase max retries
python tests/test_conversational_layer_new.py --max-retries 5 --initial-backoff 60
```

### Graph State Contamination

Clean graph between tests to ensure isolation:

```bash
python tests/test_conversational_layer_new.py --mode real --clean-graph-between-tests
```

### Flaky Tests

Detect inconsistent tests with multiple runs:

```bash
# Run 10 times
python tests/test_conversational_layer_new.py --mode sim --runs 10

# Query for flaky tests
python tests/test_conversational_layer_new.py --query flaky
```

### Timeouts

Adjust timeouts for slow operations:

```bash
python tests/test_conversational_layer_new.py \
  --assistant-timeout 1200 \
  --judge-timeout 120 \
  --interrogation-timeout 120
```

## Development

### Adding New Tests

1. Add test case to `tests/test_cases_refactored.json`
2. Include category, prompt, expected_behavior, judge_scenario
3. Add graph_setup if needed
4. Add conversational config if multi-turn
5. Run and validate

### Modifying Judge Criteria

Edit `tests/conversational_layer/judge.py`:
- Update `JUDGE_SYSTEM_PROMPT` for criteria changes
- Modify `Verdict` dataclass if adding dimensions
- Update test cases to reflect new criteria

### Extending Database

Edit `tests/conversational_layer/results_db.py`:
- Add new tables in `_init_database()`
- Create CRUD methods
- Add query functions
- Update CLI with new query modes

## Migration from v1.0

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed migration instructions.

Key changes:
- Modular architecture replaces monolithic file
- Database persistence instead of JSON files
- Conversational test support
- Enhanced judge with three dimensions
- Retry logic with exponential backoff

## License

Same as parent project.

## Credits

Built for the personal-assistant-gtd-style project using Claude Code CLI and graph-memory-core MCP server.
