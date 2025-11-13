# Test Interrogation Feature

## Overview

The test harness now supports **automated interrogation** of test sessions. After a test completes and is judged, you can automatically ask the assistant follow-up questions to understand:

- **For failures**: Why did the test fail? What was unclear in the instructions?
- **For passes**: How good are the instructions? Could they be clearer or more concise?

This feature leverages Claude Code's session persistence to have multi-turn conversations with the test instance.

## Key Benefits

1. **Understand failures faster**: Get insight into the assistant's reasoning instead of just seeing "test failed"
2. **Improve instruction quality**: Survey successful tests to identify friction, redundancy, or ambiguity
3. **Automated workflow**: No need to manually load contexts - interrogation happens automatically during test runs
4. **Rich logging**: Export detailed Q&A transcripts for analysis over time

## How It Works

### Technical Flow

```
1. Test runs → Initial assistant response (session_id captured)
2. Judge evaluates → Pass/Fail verdict
3. If interrogation enabled for this outcome:
   ├─ Resume session using session_id
   ├─ Ask contextual questions
   └─ Capture Q&A transcript
4. Display results inline + optionally save to JSON log
```

### Session Resumption

The feature uses `claude --resume <session_id>` to continue the exact same context from the test run. This means:
- The assistant remembers what it did
- All the same instructions are active
- You can ask "why did you do X?" and get meaningful answers

## Usage

### Basic Usage

**Interrogate only failures** (debugging focus):
```bash
python tests/test_conversational_layer.py --interrogate-failures
```

**Interrogate only passes** (instruction quality focus):
```bash
python tests/test_conversational_layer.py --interrogate-passes
```

**Interrogate everything**:
```bash
python tests/test_conversational_layer.py --interrogate-all
```

### With Logging

Save detailed transcripts to JSON file:
```bash
python tests/test_conversational_layer.py \
  --interrogate-all \
  --interrogation-log interrogation_results.json
```

### Advanced Options

**Custom timeout** (default is 60 seconds per question):
```bash
python tests/test_conversational_layer.py \
  --interrogate-failures \
  --interrogation-timeout 120
```

**Combine with other options**:
```bash
python tests/test_conversational_layer.py \
  --mode sim \
  --test-cases refactored \
  --suite assistant \
  --interrogate-all \
  --interrogation-log results.json
```

## Question Templates

### Failure Interrogation (Debugging)

When a test fails, the assistant is asked:

1. "Why did you choose that approach to handle the user's request?"
2. "The judge indicated your response had issues. Looking back, what were you trying to accomplish and why did you think that approach would work?"
3. "Looking at the instructions you were given (system prompt, Claude Skill guidance, test context), was there anything unclear that made this task difficult? What could be written differently to make the right choice more obvious?"

**Purpose**: Understand the reasoning behind the failure and identify instruction gaps.

### Success Interrogation (Quality Survey)

When a test passes, the assistant is asked:

> Thank you! That was the desired behavior for this test.
>
> We're evaluating the quality of our instructions to ensure they make the right choices easy and clear. A few quick questions:
>
> 1. Was it clear what you needed to do for this request?
> 2. Were there any aspects where you felt uncertain about the right approach?
> 3. Could any of the instructions (system prompt, Claude Skill guidance, test context) have been written more clearly or concisely?
> 4. Was anything redundant or unnecessarily verbose in the instructions?
>
> Please be candid - we want to improve the instructions, not just confirm they work.

**Purpose**: Get candid feedback on instruction quality, clarity, and efficiency.

## Example Output

### Console Output

```
Running test 1: capture_simple_task (Capture)
  Judge: PASS (expected PASS) - Successfully captured task...
  Interrogating session (success)...

    Q: Thank you! That was the desired behavior for this test...
    A: Thank you for asking! I'll be candid:

    ## 1. Was it clear what you needed to do?

    **Yes, very clear.** The request was straightforward: capture a task...

    ## 2. Any uncertainty?

    **Minor uncertainty about the @phone context assumption...** I inferred...
```

### JSON Log Format

```json
[
  {
    "test": "capture_simple_task",
    "category": "Capture",
    "passed": true,
    "interrogation_type": "success",
    "qa": [
      {
        "question": "Thank you! That was the desired behavior...",
        "answer": "Thank you for asking! I'll be candid:\n\n## 1. Was it clear..."
      }
    ]
  }
]
```

## Workflow Integration

### During Development

While iterating on instructions:

```bash
# Run tests with interrogation
python tests/test_conversational_layer.py \
  --interrogate-all \
  --interrogation-log dev_$(date +%Y%m%d).json

# Analyze results to identify:
# - Common sources of confusion
# - Redundant instructions
# - Missing guidance
```

### Debugging Specific Failures

```bash
# Interrogate just the failing test
python tests/test_conversational_layer.py \
  --case problematic_test_name \
  --interrogate-failures
```

### CI/CD Integration

```bash
# In CI: Interrogate failures and save log as artifact
python tests/test_conversational_layer.py \
  --interrogate-failures \
  --interrogation-log ci_interrogation.json || true

# Upload ci_interrogation.json as build artifact for review
```

## Tips and Best Practices

### When to Use Each Mode

- **`--interrogate-failures`**: Best for active development when tests are failing
- **`--interrogate-passes`**: Best for instruction refinement when tests mostly pass
- **`--interrogate-all`**: Best for comprehensive instruction audits (but slower/more expensive)

### Analyzing Logs

Look for patterns across multiple interrogations:

```bash
# View all success interrogations
jq '.[] | select(.interrogation_type == "success") | .qa[0].answer' interrogation_results.json

# Find common themes in failures
jq '.[] | select(.passed == false) | {test: .test, reason: .qa[0].answer}' interrogation_results.json
```

### Cost Considerations

Each interrogation adds:
- **Failure mode**: 3 additional LLM calls (one per question)
- **Success mode**: 1 additional LLM call (single comprehensive question)

Use selectively during development, enable broadly for periodic instruction audits.

## Limitations and Caveats

1. **No interrogation for `assistant_override` cases**: Tests using pre-canned responses can't be interrogated (no session to resume)
2. **Simulation mode context**: Interrogations happen in the same mode (sim/real) as the test
3. **Timeout handling**: Long-running interrogations may timeout (use `--interrogation-timeout` to adjust)
4. **Session lifecycle**: Sessions are ephemeral and may not persist indefinitely

## Future Enhancements

Potential improvements:

- [ ] Custom question templates per test category
- [ ] Interactive interrogation mode (ask custom questions during test run)
- [ ] Comparison views (track instruction quality over time)
- [ ] Automatic analysis of interrogation logs (pattern detection)

## Related Documentation

- [Testing Improvements](TESTING_IMPROVEMENTS.md) - Overall testing strategy
- [Architecture Update](ARCHITECTURE_UPDATE.md) - How system prompt separation works
- [Implementation Complete](IMPLEMENTATION_COMPLETE.md) - Testing framework details
