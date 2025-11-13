# Graph Cleanup - Quick Start

## What Is This?

Automatically clean the graph between tests to ensure test isolation. Solves the problem where tests pass in isolation but fail/vary in full suite runs due to shared graph state.

## The Problem You Experienced

```
Test isolated:  python test.py --case test2  → PASS ✅ (5/5 times)
Test in suite:  python test.py               → FAIL ❌ (variable)
```

**Cause**: Test 1 leaves data in graph, Test 2 finds it and behaves differently.

## The Solution

```bash
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests
```

This will:
1. Clean graph before first test
2. Clean graph between each test
3. Ensure perfect test isolation

## Quick Examples

### Fix variance in test suite:
```bash
python tests/test_conversational_layer.py \
  --mode real \
  --case capture_simple_task \
  --case capture_task_with_context \
  --clean-graph-between-tests
```

### With interrogation (recommended):
```bash
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests \
  --interrogate-failures
```

### Full audit:
```bash
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests \
  --interrogate-all \
  --interrogation-log audit.json
```

## What You'll See

```
Mode: Live MCP
Cleaning graph before tests...

Running test 1: capture_simple_task (Capture)
  Judge: PASS (expected PASS)
  Cleaning graph before next test...

Running test 2: capture_task_with_context (Capture)
  Judge: PASS (expected PASS)

Summary: 2/2 cases matched expectations. ✅
```

## Trade-offs

| Aspect | With Cleanup | Without Cleanup |
|--------|--------------|-----------------|
| **Consistency** | ✅ Deterministic | ❌ Variable |
| **Isolation** | ✅ Perfect | ❌ Shared state |
| **Speed** | ❌ 20-30% slower | ✅ Faster |

## When to Use

✅ **Use cleanup for**:
- Fixing test variance
- CI/CD pipelines
- Regression testing
- Development/debugging

❌ **Don't use cleanup for**:
- Testing with populated graphs
- Performance benchmarks
- Deduplication testing

## Cost

- Adds ~2-5 seconds per test
- 30-test suite: +2-3 minutes total
- Worth it for deterministic behavior!

## More Details

See [GRAPH_CLEANUP_FEATURE.md](GRAPH_CLEANUP_FEATURE.md) for complete documentation.
