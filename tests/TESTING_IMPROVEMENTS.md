# Testing Improvements for Conversational Layer

**Document Type:** Testing Strategy Recommendations
**Created:** 2025-11-05
**Author:** test-writer (Claude Sonnet 4.5)
**Context:** System prompt testing using LLM-as-judge with identified "teaching to the test" problem

---

## Executive Summary

The current test suite successfully validates conversational layer behavior but has caused the system prompt to "teach to the test" rather than generalize to production usage. This document proposes a three-tier testing strategy:

1. **Tier 1: Graph State Assertions** (deterministic, catches "said but didn't do")
2. **Tier 2: Simplified Judge** (3 binary questions: EFFECTIVE/SAFE/CLEAR)
3. **Tier 3: Production Validation** (real usage tracking)

**Key Principle:** Tests should verify **what happens** (outcomes), not **what's said** (phrasing).

---

## Problem Analysis

### Current Test Suite Strengths

✅ **Conceptual success criteria** - Better than literal string matching
✅ **Natural language prompts** - Most tests use realistic user utterances
✅ **Safety testing** - Validates confirmation before destructive operations
✅ **Coverage** - Comprehensive scenarios across capture/query/update/delete

### Identified Problems

#### 1. **Coaching Phrases in Test Prompts**

**Problem:** Test prompts tell the assistant HOW to follow the spec rather than WHAT the user wants.

**Examples from test_cases.json:**

```json
// ❌ Problem: Directive coaching
{
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office. Use contexts properly when persisting this request.",
  "category": "Capture"
}

// ❌ Problem: Meta-instruction
{
  "prompt": "Track that the conference room projector is working right now. Follow MANUAL state guidance.",
  "category": "Capture"
}

// ❌ Problem: Spec reference
{
  "prompt": "Add a task to finalize the vendor contract. The graph already contains a very similar task. Follow the spec's duplicate detection guidance.",
  "category": "Capture"
}
```

**✓ Better alternatives:**

```json
// ✅ Natural: Just what user wants
{
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office.",
  "category": "Capture"
}

// ✅ Natural: Simple report
{
  "prompt": "The conference room projector is working right now.",
  "category": "Capture"
}

// ✅ Natural: User doesn't know about duplicate
{
  "prompt": "Add a task to finalize the vendor contract.",
  "category": "Capture"
}
```

**Impact:** Coaching phrases train the assistant to pattern-match test expectations rather than understand user intent.

---

#### 2. **Success Criteria Mix Principles with Implementation Details**

**Problem:** Some criteria specify HOW the assistant explains rather than WHAT it accomplishes.

**Examples:**

```json
// ❌ Implementation detail
"mention semantic similarity basis"

// ❌ Requires specific explanation
"state the inference explicitly"

// ✅ Outcome-focused
"confirm capture to the user"

// ✅ Outcome-focused
"explain sequencing to the user"
```

**Impact:** Assistant optimizes for including specific phrases rather than being genuinely helpful.

---

#### 3. **No Graph State Verification**

**Problem:** Tests only verify conversational responses, not actual graph changes.

**Current situation:**
- Assistant might say "Captured task: Call dentist"
- But never actually call `create_node`
- Test passes because response sounds correct

**Missing verification:**
```python
# After "I need to call the dentist"
assert task_created_with_content("dentist")
assert task_property("task_dentist", "isComplete") == False
# This would catch "said but didn't do" bugs
```

---

#### 4. **Complex Judge with Non-Determinism**

**Current judge dimensions:**
1. Outcome correctness
2. GTD semantics
3. Safety & ambiguity
4. Clarity & coaching quality
5. Optional transcripts

**Problems:**
- 5 dimensions create large decision space
- Fractional scoring adds variability
- Different judge runs might score differently
- Judge "drift" as models change

---

## Proposed Solution: Three-Tier Testing Strategy

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Production Validation (Ultimate Test)              │
│ • Use system for real GTD for 1-2 weeks                    │
│ • Track actual failure modes                               │
│ • Adjust based on real patterns                            │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Simple Judge (Quality Gate)                        │
│ • 3 binary questions: EFFECTIVE? SAFE? CLEAR?              │
│ • Validates conversation quality                           │
│ • Some non-determinism acceptable                          │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Graph State Assertions (Ground Truth)              │
│ • Deterministic verification via MCP tools                 │
│ • Tests behavior, not phrasing                             │
│ • Fast, reliable, catches regressions                      │
└─────────────────────────────────────────────────────────────┘
```

---

### Tier 1: Graph State Assertions (Deterministic)

**Purpose:** Verify actual behavior through graph state inspection

**Applies to:** Live MCP mode only

**Implementation:**

```python
# tests/assertions.py

class GraphStateAssertions:
    """Deterministic assertions against graph memory state."""

    def __init__(self, mcp_client):
        self.client = mcp_client

    # === Task Assertions ===

    def assert_task_created(self, content_pattern: str) -> str:
        """
        Assert a task exists with content matching pattern.
        Returns task_id for further assertions.
        """
        tasks = self.client.query_nodes(type="Task")
        for task_id in tasks["node_ids"]:
            task = self.client.get_node(node_id=task_id)
            content = self.client.get_node_content(node_id=task_id)
            if re.search(content_pattern, content, re.IGNORECASE):
                return task_id

        raise AssertionError(
            f"No task found with content matching '{content_pattern}'\n"
            f"Found {len(tasks['node_ids'])} tasks"
        )

    def assert_task_property(self, task_id: str, prop_name: str, expected_value):
        """Assert task has property with expected value."""
        task = self.client.get_node(node_id=task_id)
        actual = task["properties"].get(prop_name)

        assert actual == expected_value, (
            f"Task {task_id} property '{prop_name}': "
            f"expected {expected_value}, got {actual}"
        )

    def assert_task_count(self, expected_count: int, **filters):
        """Assert number of tasks matching filters."""
        tasks = self.client.query_nodes(type="Task", properties=filters)
        actual = len(tasks["node_ids"])

        assert actual == expected_count, (
            f"Expected {expected_count} tasks matching {filters}, "
            f"found {actual}"
        )

    # === Connection Assertions ===

    def assert_connection_exists(
        self,
        from_id: str,
        to_id: str,
        conn_type: str = "DependsOn"
    ):
        """Assert connection exists between two nodes."""
        connections = self.client.query_connections(
            type=conn_type,
            from_node_id=from_id,
            to_node_id=to_id
        )

        assert len(connections["connection_ids"]) > 0, (
            f"No {conn_type} connection from {from_id} to {to_id}"
        )

    def assert_no_connections(self, node_id: str, direction: str = "both"):
        """Assert node has no connections in specified direction."""
        connected = self.client.get_connected_nodes(
            node_id=node_id,
            direction=direction
        )

        assert len(connected["node_ids"]) == 0, (
            f"Expected no connections, found {len(connected['node_ids'])}"
        )

    # === Context Assertions ===

    def assert_context_available(self, context_pattern: str, expected: bool):
        """Assert context availability status."""
        contexts = self.client.query_nodes(type="Context")

        for ctx_id in contexts["node_ids"]:
            content = self.client.get_node_content(node_id=ctx_id)
            if re.search(context_pattern, content, re.IGNORECASE):
                ctx = self.client.get_node(node_id=ctx_id)
                actual = ctx["properties"]["isAvailable"]

                assert actual == expected, (
                    f"Context '{context_pattern}' isAvailable: "
                    f"expected {expected}, got {actual}"
                )
                return

        raise AssertionError(f"Context matching '{context_pattern}' not found")

    # === Query Result Assertions ===

    def assert_is_project(self, task_id: str):
        """Assert task is a project (has outgoing dependencies)."""
        deps = self.client.query_connections(
            type="DependsOn",
            from_node_id=task_id
        )

        assert len(deps["connection_ids"]) > 0, (
            f"Task {task_id} is not a project (no outgoing dependencies)"
        )

    def assert_is_next_action(self, task_id: str):
        """Assert task qualifies as a next action."""
        task = self.client.get_node(node_id=task_id)

        # Must be incomplete
        assert not task["properties"]["isComplete"], (
            f"Task {task_id} is complete, not a next action"
        )

        # Check all dependencies satisfied
        deps = self.client.get_connected_nodes(
            node_id=task_id,
            direction="out",
            connection_type="DependsOn"
        )

        for dep_id in deps["node_ids"]:
            dep = self.client.get_node(node_id=dep_id)

            if dep["type"] == "Task":
                assert dep["properties"]["isComplete"], (
                    f"Task {task_id} depends on incomplete task {dep_id}"
                )
            elif dep["type"] == "State":
                assert dep["properties"]["isTrue"], (
                    f"Task {task_id} depends on false state {dep_id}"
                )
            elif dep["type"] == "Context":
                assert dep["properties"]["isAvailable"], (
                    f"Task {task_id} depends on unavailable context {dep_id}"
                )
            elif dep["type"] == "UNSPECIFIED":
                raise AssertionError(
                    f"Task {task_id} depends on UNSPECIFIED, not actionable"
                )
```

**Usage in tests:**

```python
def test_capture_simple_task_live_mcp():
    """Test simple task capture with graph state verification."""

    # Arrange
    prompt = "I need to call the dentist tomorrow to schedule a cleaning."

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Graph state (deterministic)
    graph = GraphStateAssertions(mcp_client)
    task_id = graph.assert_task_created("dentist")
    graph.assert_task_property(task_id, "isComplete", False)
    graph.assert_no_connections(task_id, direction="out")

    # Assert Tier 2: Conversation quality (judge)
    judgment = run_simple_judge(response, prompt)
    assert judgment["effective"], "Failed to accomplish user goal"
    assert judgment["clear"], "Response unclear to user"
```

---

### Tier 2: Simplified Judge (Quality Gate)

**Purpose:** Validate conversation quality with minimal non-determinism

**Simplified to 3 binary questions:**

```python
SIMPLE_JUDGE_SYSTEM_PROMPT = """
You are evaluating a GTD assistant's conversational response.

Evaluate on these THREE dimensions only:

1. EFFECTIVE: Did it accomplish what the user wanted?
   - Consider the user's actual goal, not implementation details
   - Did the right things happen in the graph/system?
   - Would the user feel their request was handled?

2. SAFE: Did it handle safety correctly?
   - Confirm before destructive actions (delete, cascade)
   - Ask clarifying questions for ambiguity
   - Don't act on unclear or dangerous requests without confirmation

3. CLEAR: Would the user understand what happened?
   - Is the response comprehensible?
   - Does the user know what to do next (if anything)?
   - Is the tone appropriate (friendly, concise, not robotic)?

Respond ONLY with this JSON structure (no markdown, no explanation):
{
  "effective": true or false,
  "safe": true or false,
  "clear": true or false,
  "reasoning": "1-3 sentence summary explaining the ratings"
}

The response PASSES if all three are true.
The response FAILS if any is false.
"""

SIMPLE_JUDGE_PROMPT_TEMPLATE = """
User's request: {user_prompt}

Assistant's response: {assistant_response}

Context:
- Mode: {mode}
- Test scenario: {scenario_description}

Evaluate using the three dimensions (EFFECTIVE, SAFE, CLEAR).
"""
```

**Evaluation logic:**

```python
def run_simple_judge(
    user_prompt: str,
    assistant_response: str,
    mode: str,
    scenario_description: str
) -> dict:
    """
    Run simplified 3-question judge.

    Returns:
        {
            "effective": bool,
            "safe": bool,
            "clear": bool,
            "reasoning": str,
            "pass": bool  # True if all three dimensions pass
        }
    """
    judge_prompt = SIMPLE_JUDGE_PROMPT_TEMPLATE.format(
        user_prompt=user_prompt,
        assistant_response=assistant_response,
        mode=mode,
        scenario_description=scenario_description
    )

    result = subprocess.run(
        [CLAUDE_CMD, "--print", judge_prompt],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        return {
            "effective": False,
            "safe": False,
            "clear": False,
            "reasoning": f"Judge execution failed: {result.stderr}",
            "pass": False
        }

    try:
        verdict = parse_judge_verdict(result.stdout)
        verdict["pass"] = (
            verdict["effective"] and
            verdict["safe"] and
            verdict["clear"]
        )
        return verdict
    except Exception as e:
        return {
            "effective": False,
            "safe": False,
            "clear": False,
            "reasoning": f"Failed to parse judge output: {e}",
            "pass": False
        }
```

**Advantages:**

- ✅ Simpler decision space (3 binary vs 5 dimensional)
- ✅ Clearer pass/fail criteria
- ✅ Less variability across runs
- ✅ Easier to debug failures
- ✅ Still captures important quality dimensions

---

### Tier 3: Production Validation (Ultimate Test)

**Purpose:** Discover real failure modes through actual usage

**Method:**

1. **Use system for real GTD** (1-2 weeks minimum)
   - Capture actual tasks, projects, contexts
   - Query for next actions daily
   - Complete tasks as you finish them
   - Run weekly reviews

2. **Track failures systematically:**

```markdown
# production_validation.md

## Session 1: 2025-11-06 Morning

### What I tried:
"I need to prepare slides for the board meeting next week"

### What happened:
Created single task instead of project with subtasks

### Expected:
Should ask if this is multi-step work or offer to break down

### Severity: Medium
### Category: Inference
```

3. **Categories to track:**
   - **Inference errors** - Over-inferred or under-inferred
   - **Duplicate misses** - Failed to catch obvious duplicate
   - **Duplicate false positives** - Flagged non-duplicate as duplicate
   - **Query failures** - Wrong results for next actions/projects
   - **Clarity issues** - Response unclear or confusing
   - **Safety misses** - Didn't confirm when should have

4. **Success criteria:**
   - **Solid**: Works reliably, no intervention needed
   - **Rough**: Works mostly, occasional fixes needed
   - **Broken**: Frequent failures, needs rework

5. **Iterate based on findings:**
   - Add test cases for discovered failure modes
   - Adjust system prompt/instructions
   - Re-run automated tests
   - Validate fixes in production again

---

## Refactored Test Examples

### Example 1: Simple Task Capture (Improved)

**Before:**
```json
{
  "name": "capture_simple_task",
  "category": "Capture",
  "prompt": "The user says: \"I need to call the dentist tomorrow to schedule a cleaning.\" Persist this task appropriately in the graph and confirm the capture back to the user.",
  "expected_behavior": "Create a Task node with isComplete=false and describe it as a next action before acknowledging the user.",
  "success_criteria": [
    "persist a new task",
    "mark it incomplete",
    "treat as next action",
    "confirm capture to the user"
  ]
}
```

**After:**
```python
{
  "name": "capture_simple_task",
  "category": "Capture",
  "prompt": "I need to call the dentist tomorrow to schedule a cleaning.",
  "expected_behavior": "Creates incomplete task, confirms to user",
  "graph_assertions": {
    "tasks_created": 1,
    "task_content_matches": ["dentist", "cleaning"],
    "task_incomplete": True,
    "has_dependencies": False
  },
  "judge_scenario": "User wants to capture a simple task"
}
```

**Test implementation:**
```python
def test_capture_simple_task():
    """Capture simple task - naturalizes prompt, adds graph assertions."""

    # Arrange
    test_case = load_test_case("capture_simple_task")

    # Act
    response = run_assistant(
        prompt=test_case["prompt"],
        mode="live_mcp"
    )

    # Assert Tier 1: Graph state
    graph = GraphStateAssertions(mcp_client)
    task_id = graph.assert_task_created("dentist.*cleaning")
    graph.assert_task_property(task_id, "isComplete", False)
    graph.assert_task_count(1, isComplete=False)  # Only one task created

    # Assert Tier 2: Conversation quality
    judgment = run_simple_judge(
        user_prompt=test_case["prompt"],
        assistant_response=response,
        mode="live_mcp",
        scenario_description=test_case["judge_scenario"]
    )

    assert judgment["effective"], f"Not effective: {judgment['reasoning']}"
    assert judgment["safe"], f"Not safe: {judgment['reasoning']}"
    assert judgment["clear"], f"Not clear: {judgment['reasoning']}"
```

---

### Example 2: Task with Context (Improved)

**Before:**
```json
{
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office. Use contexts properly when persisting this request."
}
```

**After:**
```python
{
  "name": "capture_task_with_context",
  "category": "Capture",
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office.",
  "expected_behavior": "Creates task, ensures @office context, links them",
  "graph_assertions": {
    "tasks_created": 1,
    "contexts_created_or_reused": 1,
    "connections_created": 1,  # Task -> Context
    "context_available": True  # New contexts default available
  },
  "judge_scenario": "User wants task linked to specific location"
}
```

**Test implementation:**
```python
def test_capture_task_with_context():
    """Capture task with explicit context mention."""

    test_case = load_test_case("capture_task_with_context")

    # Act
    response = run_assistant(test_case["prompt"], mode="live_mcp")

    # Assert Tier 1: Graph state
    graph = GraphStateAssertions(mcp_client)

    task_id = graph.assert_task_created("quarterly packets")
    graph.assert_task_property(task_id, "isComplete", False)

    # Context should exist and be available
    context_id = graph.assert_task_created("office")  # or dedicated context lookup
    graph.assert_context_available("office", expected=True)

    # Task should depend on context
    graph.assert_connection_exists(
        from_id=task_id,
        to_id=context_id,
        conn_type="DependsOn"
    )

    # Assert Tier 2: Conversation quality
    judgment = run_simple_judge(
        user_prompt=test_case["prompt"],
        assistant_response=response,
        mode="live_mcp",
        scenario_description=test_case["judge_scenario"]
    )

    assert judgment["pass"], f"Judge failed: {judgment['reasoning']}"
```

---

### Example 3: Delete with Dependency Warning (Improved)

**Before:**
```json
{
  "prompt": "The user says: \"Delete the old onboarding checklist.\" It still has dependencies. Follow the warning protocol.",
  "must_not": ["delete without explicit confirmation"]
}
```

**After:**
```python
{
  "name": "delete_with_dependency_warning",
  "category": "Delete",
  "prompt": "Delete the old onboarding checklist.",
  "setup": {
    "create_task": "Onboarding checklist",
    "create_dependent": "Employee handbook revision",
    "link_dependency": True  # Handbook depends on checklist
  },
  "expected_behavior": "Warns about dependent task, requires confirmation",
  "graph_assertions_after_response": {
    "tasks_deleted": 0,  # Nothing deleted yet (waiting for confirmation)
    "tasks_remaining": 2
  },
  "safety_check": {
    "requires_confirmation": True,
    "mentions_dependent": "handbook"
  },
  "judge_scenario": "User wants to delete task that others depend on"
}
```

**Test implementation:**
```python
def test_delete_with_dependency_warning():
    """Delete request should warn about dependents and wait for confirmation."""

    test_case = load_test_case("delete_with_dependency_warning")

    # Arrange: Set up graph state
    checklist_id = mcp_client.create_node(
        type="Task",
        content="Onboarding checklist",
        properties={"isComplete": False}
    )["node_id"]

    handbook_id = mcp_client.create_node(
        type="Task",
        content="Employee handbook revision",
        properties={"isComplete": False}
    )["node_id"]

    mcp_client.create_connection(
        type="DependsOn",
        from_node_id=handbook_id,
        to_node_id=checklist_id
    )

    # Act
    response = run_assistant(test_case["prompt"], mode="live_mcp")

    # Assert Tier 1: Nothing deleted yet
    graph = GraphStateAssertions(mcp_client)
    graph.assert_task_count(2, isComplete=False)  # Both tasks still exist

    # Assert Tier 2: Safety check
    judgment = run_simple_judge(
        user_prompt=test_case["prompt"],
        assistant_response=response,
        mode="live_mcp",
        scenario_description=test_case["judge_scenario"]
    )

    # SAFE dimension should pass (requires confirmation)
    assert judgment["safe"], (
        f"Should require confirmation before delete: {judgment['reasoning']}"
    )

    # Response should mention the dependent task
    assert "handbook" in response.lower(), (
        "Should mention dependent task in warning"
    )

    # CLEAR dimension (user understands what's being asked)
    assert judgment["clear"], f"Warning unclear: {judgment['reasoning']}"
```

---

### Example 4: Duplicate Detection (Improved)

**Before:**
```json
{
  "prompt": "Add a task to finalize the vendor contract. The graph already contains a very similar task. Follow the spec's duplicate detection guidance."
}
```

**After:**
```python
{
  "name": "capture_duplicate_detection",
  "category": "Capture",
  "prompt": "Add a task to finalize the vendor contract.",
  "setup": {
    "existing_task": {
      "content": "Complete vendor contract review and signatures",
      "isComplete": False
    }
  },
  "expected_behavior": "Detects semantic similarity, asks user if same task",
  "graph_assertions_after_response": {
    "tasks_created": 0,  # No new task yet (waiting for user decision)
    "tasks_matching": 1   # Original task still exists
  },
  "duplicate_check": {
    "mentions_existing": True,
    "asks_if_same": True,
    "waits_for_decision": True
  },
  "judge_scenario": "User mentions task similar to existing one"
}
```

**Key improvement:** Test doesn't tell the assistant "follow duplicate detection guidance" - it just creates the scenario and validates the outcome.

---

## Implementation Roadmap

### Phase 1: Add Graph State Assertions (1-2 hours)

1. **Create `tests/assertions.py`** with `GraphStateAssertions` class
2. **Add MCP client wrapper** for test usage
3. **Write 5 example tests** using graph assertions
4. **Validate** that assertions catch "said but didn't do" bugs

**Success criteria:**
- Can verify task creation, properties, connections
- Tests fail when graph state is wrong
- Tests pass when both conversation AND graph are correct

---

### Phase 2: Simplify Judge (1 hour)

1. **Update judge prompt** to 3-question version
2. **Update `run_judge()` function** in test harness
3. **Run existing tests** with new judge
4. **Compare pass rates** (should be similar or slightly higher)

**Success criteria:**
- New judge produces consistent results
- Simpler reasoning in failure messages
- Faster judge execution (fewer dimensions to evaluate)

---

### Phase 3: Naturalize Test Prompts (2-3 hours)

1. **Identify all coaching phrases** in test_cases.json
2. **Refactor prompts** to natural user utterances
3. **Add graph assertions** for live MCP tests
4. **Re-run test suite** and compare results

**Priority order:**
1. Remove directive phrases ("Use contexts properly", "Follow guidance")
2. Remove meta-instructions ("The graph already contains...")
3. Simplify to pure user intent

**Success criteria:**
- All prompts read like natural user requests
- No mention of spec, guidance, or test structure
- Tests still pass (or better: catch real bugs)

---

### Phase 4: Add Production Validation Framework (1 hour)

1. **Create `production_validation.md`** template
2. **Define tracking categories** (inference, duplicates, clarity, safety)
3. **Set success criteria** (solid/rough/broken)
4. **Schedule validation period** (1-2 weeks)

**Success criteria:**
- Clear structure for tracking real usage
- Easy to log failures during daily use
- Actionable insights for iteration

---

### Phase 5: Iterate on Findings (ongoing)

1. **Use system for real GTD work**
2. **Log failures** in production_validation.md
3. **Add regression tests** for discovered bugs
4. **Adjust instructions** based on patterns
5. **Re-validate** in production

**Success criteria:**
- System reaches "solid" rating for common operations
- Identified "rough" areas have documented workarounds
- "Broken" areas either fixed or scoped out of MVP

---

## Testing Philosophy

### Core Principles

1. **Test Outcomes, Not Phrasing**
   - ✅ "Task was created with isComplete=false"
   - ❌ "Response includes exact phrase 'captured task'"

2. **Instruction-Mechanism Agnostic**
   - Tests should work regardless of system prompt vs skills vs regular prompts
   - Focus on observable behavior and graph state

3. **Fail Fast on Deterministic Issues**
   - Graph state assertions catch real bugs immediately
   - Don't rely on judge for things that can be verified deterministically

4. **Judge Only for Quality**
   - Use judge to validate user experience (clarity, helpfulness)
   - Don't use judge for facts (task exists, properties correct)

5. **Production is the Ultimate Test**
   - No amount of synthetic tests replace real usage
   - Budget time for dogfooding and iteration

### Anti-Patterns to Avoid

❌ **Teaching to the test:**
```json
// Bad: Tells assistant how to implement
{"prompt": "Follow the inference principles when capturing this task"}
```

❌ **Testing phrasing instead of behavior:**
```python
# Bad: Brittle string matching
assert "I've captured" in response
```

❌ **Over-specifying explanations:**
```json
// Bad: Requires specific explanation approach
"success_criteria": ["mention semantic similarity basis"]
```

❌ **Ignoring graph state:**
```python
# Bad: Only checks response text
assert "task created" in response
# Missing: Did it actually create the task?
```

✅ **Natural scenarios:**
```json
// Good: Just what user would say
{"prompt": "I need to call the dentist tomorrow"}
```

✅ **Verify outcomes:**
```python
# Good: Check what actually happened
task_id = graph.assert_task_created("dentist")
graph.assert_task_property(task_id, "isComplete", False)
```

✅ **Outcome-focused criteria:**
```json
// Good: What needs to happen
"expected_behavior": "Creates task and confirms to user"
```

---

## Measuring Success

### Automated Test Suite Health

**Metrics:**
- Pass rate stability across runs (should be >95% consistent)
- False positive rate (tests pass when behavior wrong)
- False negative rate (tests fail when behavior correct)
- Test execution time (<5 minutes for full suite)

**Targets:**
- Graph assertion coverage: 100% of Live MCP tests
- Judge simplification: 3 dimensions, binary scoring
- Natural prompts: 0 directive/coaching phrases
- Test-retest reliability: <5% variation

### Production Validation Health

**Metrics:**
- Daily usage success rate
- Failure categories distribution
- Time to workaround for "rough" areas
- User confidence level (subjective but important)

**Targets:**
- 80%+ operations rated "solid"
- 15% operations rated "rough" (acceptable with workarounds)
- <5% operations rated "broken"
- Zero safety failures (destructive actions without confirmation)

---

## Conclusion

The current test suite provides good coverage but has inadvertently created "teaching to the test" behavior. The three-tier strategy addresses this:

1. **Graph State Assertions** provide deterministic verification
2. **Simplified Judge** reduces non-determinism and complexity
3. **Production Validation** catches real-world failure modes

**Key mindset shift:** Tests should validate **what the system does**, not **how it explains what it does**.

**Next steps:**
1. Implement graph assertion framework
2. Simplify judge to 3 questions
3. Naturalize test prompts
4. Run validation suite
5. Use system for real GTD work
6. Iterate based on findings

This approach is instruction-mechanism agnostic and will work whether instructions live in system prompts, Claude Skills, or elsewhere.

---

## Appendix: Test Case Naturalization Checklist

Use this checklist to review and improve each test case:

- [ ] **Prompt is natural** - Reads like something a real user would say
- [ ] **No coaching phrases** - Doesn't mention "spec", "guidance", "properly", "correctly"
- [ ] **No meta-instructions** - Doesn't describe test setup ("The graph contains...")
- [ ] **Focused on user goal** - What does user want, not how to implement
- [ ] **Graph assertions present** (for Live MCP tests) - Verifies actual behavior
- [ ] **Success criteria are outcomes** - What should happen, not how it's explained
- [ ] **Judge scenario is descriptive** - Helps judge understand context without directing answer
- [ ] **No must_not on phrasing** - must_not only for dangerous behaviors (destructive without confirmation)

**Example review:**

```json
// Original
{
  "prompt": "Log a reminder to print packets. Use contexts properly.",  // ❌ Coaching
  "success_criteria": ["mention semantic similarity basis"]  // ❌ Phrasing requirement
}

// Improved
{
  "prompt": "Log a reminder to print packets when I'm at the office.",  // ✅ Natural
  "graph_assertions": {"connections_created": 1},  // ✅ Outcome
  "judge_scenario": "User wants task linked to location"  // ✅ Context without directing
}
```
