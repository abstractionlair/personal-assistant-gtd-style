"""
Graph State Assertions Framework

Provides deterministic verification of graph memory state for Live MCP tests.
Tests behavior (what happened) not phrasing (what was said).

Usage:
    graph = GraphStateAssertions(mcp_client)
    task_id = graph.assert_task_created("dentist")
    graph.assert_task_property(task_id, "isComplete", False)
"""

import re
from typing import Any, Dict, List, Optional


class GraphStateAssertions:
    """Deterministic assertions against graph memory state via MCP."""

    def __init__(self, mcp_client):
        """
        Initialize with MCP client.

        Args:
            mcp_client: Graph memory MCP client instance with tool access
        """
        self.client = mcp_client

    # === Task Assertions ===

    def assert_task_created(self, content_pattern: str) -> str:
        """
        Assert a task exists with content matching pattern.

        Args:
            content_pattern: Regex pattern to match against task content

        Returns:
            task_id: ID of the matched task (for chaining assertions)

        Raises:
            AssertionError: If no matching task found
        """
        tasks = self.client.query_nodes(type="Task")

        for task_id in tasks.get("node_ids", []):
            try:
                content = self.client.get_node_content(node_id=task_id)
                if re.search(content_pattern, content, re.IGNORECASE):
                    return task_id
            except Exception:
                # Skip tasks we can't read
                continue

        # Gather details for helpful error message
        task_contents = []
        for task_id in tasks.get("node_ids", [])[:5]:  # Show first 5
            try:
                content = self.client.get_node_content(node_id=task_id)
                task_contents.append(f"  - {content[:100]}")
            except Exception:
                pass

        tasks_summary = "\n".join(task_contents) if task_contents else "  (none)"

        raise AssertionError(
            f"No task found matching pattern: '{content_pattern}'\n"
            f"Found {len(tasks.get('node_ids', []))} total tasks:\n"
            f"{tasks_summary}"
        )

    def assert_task_property(
        self,
        task_id: str,
        prop_name: str,
        expected_value: Any
    ):
        """
        Assert task has property with expected value.

        Args:
            task_id: Task node ID
            prop_name: Property name (e.g., "isComplete")
            expected_value: Expected property value

        Raises:
            AssertionError: If property doesn't match
        """
        task = self.client.get_node(node_id=task_id)
        actual = task.get("properties", {}).get(prop_name)

        assert actual == expected_value, (
            f"Task {task_id} property '{prop_name}': "
            f"expected {expected_value!r}, got {actual!r}"
        )

    def assert_task_count(
        self,
        expected_count: int,
        **property_filters
    ):
        """
        Assert number of tasks matching filters.

        Args:
            expected_count: Expected number of matching tasks
            **property_filters: Property filters (e.g., isComplete=False)

        Raises:
            AssertionError: If count doesn't match
        """
        query_params = {"type": "Task"}
        if property_filters:
            query_params["properties"] = property_filters

        tasks = self.client.query_nodes(**query_params)
        actual = len(tasks.get("node_ids", []))

        assert actual == expected_count, (
            f"Expected {expected_count} tasks matching {property_filters}, "
            f"found {actual}"
        )

    def get_tasks_by_content(self, content_pattern: str) -> List[str]:
        """
        Get all task IDs matching content pattern.

        Args:
            content_pattern: Regex pattern to match

        Returns:
            List of matching task IDs
        """
        tasks = self.client.query_nodes(type="Task")
        matches = []

        for task_id in tasks.get("node_ids", []):
            try:
                content = self.client.get_node_content(node_id=task_id)
                if re.search(content_pattern, content, re.IGNORECASE):
                    matches.append(task_id)
            except Exception:
                continue

        return matches

    # === Connection Assertions ===

    def assert_connection_exists(
        self,
        from_id: str,
        to_id: str,
        conn_type: str = "DependsOn"
    ):
        """
        Assert connection exists between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            conn_type: Connection type (default "DependsOn")

        Raises:
            AssertionError: If connection doesn't exist
        """
        connections = self.client.query_connections(
            type=conn_type,
            from_node_id=from_id,
            to_node_id=to_id
        )

        conn_ids = connections.get("connection_ids", [])

        assert len(conn_ids) > 0, (
            f"No {conn_type} connection from {from_id} to {to_id}"
        )

    def assert_no_connections(
        self,
        node_id: str,
        direction: str = "both",
        conn_type: Optional[str] = None
    ):
        """
        Assert node has no connections in specified direction.

        Args:
            node_id: Node ID to check
            direction: "in", "out", or "both"
            conn_type: Optional connection type filter

        Raises:
            AssertionError: If connections exist
        """
        params = {
            "node_id": node_id,
            "direction": direction
        }
        if conn_type:
            params["connection_type"] = conn_type

        connected = self.client.get_connected_nodes(**params)
        node_ids = connected.get("node_ids", [])

        assert len(node_ids) == 0, (
            f"Expected no {direction} connections for {node_id}, "
            f"found {len(node_ids)}"
        )

    def assert_dependency_count(
        self,
        task_id: str,
        expected_count: int,
        direction: str = "out"
    ):
        """
        Assert number of dependencies for a task.

        Args:
            task_id: Task node ID
            expected_count: Expected number of dependencies
            direction: "in" for dependents, "out" for dependencies

        Raises:
            AssertionError: If count doesn't match
        """
        connected = self.client.get_connected_nodes(
            node_id=task_id,
            direction=direction,
            connection_type="DependsOn"
        )

        actual = len(connected.get("node_ids", []))

        assert actual == expected_count, (
            f"Task {task_id} expected {expected_count} {direction} dependencies, "
            f"found {actual}"
        )

    # === Context Assertions ===

    def assert_context_exists(self, context_pattern: str) -> str:
        """
        Assert context exists matching pattern.

        Args:
            context_pattern: Regex to match context content

        Returns:
            context_id: ID of matched context

        Raises:
            AssertionError: If context not found
        """
        contexts = self.client.query_nodes(type="Context")

        for ctx_id in contexts.get("node_ids", []):
            try:
                content = self.client.get_node_content(node_id=ctx_id)
                if re.search(context_pattern, content, re.IGNORECASE):
                    return ctx_id
            except Exception:
                continue

        raise AssertionError(
            f"No context found matching pattern: '{context_pattern}'"
        )

    def assert_context_available(
        self,
        context_pattern: str,
        expected: bool
    ):
        """
        Assert context availability status.

        Args:
            context_pattern: Regex to identify context
            expected: Expected isTrue value

        Raises:
            AssertionError: If availability doesn't match
        """
        ctx_id = self.assert_context_exists(context_pattern)
        ctx = self.client.get_node(node_id=ctx_id)
        actual = ctx.get("properties", {}).get("isTrue")

        assert actual == expected, (
            f"Context '{context_pattern}' isTrue: "
            f"expected {expected}, got {actual}"
        )

    # === State Assertions ===

    def assert_state_exists(self, state_pattern: str) -> str:
        """
        Assert state exists matching pattern.

        Args:
            state_pattern: Regex to match state content

        Returns:
            state_id: ID of matched state

        Raises:
            AssertionError: If state not found
        """
        states = self.client.query_nodes(type="State")

        for state_id in states.get("node_ids", []):
            try:
                content = self.client.get_node_content(node_id=state_id)
                if re.search(state_pattern, content, re.IGNORECASE):
                    return state_id
            except Exception:
                continue

        raise AssertionError(
            f"No state found matching pattern: '{state_pattern}'"
        )

    def assert_state_value(
        self,
        state_pattern: str,
        expected_is_true: bool
    ):
        """
        Assert state isTrue value.

        Args:
            state_pattern: Regex to identify state
            expected_is_true: Expected isTrue value

        Raises:
            AssertionError: If isTrue doesn't match
        """
        state_id = self.assert_state_exists(state_pattern)
        state = self.client.get_node(node_id=state_id)
        actual = state.get("properties", {}).get("isTrue")

        assert actual == expected_is_true, (
            f"State '{state_pattern}' isTrue: "
            f"expected {expected_is_true}, got {actual}"
        )

    # === Derived View Assertions ===

    def assert_is_project(self, task_id: str):
        """
        Assert task is a project (has outgoing dependencies).

        Args:
            task_id: Task node ID

        Raises:
            AssertionError: If task has no outgoing dependencies
        """
        deps = self.client.query_connections(
            type="DependsOn",
            from_node_id=task_id
        )

        conn_count = len(deps.get("connection_ids", []))

        assert conn_count > 0, (
            f"Task {task_id} is not a project "
            f"(has no outgoing dependencies)"
        )

    def assert_is_next_action(self, task_id: str):
        """
        Assert task qualifies as a next action.

        Checks:
        - Task is incomplete
        - All dependencies satisfied
        - Not dependent on UNSPECIFIED

        Args:
            task_id: Task node ID

        Raises:
            AssertionError: If task doesn't qualify as next action
        """
        task = self.client.get_node(node_id=task_id)

        # Must be incomplete
        is_complete = task.get("properties", {}).get("isComplete")
        assert not is_complete, (
            f"Task {task_id} is complete, not a next action"
        )

        # Check all dependencies satisfied
        deps = self.client.get_connected_nodes(
            node_id=task_id,
            direction="out",
            connection_type="DependsOn"
        )

        for dep_id in deps.get("node_ids", []):
            dep = self.client.get_node(node_id=dep_id)
            dep_type = dep.get("type")

            if dep_type == "Task":
                dep_complete = dep.get("properties", {}).get("isComplete")
                assert dep_complete, (
                    f"Task {task_id} depends on incomplete task {dep_id}, "
                    f"not actionable"
                )

            elif dep_type == "State":
                dep_true = dep.get("properties", {}).get("isTrue")
                assert dep_true, (
                    f"Task {task_id} depends on false state {dep_id}, "
                    f"not actionable"
                )

            elif dep_type == "Context":
                dep_available = dep.get("properties", {}).get("isTrue")
                assert dep_available, (
                    f"Task {task_id} depends on unavailable context {dep_id}, "
                    f"not actionable"
                )

            elif dep_type == "UNSPECIFIED":
                raise AssertionError(
                    f"Task {task_id} depends on UNSPECIFIED, "
                    f"never actionable"
                )

    def assert_is_waiting_for(self, task_id: str):
        """
        Assert task is in Waiting For list (delegated to external party).

        Args:
            task_id: Task node ID

        Raises:
            AssertionError: If task not delegated or complete
        """
        task = self.client.get_node(node_id=task_id)
        props = task.get("properties", {})

        # Must be incomplete
        assert not props.get("isComplete"), (
            f"Task {task_id} is complete, not in Waiting For"
        )

        # Must have external responsible party
        responsible = props.get("responsibleParty")
        assert responsible and responsible != "me", (
            f"Task {task_id} responsibleParty is '{responsible}', "
            f"not in Waiting For (must be external party, not 'me')"
        )

    # === Deletion Verification ===

    def assert_node_deleted(self, node_id: str):
        """
        Assert node no longer exists.

        Args:
            node_id: Node ID that should be deleted

        Raises:
            AssertionError: If node still exists
        """
        try:
            self.client.get_node(node_id=node_id)
            # If we get here, node exists (should have raised)
            raise AssertionError(f"Node {node_id} still exists (should be deleted)")
        except Exception as e:
            # Expected: node not found
            if "not found" in str(e).lower():
                return  # Success
            # Unexpected error
            raise

    def assert_node_exists(self, node_id: str):
        """
        Assert node still exists.

        Args:
            node_id: Node ID that should exist

        Raises:
            AssertionError: If node doesn't exist
        """
        try:
            self.client.get_node(node_id=node_id)
        except Exception as e:
            raise AssertionError(
                f"Node {node_id} doesn't exist (should exist): {e}"
            )

    # === Utility Methods ===

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all task nodes with their properties and content."""
        tasks = self.client.query_nodes(type="Task")
        result = []

        for task_id in tasks.get("node_ids", []):
            try:
                task = self.client.get_node(node_id=task_id)
                content = self.client.get_node_content(node_id=task_id)
                result.append({
                    "id": task_id,
                    "properties": task.get("properties", {}),
                    "content": content
                })
            except Exception:
                continue

        return result

    def debug_graph_state(self) -> str:
        """
        Generate debug summary of current graph state.

        Returns:
            Formatted string with graph statistics
        """
        lines = ["=== Graph State Debug ==="]

        # Count nodes by type
        for node_type in ["Task", "State", "Context", "UNSPECIFIED"]:
            nodes = self.client.query_nodes(type=node_type)
            count = len(nodes.get("node_ids", []))
            lines.append(f"{node_type} nodes: {count}")

        # Count connections
        connections = self.client.query_connections(type="DependsOn")
        conn_count = len(connections.get("connection_ids", []))
        lines.append(f"DependsOn connections: {conn_count}")

        # Show incomplete tasks
        incomplete = self.client.query_nodes(
            type="Task",
            properties={"isComplete": False}
        )
        lines.append(f"Incomplete tasks: {len(incomplete.get('node_ids', []))}")

        return "\n".join(lines)
