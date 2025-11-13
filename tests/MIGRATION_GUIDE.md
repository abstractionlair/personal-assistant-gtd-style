# Test Case Migration Guide

**Purpose:** Step-by-step guide to refactor existing test cases using the three-tier strategy

**Target:** Convert tests in `test_cases.json` to use natural prompts and graph assertions

---

## Quick Reference: Common Problems

| Problem | Example | Fix |
|---------|---------|-----|
| **Coaching phrase** | "Use contexts properly" | Remove entirely |
| **Meta-instruction** | "The graph already contains..." | Move to test setup |
| **Spec reference** | "Follow guidance" | Remove, test behavior instead |
| **Implementation detail** | "mention semantic similarity basis" | Remove from criteria |
| **Phrasing requirement** | "state the inference explicitly" | Replace with outcome check |

---

## Migration Process for Each Test

### Step 1: Identify Coaching Phrases

Scan prompt for:
- "properly", "correctly", "appropriately"
- "Follow the [spec/guidance/rules]"
- "Use [feature] when [doing X]"
- Test setup details ("The graph contains...")

### Step 2: Extract Setup Requirements

If prompt mentions existing state:
```json
// Before
"prompt": "Mark the proposal done. There are two proposals in the graph."

// After - Move to setup
"prompt": "Mark the proposal done.",
"setup": {
  "create_tasks": [
    {"content": "Client proposal for Q4", "isComplete": false},
    {"content": "Internal hiring proposal", "isComplete": false}
  ]
}
```

### Step 3: Naturalize the Prompt

Remove all non-user language:
```json
// Before
"prompt": "Log a reminder to print packets. Use contexts properly when persisting this request."

// After
"prompt": "Log a reminder to print the quarterly packets when I'm at the office."
```

### Step 4: Add Graph Assertions

Define expected graph state after operation:
```json
"graph_assertions": {
  "tasks_created": 1,
  "contexts_created_or_reused": 1,
  "connections_created": 1,
  "task_incomplete": true
}
```

### Step 5: Simplify Success Criteria

Remove phrasing requirements, keep outcomes:
```json
// Before
"success_criteria": [
  "persist a new task",
  "mark it incomplete",
  "treat as next action",
  "confirm capture to the user",
  "mention semantic similarity basis"  // ❌ Phrasing requirement
]

// After
"expected_behavior": "Creates incomplete task, confirms to user"
```

### Step 6: Add Judge Scenario

Provide context for judge without directing answer:
```json
"judge_scenario": "User wants to capture a simple task"
// Not: "User wants to capture task and should use proper GTD semantics"
```

---

## Conversion Examples: All 32 Test Cases

### Capture Tests (9 cases)

#### 1. capture_simple_task

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
  ],
  "must_not": [
    "pre-emptively ask for permission before capture",
    "defer task creation pending permission"
  ]
}
```

**After:**
```json
{
  "name": "capture_simple_task",
  "category": "Capture",
  "prompt": "I need to call the dentist tomorrow to schedule a cleaning.",
  "expected_behavior": "Creates incomplete task, confirms to user",
  "graph_assertions": {
    "tasks_created": 1,
    "task_content_matches": ["dentist", "cleaning"],
    "task_property": {"isComplete": false},
    "has_dependencies": false
  },
  "judge_scenario": "User wants to capture a simple task"
}
```

**Changes:**
- ✅ Removed "The user says:" framing
- ✅ Removed "Persist this task appropriately in the graph"
- ✅ Added graph_assertions for deterministic verification
- ✅ Simplified success_criteria to expected_behavior
- ✅ Removed must_not (redundant with judge SAFE dimension)

---

#### 2. capture_task_with_context

**Before:**
```json
{
  "name": "capture_task_with_context",
  "category": "Capture",
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office. Use contexts properly when persisting this request.",
  "expected_behavior": "Create the task, ensure context @office exists or is created, connect the task to the context, and explain the availability expectation.",
  "success_criteria": [
    "persist the task",
    "ensure @office context exists",
    "link task to @office context",
    "explain availability expectations"
  ]
}
```

**After:**
```json
{
  "name": "capture_task_with_context",
  "category": "Capture",
  "prompt": "Log a reminder to print the quarterly packets when I'm at the office.",
  "expected_behavior": "Creates task, creates/reuses @office context, links them",
  "graph_assertions": {
    "tasks_created": 1,
    "contexts_created_or_reused": 1,
    "context_pattern": "office",
    "context_available": true,
    "connections_created": 1,
    "connection_type": "DependsOn"
  },
  "judge_scenario": "User wants task associated with specific location"
}
```

**Changes:**
- ✅ Removed coaching "Use contexts properly when persisting this request"
- ✅ Added graph_assertions for context and connection
- ✅ Removed "explain availability expectations" (judge CLEAR handles this)

---

#### 3. capture_task_with_dependency

**Before:**
```json
{
  "name": "capture_task_with_dependency",
  "category": "Capture",
  "prompt": "I need to send the board update, but only after I finish the financial summary. Capture the dependent work correctly.",
  "expected_behavior": "Create both tasks if needed and add a DependsOn connection so the board update waits for the summary.",
  "success_criteria": [
    "create both tasks if missing",
    "establish dependency from update to summary",
    "explain sequencing to the user"
  ],
  "must_not": [
    "pre-emptively ask for permission before capture",
    "defer task creation pending permission"
  ]
}
```

**After:**
```json
{
  "name": "capture_task_with_dependency",
  "category": "Capture",
  "prompt": "I need to send the board update, but only after I finish the financial summary.",
  "expected_behavior": "Creates both tasks with correct dependency direction",
  "graph_assertions": {
    "tasks_created": 2,
    "task1_content": "board update",
    "task2_content": "financial summary",
    "dependency_from": "board update",
    "dependency_to": "financial summary",
    "board_is_project": true,
    "summary_is_next_action": true
  },
  "judge_scenario": "User describes sequential work dependency"
}
```

**Changes:**
- ✅ Removed "Capture the dependent work correctly"
- ✅ Added specific graph assertions for dependency direction
- ✅ Added project/next action checks

---

#### 4. capture_task_with_unspecified

**Before:**
```json
{
  "name": "capture_task_with_unspecified",
  "category": "Capture",
  "prompt": "I'm not sure what the next step is for the marketing launch, but something needs to happen. Persist the task in a way that reflects the uncertainty.",
  "expected_behavior": "Create a task that depends on the UNSPECIFIED singleton and explain that it blocks actionability.",
  "success_criteria": [
    "persist the task",
    "ensure UNSPECIFIED singleton exists",
    "link task to UNSPECIFIED",
    "explain that it is blocked until defined"
  ],
  "must_not": [
    "pre-emptively ask for permission before capture",
    "defer task creation pending permission"
  ]
}
```

**After:**
```json
{
  "name": "capture_task_with_unspecified",
  "category": "Capture",
  "prompt": "I'm not sure what the next step is for the marketing launch, but something needs to happen.",
  "expected_behavior": "Creates task linked to UNSPECIFIED, explains blockage",
  "graph_assertions": {
    "tasks_created": 1,
    "task_content": "marketing launch",
    "depends_on_unspecified": true,
    "task_not_next_action": true
  },
  "judge_scenario": "User mentions vague work without clear decomposition"
}
```

**Changes:**
- ✅ Removed "Persist the task in a way that reflects the uncertainty"
- ✅ Graph assertions verify UNSPECIFIED link
- ✅ Verify task NOT in next actions

---

#### 5. capture_duplicate_detection

**Before:**
```json
{
  "name": "capture_duplicate_detection",
  "category": "Capture",
  "prompt": "Add a task to finalize the vendor contract. The graph already contains a very similar task. Follow the spec's duplicate detection guidance.",
  "expected_behavior": "Query for similar tasks, flag the potential duplicate, and ask the user how to proceed.",
  "success_criteria": [
    "search for similar tasks",
    "flag potential duplicate",
    "ask whether to reuse or create new",
    "mention semantic similarity basis"
  ],
  "must_not": [
    "create duplicate without asking"
  ]
}
```

**After:**
```json
{
  "name": "capture_duplicate_detection",
  "category": "Capture",
  "prompt": "Add a task to finalize the vendor contract.",
  "setup": {
    "existing_task": {
      "content": "Complete vendor contract review and signatures",
      "isComplete": false
    }
  },
  "expected_behavior": "Detects similarity, asks user if same task",
  "graph_assertions": {
    "tasks_created": 0,
    "existing_tasks_unchanged": true
  },
  "judge_scenario": "User mentions task similar to existing one",
  "safety_check": {
    "waits_for_user_decision": true,
    "mentions_existing_task": true
  }
}
```

**Changes:**
- ✅ Removed "The graph already contains..." (moved to setup)
- ✅ Removed "Follow the spec's duplicate detection guidance"
- ✅ Removed "mention semantic similarity basis" (implementation detail)
- ✅ Setup creates existing task silently
- ✅ Graph assertions verify no duplicate created yet

---

#### 6. capture_project_with_subtasks

**Before:**
```json
{
  "name": "capture_project_with_subtasks",
  "category": "Capture",
  "prompt": "I need to prepare the investor packet: gather metrics, draft the narrative, and polish the slides. Capture this in project form per the planning model.",
  "expected_behavior": "Create a parent project task and three child tasks, wiring DependsOn edges from the parent to each child.",
  "success_criteria": [
    "create parent project",
    "create three child tasks",
    "wire dependencies parent depends on each child",
    "summarize the plan"
  ]
}
```

**After:**
```json
{
  "name": "capture_project_with_subtasks",
  "category": "Capture",
  "prompt": "I need to prepare the investor packet: gather metrics, draft the narrative, and polish the slides.",
  "expected_behavior": "Creates parent and child tasks with correct dependencies",
  "graph_assertions": {
    "tasks_created": 4,
    "parent_content": "investor packet",
    "child_contents": ["metrics", "narrative", "slides"],
    "parent_is_project": true,
    "parent_depends_on_children": true,
    "children_are_next_actions": true
  },
  "judge_scenario": "User describes multi-step project"
}
```

**Changes:**
- ✅ Removed "Capture this in project form per the planning model"
- ✅ Graph assertions verify all relationships
- ✅ Verify derived views (project, next actions)

---

#### 7. capture_delegated_task

**Before:**
```json
{
  "name": "capture_delegated_task",
  "category": "Capture",
  "prompt": "Log that Jane is handling the new logo design. Persist this as a waiting-for item.",
  "expected_behavior": "Create or update a task with responsibleParty set to Jane, isComplete=false, and mark it as waiting for someone else.",
  "success_criteria": [
    "set responsible party to Jane",
    "leave task incomplete",
    "treat as delegated / waiting-for",
    "confirm tracking to the user",
    "explicitly state that the task was created or updated"
  ]
}
```

**After:**
```json
{
  "name": "capture_delegated_task",
  "category": "Capture",
  "prompt": "Log that Jane is handling the new logo design.",
  "expected_behavior": "Creates delegated task with responsibleParty=Jane",
  "graph_assertions": {
    "tasks_created": 1,
    "task_content": "logo design",
    "task_property": {
      "isComplete": false,
      "responsibleParty": "Jane"
    },
    "task_is_waiting_for": true,
    "task_not_next_action": true
  },
  "judge_scenario": "User delegates task to external party"
}
```

**Changes:**
- ✅ Removed "Persist this as a waiting-for item"
- ✅ Graph assertions verify delegation properties
- ✅ Verify derived views (waiting for, not next action)

---

#### 8. capture_manual_state

**Before:**
```json
{
  "name": "capture_manual_state",
  "category": "Capture",
  "prompt": "Track that the conference room projector is working right now. Follow MANUAL state guidance.",
  "expected_behavior": "Create or update a MANUAL state node with isTrue=true and explain that the user must report changes.",
  "success_criteria": [
    "create or update MANUAL state",
    "set state to true",
    "remind user to report changes"
  ]
}
```

**After:**
```json
{
  "name": "capture_manual_state",
  "category": "Capture",
  "prompt": "Track that the conference room projector is working right now.",
  "expected_behavior": "Creates MANUAL state set to true, explains tracking",
  "graph_assertions": {
    "states_created": 1,
    "state_content": "projector",
    "state_properties": {
      "isTrue": true,
      "logic": "MANUAL"
    }
  },
  "judge_scenario": "User reports environmental condition"
}
```

**Changes:**
- ✅ Removed "Follow MANUAL state guidance"
- ✅ Graph assertions verify state properties
- ✅ Judge CLEAR checks explanation quality

---

#### 9. capture_infer_obvious_context

**Before:**
```json
{
  "name": "capture_infer_obvious_context",
  "category": "Capture",
  "prompt": "Add a reminder to call the dentist. Apply the inference guidance for obvious contexts.",
  "expected_behavior": "Create the task, infer that it requires a phone context, attach the dependency, and mention the inference explicitly.",
  "success_criteria": [
    "persist the task",
    "infer @phone context",
    "link task to @phone",
    "state the inference explicitly"
  ]
}
```

**After:**
```json
{
  "name": "capture_infer_obvious_context",
  "category": "Capture",
  "prompt": "Add a reminder to call the dentist.",
  "expected_behavior": "Creates task, infers @phone context, links them",
  "graph_assertions": {
    "tasks_created": 1,
    "contexts_created_or_reused": 1,
    "context_pattern": "phone",
    "connection_exists": true
  },
  "judge_scenario": "User mentions task with obvious context implication"
}
```

**Changes:**
- ✅ Removed "Apply the inference guidance for obvious contexts"
- ✅ Removed "state the inference explicitly" (let response be natural)
- ✅ Graph assertions verify inference happened

---

### Query Tests (6 cases)

#### 10. query_next_actions

**Before:**
```json
{
  "name": "query_next_actions",
  "category": "Query",
  "prompt": "What next actions are available right now? Assume contexts and dependencies should be respected.",
  "expected_behavior": "Run the Next Actions query that filters for incomplete tasks with satisfied dependencies and exclude those tied to UNSPECIFIED.",
  "success_criteria": [
    "filter to incomplete tasks",
    "exclude items blocked by dependencies or UNSPECIFIED",
    "respect context availability",
    "present next actions clearly"
  ],
  "must_not": [
    "include blocked items",
    "ignore context availability"
  ]
}
```

**After:**
```json
{
  "name": "query_next_actions",
  "category": "Query",
  "prompt": "What should I work on next?",
  "setup": {
    "create_tasks": [
      {"content": "Write report", "isComplete": false},
      {"content": "Review report", "isComplete": false, "depends_on": "Write report"},
      {"content": "Call client", "isComplete": false, "depends_on": "@phone"}
    ],
    "create_contexts": [
      {"content": "@phone", "isAvailable": true}
    ]
  },
  "expected_behavior": "Returns actionable tasks only",
  "graph_verification": {
    "query_result_should_include": ["Write report", "Call client"],
    "query_result_should_exclude": ["Review report"]
  },
  "judge_scenario": "User asks what to work on"
}
```

**Changes:**
- ✅ Removed "Assume contexts and dependencies should be respected"
- ✅ Setup creates test scenario
- ✅ Graph verification checks query correctness
- ✅ Natural prompt variation ("What should I work on next?")

---

#### 11. query_projects

**Before:**
```json
{
  "name": "query_projects",
  "category": "Query",
  "prompt": "Show me my active projects. Use the derived view definition.",
  "expected_behavior": "Identify tasks with outgoing DependsOn edges, list incomplete ones, and summarize dependency counts.",
  "success_criteria": [
    "identify tasks with outgoing dependencies",
    "limit to incomplete projects",
    "summarize dependency status"
  ]
}
```

**After:**
```json
{
  "name": "query_projects",
  "category": "Query",
  "prompt": "Show me my active projects.",
  "setup": {
    "create_tasks": [
      {"content": "Launch website", "isComplete": false, "has_subtasks": 3},
      {"content": "Design homepage", "isComplete": false},
      {"content": "Write content", "isComplete": true},
      {"content": "Deploy", "isComplete": false}
    ],
    "create_dependencies": [
      "Launch website → Design homepage",
      "Launch website → Write content",
      "Launch website → Deploy"
    ]
  },
  "expected_behavior": "Lists projects with dependency status",
  "graph_verification": {
    "identifies_as_project": ["Launch website"],
    "shows_incomplete_deps": ["Design homepage", "Deploy"],
    "shows_complete_deps": ["Write content"]
  },
  "judge_scenario": "User wants overview of multi-step work"
}
```

**Changes:**
- ✅ Removed "Use the derived view definition"
- ✅ Setup creates project scenario
- ✅ Graph verification checks project identification

---

### Update Tests (5 cases)

#### 18. update_mark_complete

**Before:**
```json
{
  "name": "update_mark_complete",
  "category": "Update",
  "prompt": "I finished filing the quarterly taxes. Update the task appropriately.",
  "expected_behavior": "Find the matching task, set isComplete=true, record completion message, and mention follow-up if dependencies unblock projects.",
  "success_criteria": [
    "locate the matching task",
    "mark task complete",
    "record completion",
    "note if any project becomes unblocked"
  ]
}
```

**After:**
```json
{
  "name": "update_mark_complete",
  "category": "Update",
  "prompt": "I finished filing the quarterly taxes.",
  "setup": {
    "create_task": {
      "content": "File quarterly taxes",
      "isComplete": false
    }
  },
  "expected_behavior": "Marks task complete",
  "graph_assertions": {
    "task_property": {"isComplete": true}
  },
  "judge_scenario": "User reports task completion"
}
```

**Changes:**
- ✅ Removed "Update the task appropriately"
- ✅ Setup creates task
- ✅ Graph assertion verifies completion

---

### Delete Tests (2 cases)

#### 22. delete_with_dependency_warning

**Before:**
```json
{
  "name": "delete_with_dependency_warning",
  "category": "Delete",
  "prompt": "Delete the old onboarding checklist. It still has dependencies. Follow the warning protocol.",
  "expected_behavior": "Fetch dependencies, warn the user about impacts, and only proceed after explicit confirmation.",
  "success_criteria": [
    "inspect dependencies before deletion",
    "warn about impacts",
    "require explicit confirmation before proceeding"
  ],
  "must_not": [
    "delete without explicit confirmation"
  ]
}
```

**After:**
```json
{
  "name": "delete_with_dependency_warning",
  "category": "Delete",
  "prompt": "Delete the old onboarding checklist.",
  "setup": {
    "create_tasks": [
      {"content": "Onboarding checklist", "isComplete": false},
      {"content": "Employee handbook", "isComplete": false, "depends_on": "Onboarding checklist"}
    ]
  },
  "expected_behavior": "Warns about dependent task, waits for confirmation",
  "graph_assertions": {
    "tasks_deleted": 0,
    "tasks_still_exist": 2
  },
  "safety_check": {
    "requires_confirmation": true,
    "mentions_dependent": "handbook"
  },
  "judge_scenario": "User wants to delete task that others depend on"
}
```

**Changes:**
- ✅ Removed "It still has dependencies"
- ✅ Removed "Follow the warning protocol"
- ✅ Setup creates dependency
- ✅ Graph assertions verify nothing deleted yet
- ✅ Safety check verifies warning behavior

---

#### 23. delete_cascade_confirmed

**Before:**
```json
{
  "name": "delete_cascade_confirmed",
  "category": "Delete",
  "prompt": "After warning, the user responds: \"Yes, go ahead and remove it even if it deletes the subtasks.\" Finish cleanup.",
  "expected_behavior": "Proceed with deletions in correct order, including cascading dependencies, and summarize what was removed.",
  "success_criteria": [
    "perform deletion after confirmation",
    "cascade removals in correct order",
    "summarize what was removed"
  ],
  "must_not": [
    "ask for confirmation again after confirmation was given",
    "refuse to act after confirmation"
  ]
}
```

**After:**
```json
{
  "name": "delete_cascade_confirmed",
  "category": "Delete",
  "conversation_flow": [
    {
      "prompt": "Delete the old onboarding checklist.",
      "expected": "Warning about dependencies"
    },
    {
      "prompt": "Yes, go ahead and remove it even if it deletes the subtasks.",
      "expected": "Performs deletion"
    }
  ],
  "setup": {
    "create_tasks": [
      {"content": "Onboarding checklist", "isComplete": false},
      {"content": "Employee handbook", "isComplete": false, "depends_on": "Onboarding checklist"}
    ]
  },
  "expected_behavior": "Completes deletion after confirmation",
  "graph_assertions_after_confirmation": {
    "checklist_deleted": true
  },
  "judge_scenario": "User confirms deletion after seeing warning"
}
```

**Changes:**
- ✅ Removed "After warning, the user responds:" meta-description
- ✅ Added conversation_flow to show sequence
- ✅ Graph assertions verify actual deletion

---

### Edge Case Tests (6 cases)

#### 25. edge_empty_results

**Before:**
```json
{
  "name": "edge_empty_results",
  "category": "Edge",
  "prompt": "Any next actions for @studio? No matching items exist.",
  "expected_behavior": "Run the query, detect there are no results, and reply with a helpful message encouraging capture or context changes.",
  "success_criteria": [
    "run the relevant query",
    "explain that results are empty",
    "suggest capture or different contexts"
  ]
}
```

**After:**
```json
{
  "name": "edge_empty_results",
  "category": "Edge",
  "prompt": "Any next actions for @studio?",
  "setup": {
    "create_contexts": [
      {"content": "@studio", "isAvailable": true}
    ],
    "create_tasks": []
  },
  "expected_behavior": "Handles empty results gracefully",
  "graph_assertions": {
    "tasks_matching_query": 0
  },
  "judge_scenario": "User queries context with no matching work"
}
```

**Changes:**
- ✅ Removed "No matching items exist" meta-description
- ✅ Setup creates empty scenario
- ✅ Graph assertions verify empty state

---

#### 26. edge_ambiguous_reference

**Before:**
```json
{
  "name": "edge_ambiguous_reference",
  "category": "Edge",
  "prompt": "Mark the proposal done. There are two proposals. Handle the ambiguity.",
  "expected_behavior": "Search for matches, present disambiguation choices, and wait for clarification before updating anything.",
  "success_criteria": [
    "identify multiple matches",
    "ask for clarification",
    "make no changes until clarified"
  ],
  "must_not": [
    "make updates before disambiguation"
  ]
}
```

**After:**
```json
{
  "name": "edge_ambiguous_reference",
  "category": "Edge",
  "prompt": "Mark the proposal done.",
  "setup": {
    "create_tasks": [
      {"content": "Client proposal for Q4", "isComplete": false},
      {"content": "Internal hiring proposal", "isComplete": false}
    ]
  },
  "expected_behavior": "Asks which proposal, makes no changes",
  "graph_assertions": {
    "both_tasks_still_incomplete": true
  },
  "safety_check": {
    "asks_for_clarification": true,
    "makes_no_changes": true
  },
  "judge_scenario": "User refers ambiguously to one of multiple tasks"
}
```

**Changes:**
- ✅ Removed "There are two proposals. Handle the ambiguity."
- ✅ Setup creates ambiguous scenario
- ✅ Safety check verifies no premature action

---

## Bulk Migration Script

To migrate all tests at once:

```python
#!/usr/bin/env python3
"""
Migrate test_cases.json to improved format.

Usage:
    python migrate_tests.py test_cases.json > test_cases_v2.json
"""

import json
import re
import sys

def remove_coaching_phrases(prompt):
    """Remove common coaching phrases from prompts."""
    # Remove coaching verbs
    prompt = re.sub(r'\. (Use|Follow|Apply|Persist) .*', '.', prompt)
    prompt = re.sub(r' (appropriately|correctly|properly|per the [^.]+)', '', prompt)

    # Remove meta-descriptions
    prompt = re.sub(r'The (user says|graph [^.]+)\. ', '', prompt)
    prompt = re.sub(r'\. (It|There|This) [^.]+\. ', '. ', prompt)

    # Clean up spacing
    prompt = re.sub(r'\s+', ' ', prompt).strip()

    return prompt

def migrate_test_case(test_case):
    """Migrate a single test case to improved format."""
    migrated = {
        "name": test_case["name"],
        "category": test_case["category"],
        "prompt": remove_coaching_phrases(test_case["prompt"]),
        "expected_behavior": test_case.get("expected_behavior", ""),
        "judge_scenario": f"User {test_case['category'].lower()} scenario"
    }

    # Add graph_assertions placeholder for Live MCP tests
    if test_case["category"] in ["Capture", "Update", "Delete"]:
        migrated["graph_assertions"] = {
            "TODO": "Add specific assertions for this test"
        }

    # Preserve expected_pass for negative controls
    if "expected_pass" in test_case:
        migrated["expected_pass"] = test_case["expected_pass"]

    # Preserve assistant_override for judge tests
    if "assistant_override" in test_case:
        migrated["assistant_override"] = test_case["assistant_override"]

    return migrated

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_tests.py test_cases.json", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        test_cases = json.load(f)

    migrated_cases = [migrate_test_case(tc) for tc in test_cases]

    print(json.dumps(migrated_cases, indent=2))

if __name__ == "__main__":
    main()
```

---

## Validation Checklist

After migration, verify each test:

- [ ] **Prompt is natural** - No coaching phrases remain
- [ ] **Setup extracted** - Meta-descriptions moved to setup section
- [ ] **Graph assertions added** - For Live MCP capture/update/delete tests
- [ ] **Success criteria simplified** - Outcomes only, no phrasing requirements
- [ ] **Judge scenario descriptive** - Provides context without directing
- [ ] **Safety checks explicit** - For delete/ambiguous cases
- [ ] **Must_not removed** - Redundant with SAFE dimension

---

## Testing the Migration

1. **Run original tests** - Capture baseline pass rate
2. **Run migrated tests** - Compare pass rate (should be similar or better)
3. **Compare failures** - New failures should reveal real bugs (not test brittleness)
4. **Validate graph assertions** - Ensure they catch "said but didn't do" bugs

---

## Summary

Migration improves tests by:

1. ✅ **Removing coaching** - Tests user behavior, not spec compliance
2. ✅ **Adding determinism** - Graph assertions catch real bugs
3. ✅ **Simplifying judge** - 3 binary questions reduce variability
4. ✅ **Natural prompts** - Realistic user utterances only

**Next step:** Implement graph_assertions.py and example_refactored_tests.py, then migrate test_cases.json incrementally.
