# Graph Cleanup Between Tests

## Overview

The test harness now supports **automatic graph cleanup between tests** to ensure test isolation in Live MCP mode. This solves the problem where tests running in sequence can interfere with each other due to shared graph state.

## The Problem

### Before Cleanup Feature

When tests run against Live MCP:

```
Test 1: Create task "Call dentist"
  → Creates nodes in graph
  → Test passes ✅

Test 2: Create task "Schedule meeting"
  → Graph already contains "Call dentist" from Test 1
  → Test 2 might find Test 1's data and behave differently
  → Stochastic pass/fail behavior ❌
```

**Result**: Tests have **variable outcomes** depending on:
- What previous tests created
- Test execution order
- Stochastic search/deduplication decisions

### Symptoms of This Problem

- Test passes when run in isolation: `--case test_name` ✅
- Same test fails or behaves differently in full suite ❌
- Opposite failure modes (too cautious vs too assertive)
- Non-deterministic test outcomes

## The Solution

Enable `--clean-graph-between-tests` to:

1. **Clean graph before tests start** (ensures fresh state)
2. **Clean graph between each test** (ensures isolation)
3. **Skip cleanup in simulation mode** (no MCP, no need)

### How It Works

```python
# Before each test (or before first test):
1. Query all nodes in graph
2. Delete each node (connections cascade automatically)
3. Verify graph is empty
4. Continue with test
```

The cleanup uses a dedicated Claude Code session with MCP to perform the cleanup operations.

## Usage

### Basic Usage

Enable cleanup for test suite:

```bash
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests
```

### Combined with Other Flags

```bash
# Cleanup + specific test cases
python tests/test_conversational_layer.py \
  --mode real \
  --case capture_simple_task \
  --case capture_task_with_context \
  --clean-graph-between-tests

# Cleanup + interrogation
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests \
  --interrogate-failures

# Full audit with cleanup
python tests/test_conversational_layer.py \
  --mode real \
  --test-cases refactored \
  --clean-graph-between-tests \
  --interrogate-all \
  --interrogation-log audit.json
```

### When NOT to Use

Don't use cleanup if:
- Running in simulation mode (`--mode sim`) - cleanup is automatically skipped
- Testing behavior with pre-existing graph data
- Testing deduplication/search against populated graph
- Benchmarking performance (cleanup adds overhead)

## Example Output

### With Cleanup Enabled

```bash
$ python tests/test_conversational_layer.py \
  --mode real \
  --case test1 test2 \
  --clean-graph-between-tests

Using full system prompt: /path/to/system-prompt-full.md
Mode: Live MCP
Cleaning graph before tests...

Running test 1: capture_simple_task (Capture)
  Judge: PASS (expected PASS) - Successfully created task...
  Cleaning graph before next test...

Running test 2: capture_task_with_context (Capture)
  Judge: PASS (expected PASS) - Successfully created task...

Summary: 2/2 cases matched expectations.
```

### Without Cleanup (Default)

```bash
$ python tests/test_conversational_layer.py \
  --mode real \
  --case test1 test2

Using full system prompt: /path/to/system-prompt-full.md
Mode: Live MCP

Running test 1: capture_simple_task (Capture)
  Judge: PASS (expected PASS) - Successfully created task...

Running test 2: capture_task_with_context (Capture)
  Judge: FAIL (expected PASS) - Found existing task, asked for clarification...

Summary: 1/2 cases matched expectations.
```

Notice: Test 2 fails because it found Test 1's data!

## Performance Considerations

### Cleanup Overhead

Each cleanup operation:
- Takes ~2-5 seconds
- Makes 1 Claude Code API call
- Queries + deletes all nodes

For a 30-test suite:
- Without cleanup: ~10 minutes
- With cleanup: ~12-13 minutes (20-30% slower)

### Trade-offs

| Aspect | With Cleanup | Without Cleanup |
|--------|--------------|-----------------|
| **Test Isolation** | ✅ Perfect | ❌ Variable |
| **Determinism** | ✅ Consistent | ❌ Stochastic |
| **Speed** | ❌ Slower (20-30%) | ✅ Faster |
| **Real-world Testing** | ❌ Empty graph only | ✅ Tests with data |

## Use Cases

### Development Workflow

When actively developing/debugging:

```bash
# Test isolated behavior
python tests/test_conversational_layer.py \
  --mode real \
  --case problematic_test \
  --clean-graph-between-tests
```

### CI/CD Pipeline

For consistent, reproducible test results:

```bash
# CI should use cleanup for determinism
python tests/test_conversational_layer.py \
  --mode real \
  --suite assistant \
  --clean-graph-between-tests
```

### Regression Testing

After instruction changes:

```bash
# Ensure changes don't break isolated test behavior
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests \
  --interrogate-all \
  --interrogation-log regression_$(date +%Y%m%d).json
```

### Testing With Pre-existing Data

For scenarios that require populated graphs:

```bash
# Don't use cleanup - let tests share state
python tests/test_conversational_layer.py \
  --mode real \
  --suite deduplication_tests
```

## Troubleshooting

### Cleanup Fails

If you see:
```
WARNING: Graph cleanup failed: [error message]
```

**Causes**:
- MCP server not responding
- Graph operations timing out
- Permission issues

**Solution**:
- Check MCP server status
- Increase timeout: adjust `--assistant-timeout` (cleanup uses same timeout)
- Verify MCP config is valid

### Cleanup Incomplete

If tests still interfere:
- Check cleanup success messages
- Verify graph is actually empty after cleanup
- Look for nodes that aren't being deleted (e.g., system nodes)

### Too Slow

If cleanup makes tests too slow:
- Use cleanup selectively: only for tests that show variance
- Run isolated tests individually: `--case test_name`
- Use simulation mode for fast iteration: `--mode sim`

## Future Enhancements

Potential improvements:

- [ ] **Fixture support**: Preserve specific "fixture" nodes during cleanup
- [ ] **Partial cleanup**: Only delete nodes created by tests (not all nodes)
- [ ] **Graph snapshots**: Save/restore graph state instead of full cleanup
- [ ] **Smart cleanup**: Detect when cleanup is needed vs unnecessary
- [ ] **Setup fixtures**: Populate graph with test data before tests

## Related Issues

This feature solves the problem documented in:
- Test variance when run in isolation vs full suite
- Stochastic test outcomes due to shared MCP state
- Opposite failure modes (too cautious vs too assertive)

## Related Documentation

- [Testing Improvements](TESTING_IMPROVEMENTS.md) - Overall testing strategy
- [Interrogation Feature](INTERROGATION_FEATURE.md) - Post-test questioning
- [Implementation Complete](IMPLEMENTATION_COMPLETE.md) - Testing framework details
