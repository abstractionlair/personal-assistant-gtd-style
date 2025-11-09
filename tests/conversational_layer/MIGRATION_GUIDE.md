# Migration Guide: Test Framework v1.0 → v2.0

This guide helps you migrate from the monolithic `test_conversational_layer.py` to the new modular framework in `tests/conversational_layer/`.

## Quick Reference

| **Feature** | **v1.0** | **v2.0** |
|------------|----------|----------|
| Entry point | `test_conversational_layer.py` | `test_conversational_layer_new.py` |
| Architecture | Monolithic (1053 lines) | Modular (10 files) |
| Retry logic | Manual | Automatic exponential backoff |
| Results | JSON files | SQLite database |
| Multi-turn | Not supported | Full support via user-proxy |
| Judge | Binary pass/fail | Three dimensions (EFFECTIVE/SAFE/CLEAR) |
| Graph cleanup | Manual deletion | Automated with --clean-graph-between-tests |

## Breaking Changes

### 1. Command-Line Interface

#### Test Selection

**v1.0:**
```bash
python tests/test_conversational_layer.py \
  --test-cases test_cases.json \
  --filter-category Edge
```

**v2.0:**
```bash
python tests/test_conversational_layer_new.py \
  --test-cases test_cases_refactored.json \
  --category Edge
```

**Changes:**
- `--filter-category` → `--category`
- `--test-cases` accepts "refactored" shortcut for `test_cases_refactored.json`

#### Interrogation

**v1.0:**
```bash
python tests/test_conversational_layer.py \
  --interrogate-on-fail \
  --save-interrogation interrogation.json
```

**v2.0:**
```bash
python tests/test_conversational_layer_new.py \
  --interrogate-failures \
  --interrogation-log interrogation.json
```

**Changes:**
- `--interrogate-on-fail` → `--interrogate-failures`
- `--save-interrogation` → `--interrogation-log`
- New: `--interrogate-passes` for surveying successes

### 2. Test Case Format

#### Judge Scenario Field

**v1.0:**
```json
{
  "name": "test_name",
  "expected_behavior": "What should happen"
}
```

**v2.0:**
```json
{
  "name": "test_name",
  "expected_behavior": "What should happen",
  "judge_scenario": "Context for judge evaluation"
}
```

**Migration:** Add `judge_scenario` field to all test cases. This helps the judge understand the test context.

#### Graph Setup Format

**v1.0:** (Custom implementation required)

**v2.0:** (Built-in support)
```json
{
  "graph_setup": {
    "tasks": [
      {"content": "Task description", "isComplete": false}
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

**Migration:** Replace custom graph setup code with declarative `graph_setup` field.

#### Conversational Tests (NEW)

**v1.0:** Not supported

**v2.0:**
```json
{
  "conversational": {
    "enabled": true,
    "max_turns": 2,
    "user_responses": ["User's scripted response"],
    "validate_mcp_before_ask": true,
    "require_search_first": true
  }
}
```

**Migration:** Add conversational config to edge cases where asking clarifying questions is expected behavior.

### 3. Judge Verdict Format

#### Old Format (v1.0)

```json
{
  "pass": true,
  "reasoning": "Explanation"
}
```

#### New Format (v2.0)

```json
{
  "effective": true,
  "safe": true,
  "clear": true,
  "reasoning": "Explanation"
}
```

**Migration:**
- Judge code automatically handles both formats
- Update any custom judge prompt overrides to use three dimensions
- Passes if **all three** dimensions are true

### 4. Results Storage

#### Old Format (JSON Files)

**v1.0:**
```bash
# Results saved to manual JSON files
run1_output.json
run1_interrogation.json
```

**v2.0:**
```bash
# Results in SQLite database
test_results.db
```

**Migration:**
1. Old JSON files are preserved but not used
2. New runs automatically write to database
3. Export old runs to new format:

```python
# Migration script (example)
import json
from pathlib import Path
from conversational_layer.results_db import ResultsDB

db = ResultsDB(Path("test_results.db"))

# Load old JSON result
with open("run1_output.json") as f:
    old_data = json.load(f)

# Convert and save to database
# (Custom migration code based on your old format)
```

## Step-by-Step Migration

### Step 1: Update Test Cases

1. Copy `test_cases.json` to `test_cases_refactored.json`
2. Add `judge_scenario` field to each test case
3. Convert custom graph setup to `graph_setup` field
4. Add `conversational` config to edge cases:
   - `edge_ambiguous_reference`
   - `edge_conflicting_update`
   - `edge_ask_vs_infer`
   - `edge_undefined_context`
   - `capture_duplicate_detection`

**Example:**

```diff
{
  "name": "edge_ambiguous_reference",
  "category": "Edge",
  "prompt": "Mark the proposal done.",
- "expected_behavior": "Asks which proposal, makes no changes"
+ "expected_behavior": "Searches graph, finds 3 proposals, asks which one, marks specified one complete",
+ "judge_scenario": "User refers ambiguously - assistant should search then ask",
+ "graph_setup": {
+   "tasks": [
+     {"content": "Write Q4 budget proposal", "isComplete": false},
+     {"content": "Review marketing proposal", "isComplete": false},
+     {"content": "Submit project proposal", "isComplete": false}
+   ]
+ },
+ "conversational": {
+   "enabled": true,
+   "max_turns": 2,
+   "user_responses": ["The marketing proposal"],
+   "validate_mcp_before_ask": true,
+   "require_search_first": true
+ }
}
```

### Step 2: Update Scripts

Replace:
```bash
python tests/test_conversational_layer.py --mode sim --filter-category Edge
```

With:
```bash
python tests/test_conversational_layer_new.py --mode sim --category Edge
```

### Step 3: Update Environment

No changes needed. Environment variables remain compatible:
- `MCP_CONFIG_PATH`
- `CLAUDE_TIMEOUT_ASSISTANT`
- `CLAUDE_TIMEOUT_JUDGE`
- `PRINT_ASSISTANT_ON_FAIL`

### Step 4: Validate Migration

Run side-by-side comparison:

```bash
# Old framework
python tests/test_conversational_layer.py --mode sim --category Capture

# New framework
python tests/test_conversational_layer_new.py --mode sim --category Capture
```

Compare results manually for first few runs.

### Step 5: Archive Old Code

Once validated:

```bash
# Keep old code for reference
mv tests/test_conversational_layer.py tests/test_conversational_layer_v1_archived.py

# Rename new code to primary
mv tests/test_conversational_layer_new.py tests/test_conversational_layer.py
```

## Feature Mapping

### Retry Logic

**v1.0:** Manual retry required
```bash
# Had to manually retry on rate limits
python tests/test_conversational_layer.py ...
# Wait, then retry
python tests/test_conversational_layer.py ...
```

**v2.0:** Automatic exponential backoff
```bash
# Automatically retries with 30s → 60s → 120s backoff
python tests/test_conversational_layer_new.py --max-retries 3 --initial-backoff 30
```

### N-Run Execution

**v1.0:** Run script multiple times manually
```bash
for i in {1..5}; do
  python tests/test_conversational_layer.py --mode sim
  sleep 10
done
```

**v2.0:** Built-in N-run support
```bash
python tests/test_conversational_layer_new.py --mode sim --runs 5 --inter-run-delay 10
```

### Graph Cleanup

**v1.0:** Manual cleanup between runs
```bash
# Custom script to delete all nodes
python cleanup_graph.py
python tests/test_conversational_layer.py --mode real
```

**v2.0:** Automated cleanup
```bash
python tests/test_conversational_layer_new.py --mode real --clean-graph-between-tests
```

### Interrogation

**v1.0:** Limited to failures, basic questions

**v2.0:**
- Separate questions for passes vs failures
- Uncertainty extraction
- Success surveys for instruction quality
- Full transcript saved to database

```bash
# Interrogate both passes and failures
python tests/test_conversational_layer_new.py \
  --mode sim \
  --interrogate-all \
  --interrogation-log detailed_feedback.json
```

### Results Analysis

**v1.0:** Manual JSON parsing
```python
import json
with open("run1_output.json") as f:
    data = json.load(f)
# Manual analysis
```

**v2.0:** Built-in queries
```bash
# Find flaky tests
python tests/test_conversational_layer_new.py --query flaky

# Category statistics
python tests/test_conversational_layer_new.py --query category --run-id 42

# Export to JSON
python tests/test_conversational_layer_new.py --query export --run-id 42 --export-json run_42.json
```

## Common Migration Issues

### Issue 1: Missing judge_scenario

**Error:**
```
KeyError: 'judge_scenario'
```

**Fix:**
Add `judge_scenario` field to test case:
```json
{
  "judge_scenario": "Description of what test validates"
}
```

### Issue 2: Graph setup not working

**Symptom:** Tests expect pre-populated graph but it's empty

**Fix:**
1. Ensure `--mode real` is used (graph setup requires Live MCP)
2. Add `graph_setup` field to test case
3. Verify MCP server is running

### Issue 3: Conversational tests failing

**Symptom:** Edge cases failing with "assistant didn't ask"

**Fix:**
Add conversational config:
```json
{
  "conversational": {
    "enabled": true,
    "max_turns": 2,
    "user_responses": ["User's response to clarifying question"]
  }
}
```

### Issue 4: Database file conflicts

**Symptom:** Multiple test runs overwriting results

**Fix:**
Use different database files:
```bash
python tests/test_conversational_layer_new.py \
  --results-db test_run_experiment_1.db
```

## Rollback Plan

If migration issues occur:

1. **Keep old code:** Don't delete `test_conversational_layer.py`
2. **Revert test cases:** Restore from version control
3. **Use old framework temporarily:**
   ```bash
   python tests/test_conversational_layer.py --mode sim
   ```
4. **Report issues:** Document problems encountered
5. **Gradual migration:** Migrate one category at a time

## Benefits After Migration

✅ **Reliability:** Automatic retry with exponential backoff
✅ **Maintainability:** Modular code, easy to extend
✅ **Functionality:** Multi-turn conversations, graph fixtures
✅ **Analysis:** SQLite database, flaky test detection
✅ **Debugging:** Structured logging, interrogation transcripts
✅ **Judge Quality:** Three-dimension evaluation, edge case handling

## Support

If you encounter migration issues:

1. Check this guide
2. Review [README.md](./README.md) for new features
3. Examine example test cases in `test_cases_refactored.json`
4. Run with `--log-level DEBUG` for detailed logging
5. Consult test-writer documentation

## Timeline Recommendation

- **Week 1:** Update test cases, run side-by-side
- **Week 2:** Validate results match, fix edge cases
- **Week 3:** Full migration, archive old code
- **Week 4:** Utilize new features (conversational, database queries)
