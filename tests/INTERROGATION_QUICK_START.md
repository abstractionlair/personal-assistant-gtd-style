# Test Interrogation - Quick Start

## What Is This?

Automatically ask your test instances **why they did what they did** after tests complete. Great for:
- Understanding failures: "Why didn't this work?"
- Improving instructions: "Was anything unclear or redundant?"

## 30-Second Examples

### Debug a failing test:
```bash
python tests/test_conversational_layer.py \
  --case my_failing_test \
  --interrogate-failures
```

### Survey instruction quality:
```bash
python tests/test_conversational_layer.py \
  --interrogate-passes \
  --interrogation-log survey_results.json
```

### Full audit:
```bash
python tests/test_conversational_layer.py \
  --interrogate-all \
  --interrogation-log audit_$(date +%Y%m%d).json
```

## CLI Arguments

| Argument | Purpose |
|----------|---------|
| `--interrogate-failures` | Ask why when tests fail |
| `--interrogate-passes` | Survey quality when tests pass |
| `--interrogate-all` | Do both (comprehensive but slower) |
| `--interrogation-log FILE` | Save Q&A transcripts to JSON |
| `--interrogation-timeout N` | Seconds per question (default: 60) |

## What Questions Are Asked?

### For Failures (3 questions):
1. Why did you choose that approach?
2. What were you trying to accomplish?
3. What instructions were unclear?

### For Passes (1 comprehensive question):
- Survey covering clarity, uncertainty, redundancy, and improvement suggestions

## Real Example

```bash
$ python tests/test_conversational_layer.py \
  --case capture_simple_task \
  --interrogate-passes

Running test 1: capture_simple_task (Capture)
  Judge: PASS - Successfully captured task...
  Interrogating session (success)...

    Q: Thank you! That was the desired behavior...
    A: I'll be candid:

    ## 1. Was it clear?
    **Yes, very clear.** The GTD MCP tool descriptions...

    ## 2. Any uncertainty?
    **Minor uncertainty about @phone context...** I inferred...

    ## 3. Could instructions be clearer?
    **Yes - TodoWrite tool description is overly aggressive...**
```

## Combine with Graph Cleanup

For deterministic test behavior in Live MCP mode:

```bash
python tests/test_conversational_layer.py \
  --mode real \
  --clean-graph-between-tests \
  --interrogate-failures
```

See [GRAPH_CLEANUP_FEATURE.md](GRAPH_CLEANUP_FEATURE.md) for details.

## Tips

- **Use `--interrogate-failures`** during active debugging
- **Use `--interrogate-passes`** for periodic instruction reviews
- **Use `--interrogate-all`** for comprehensive audits (more expensive)
- **Save logs** (`--interrogation-log`) to track instruction quality over time
- **Use `--clean-graph-between-tests`** to ensure test isolation

## View Saved Logs

```bash
# Pretty-print the log
cat interrogation_results.json | jq

# Extract just the answers
jq '.[] | .qa[].answer' interrogation_results.json

# Filter by type
jq '.[] | select(.interrogation_type == "success")' interrogation_results.json
```

## More Details

See [INTERROGATION_FEATURE.md](INTERROGATION_FEATURE.md) for complete documentation.
