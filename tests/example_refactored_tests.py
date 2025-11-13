#!/usr/bin/env python3
"""
Example Refactored Tests Using Three-Tier Strategy

Demonstrates:
1. Tier 1: Graph state assertions (deterministic)
2. Tier 2: Simplified 3-question judge (quality gate)
3. Natural test prompts (no coaching phrases)

Run with:
    python tests/example_refactored_tests.py --suite assistant --mode real
"""

from graph_assertions import GraphStateAssertions
import pytest


# === Test Fixtures ===

@pytest.fixture
def mcp_client():
    """Provide MCP client for Live MCP tests."""
    # TODO: Initialize real MCP client
    # For now, this is a placeholder
    raise NotImplementedError("Implement MCP client initialization")


@pytest.fixture
def graph(mcp_client):
    """Provide graph assertions helper."""
    return GraphStateAssertions(mcp_client)


@pytest.fixture
def clean_graph(mcp_client):
    """Provide clean graph state for each test."""
    # TODO: Implement graph cleanup/reset
    # For tests that need empty starting state
    pass


# === Helper Functions ===

def run_assistant(prompt: str, mode: str = "live_mcp") -> str:
    """
    Run assistant with given prompt.

    Args:
        prompt: User's natural language request
        mode: "live_mcp" or "simulation"

    Returns:
        Assistant's response text
    """
    # TODO: Implement assistant invocation
    raise NotImplementedError("Implement assistant runner")


def run_simple_judge(
    user_prompt: str,
    assistant_response: str,
    scenario_description: str,
    mode: str = "live_mcp"
) -> dict:
    """
    Run simplified 3-question judge.

    Returns:
        {
            "effective": bool,
            "safe": bool,
            "clear": bool,
            "reasoning": str,
            "pass": bool
        }
    """
    # TODO: Implement simplified judge
    raise NotImplementedError("Implement simplified judge")


# === Example Test 1: Simple Task Capture ===

def test_capture_simple_task_refactored(graph, clean_graph):
    """
    Capture simple task - demonstrates natural prompt + graph assertions.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Removed coaching phrase ("Persist this task appropriately")
    - ✅ Added graph state verification (Tier 1)
    - ✅ Simplified judge to 3 questions (Tier 2)
    - ✅ Natural user utterance only
    """

    # Arrange
    prompt = "I need to call the dentist tomorrow to schedule a cleaning."
    # ^^ Natural prompt - no mention of "persist", "graph", or "appropriately"

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Graph state (deterministic verification)
    task_id = graph.assert_task_created("dentist.*cleaning")
    graph.assert_task_property(task_id, "isComplete", False)
    graph.assert_no_connections(task_id, direction="out")
    graph.assert_task_count(1, isComplete=False)

    # Assert Tier 2: Conversation quality (simplified judge)
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User wants to capture a simple task",
        mode="live_mcp"
    )

    assert judgment["effective"], (
        f"Failed EFFECTIVE dimension: {judgment['reasoning']}"
    )
    assert judgment["safe"], (
        f"Failed SAFE dimension: {judgment['reasoning']}"
    )
    assert judgment["clear"], (
        f"Failed CLEAR dimension: {judgment['reasoning']}"
    )

    # Note: We don't check for specific phrases like "captured task"
    # That's brittle and teaches to the test.
    # Graph assertions + judge quality check are sufficient.


# === Example Test 2: Task with Context ===

def test_capture_task_with_context_refactored(graph, clean_graph):
    """
    Capture task with explicit context mention.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Removed coaching ("Use contexts properly when persisting")
    - ✅ Added graph verification for context creation and linkage
    - ✅ Natural prompt only
    """

    # Arrange
    prompt = "Log a reminder to print the quarterly packets when I'm at the office."
    # ^^ Natural - user just states what they want and where

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Graph state
    task_id = graph.assert_task_created("quarterly packets")
    graph.assert_task_property(task_id, "isComplete", False)

    # Context should exist (created or reused)
    context_id = graph.assert_context_exists("office")
    graph.assert_context_available("office", expected=True)

    # Task should depend on context
    graph.assert_connection_exists(
        from_id=task_id,
        to_id=context_id,
        conn_type="DependsOn"
    )

    # Assert Tier 2: Quality
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User wants task associated with specific location",
        mode="live_mcp"
    )

    assert judgment["pass"], f"Quality check failed: {judgment['reasoning']}"


# === Example Test 3: Task with Dependency ===

def test_capture_task_with_dependency_refactored(graph, clean_graph):
    """
    Capture dependent tasks.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Removed coaching ("Capture the dependent work correctly")
    - ✅ Natural phrasing
    - ✅ Graph verification of both tasks and connection
    """

    # Arrange
    prompt = "I need to send the board update, but only after I finish the financial summary."
    # ^^ Natural dependency expression

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Both tasks created
    board_task_id = graph.assert_task_created("board update")
    summary_task_id = graph.assert_task_created("financial summary")

    # Both incomplete
    graph.assert_task_property(board_task_id, "isComplete", False)
    graph.assert_task_property(summary_task_id, "isComplete", False)

    # Correct dependency direction: board depends on summary
    graph.assert_connection_exists(
        from_id=board_task_id,
        to_id=summary_task_id,
        conn_type="DependsOn"
    )

    # Board task is now a project (has outgoing dependency)
    graph.assert_is_project(board_task_id)

    # Summary task is actionable (no dependencies)
    graph.assert_is_next_action(summary_task_id)

    # Board task is NOT actionable (depends on incomplete summary)
    with pytest.raises(AssertionError, match="not actionable"):
        graph.assert_is_next_action(board_task_id)

    # Assert Tier 2: Quality
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User describes sequential work dependency",
        mode="live_mcp"
    )

    assert judgment["pass"], f"Quality check failed: {judgment['reasoning']}"


# === Example Test 4: Duplicate Detection ===

def test_capture_duplicate_detection_refactored(graph, mcp_client):
    """
    Duplicate detection without coaching the assistant.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Removed meta-instruction ("The graph already contains a very similar task")
    - ✅ Removed coaching ("Follow the spec's duplicate detection guidance")
    - ✅ Setup creates existing task silently
    - ✅ Tests for correct behavior (asks user) not specific phrasing
    """

    # Arrange: Create existing similar task
    existing_task_id = mcp_client.create_node(
        type="Task",
        content="Complete vendor contract review and signatures",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    # User doesn't know about existing task
    prompt = "Add a task to finalize the vendor contract."
    # ^^ Natural - no mention of duplicate or graph state

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: No new task created yet (waiting for user decision)
    graph.assert_task_count(1, isComplete=False)  # Only existing task

    # Assert Tier 2: Quality with emphasis on SAFE dimension
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User mentions task similar to existing one",
        mode="live_mcp"
    )

    # EFFECTIVE: Should recognize similarity and ask
    assert judgment["effective"], (
        f"Should detect similarity: {judgment['reasoning']}"
    )

    # SAFE: Should ask before creating duplicate
    assert judgment["safe"], (
        f"Should ask user decision before creating: {judgment['reasoning']}"
    )

    # CLEAR: User should understand the question
    assert judgment["clear"], (
        f"Duplicate question unclear: {judgment['reasoning']}"
    )

    # Additional check: Response should mention existing task
    # (Not brittle string matching, just verification question was asked)
    assert "contract" in response.lower(), (
        "Should mention existing task in question to user"
    )


# === Example Test 5: Delete with Dependency Warning ===

def test_delete_with_dependency_warning_refactored(graph, mcp_client):
    """
    Delete request should warn and wait for confirmation.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Removed meta-instruction ("It still has dependencies")
    - ✅ Removed coaching ("Follow the warning protocol")
    - ✅ Setup creates graph state silently
    - ✅ Verifies SAFE dimension through judge
    - ✅ Verifies nothing deleted through graph assertions
    """

    # Arrange: Create task with dependent
    checklist_id = mcp_client.create_node(
        type="Task",
        content="Onboarding checklist",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    handbook_id = mcp_client.create_node(
        type="Task",
        content="Employee handbook revision",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    # Handbook depends on checklist
    mcp_client.create_connection(
        type="DependsOn",
        from_node_id=handbook_id,
        to_node_id=checklist_id
    )

    # User doesn't know about dependency
    prompt = "Delete the old onboarding checklist."
    # ^^ Natural delete request - no mention of dependencies

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Nothing deleted yet (waiting for confirmation)
    graph.assert_node_exists(checklist_id)
    graph.assert_node_exists(handbook_id)
    graph.assert_task_count(2, isComplete=False)

    # Assert Tier 2: Quality with emphasis on SAFE
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User wants to delete task that others depend on",
        mode="live_mcp"
    )

    # SAFE is critical for delete operations
    assert judgment["safe"], (
        f"Should require confirmation before delete: {judgment['reasoning']}"
    )

    # CLEAR: User should understand what's being asked
    assert judgment["clear"], (
        f"Warning message unclear: {judgment['reasoning']}"
    )

    # Response should mention dependent task
    assert "handbook" in response.lower(), (
        "Should mention dependent task in warning"
    )


# === Example Test 6: Cascade Delete (Follow-up) ===

def test_delete_cascade_after_confirmation_refactored(graph, mcp_client):
    """
    After warning, user confirms cascade delete.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Tests realistic follow-up conversation
    - ✅ Verifies actual deletion through graph state
    - ✅ No "teaching to test" phrases
    """

    # Arrange: Create task with dependent
    checklist_id = mcp_client.create_node(
        type="Task",
        content="Onboarding checklist",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    handbook_id = mcp_client.create_node(
        type="Task",
        content="Employee handbook revision",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    mcp_client.create_connection(
        type="DependsOn",
        from_node_id=handbook_id,
        to_node_id=checklist_id
    )

    # First interaction: Delete request -> Warning
    prompt1 = "Delete the old onboarding checklist."
    response1 = run_assistant(prompt1, mode="live_mcp")

    # User confirms after seeing warning
    prompt2 = "Yes, go ahead and remove it even if it deletes the subtasks."
    # ^^ Natural confirmation

    # Act
    response2 = run_assistant(prompt2, mode="live_mcp")

    # Assert Tier 1: Checklist deleted (at minimum)
    graph.assert_node_deleted(checklist_id)

    # Depending on cascade behavior:
    # - Option A: Only checklist deleted, handbook has broken dependency
    # - Option B: Both deleted (cascade)
    # Test for whatever the spec requires

    # Assert Tier 2: Quality
    judgment = run_simple_judge(
        user_prompt=prompt2,
        assistant_response=response2,
        scenario_description="User confirms deletion after warning",
        mode="live_mcp"
    )

    assert judgment["effective"], (
        f"Should complete deletion: {judgment['reasoning']}"
    )

    assert judgment["clear"], (
        f"Confirmation unclear: {judgment['reasoning']}"
    )


# === Example Test 7: Empty Query Results ===

def test_query_empty_results_refactored(graph, clean_graph):
    """
    Query with no results should be handled gracefully.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Natural query ("Any next actions for @studio?")
    - ✅ Tests helpful response, not specific phrasing
    - ✅ Graph verification of empty state
    """

    # Arrange: Empty graph (no tasks exist)
    graph.assert_task_count(0)

    prompt = "What should I work on next?"
    # ^^ Natural query

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Still no tasks
    graph.assert_task_count(0)

    # Assert Tier 2: Quality
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User queries next actions when none exist",
        mode="live_mcp"
    )

    # EFFECTIVE: Should handle empty gracefully
    assert judgment["effective"], (
        f"Should handle empty results: {judgment['reasoning']}"
    )

    # CLEAR: User should understand there's nothing to do
    assert judgment["clear"], (
        f"Empty result explanation unclear: {judgment['reasoning']}"
    )

    # Don't check for exact phrase "No next actions available"
    # That's brittle. Judge evaluation is sufficient.


# === Example Test 8: Ambiguous Reference ===

def test_query_ambiguous_reference_refactored(graph, mcp_client):
    """
    Ambiguous task reference should trigger clarification.

    IMPROVEMENTS FROM ORIGINAL:
    - ✅ Setup creates ambiguity silently
    - ✅ Natural user utterance
    - ✅ Tests for safe behavior (asks) not exact phrasing
    """

    # Arrange: Create two proposals
    proposal1_id = mcp_client.create_node(
        type="Task",
        content="Client proposal for Q4 campaign",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    proposal2_id = mcp_client.create_node(
        type="Task",
        content="Internal proposal for new hiring process",
        encoding="utf-8",
        format="markdown",
        properties={"isComplete": False}
    )["node_id"]

    # User refers ambiguously
    prompt = "Mark the proposal done."
    # ^^ Ambiguous - which proposal?

    # Act
    response = run_assistant(prompt, mode="live_mcp")

    # Assert Tier 1: Neither marked complete yet
    graph.assert_task_property(proposal1_id, "isComplete", False)
    graph.assert_task_property(proposal2_id, "isComplete", False)

    # Assert Tier 2: Quality with emphasis on SAFE
    judgment = run_simple_judge(
        user_prompt=prompt,
        assistant_response=response,
        scenario_description="User refers ambiguously to one of multiple tasks",
        mode="live_mcp"
    )

    # SAFE: Should ask for clarification, not guess
    assert judgment["safe"], (
        f"Should ask which proposal: {judgment['reasoning']}"
    )

    # CLEAR: Clarification question should be understandable
    assert judgment["clear"], (
        f"Clarification unclear: {judgment['reasoning']}"
    )


# === Running Tests ===

if __name__ == "__main__":
    """
    Run example tests.

    Usage:
        python example_refactored_tests.py
    """
    print("Example refactored tests demonstrating three-tier strategy")
    print("\nTo run with pytest:")
    print("  pytest example_refactored_tests.py -v")
    print("\nTo run with test harness:")
    print("  python tests/test_conversational_layer.py --suite assistant --mode real")
