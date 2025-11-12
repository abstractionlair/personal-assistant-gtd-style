"""Tool exposure policies per role.

Defines which canonical tools are exposed to which roles.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from ..adapters.base import ToolDefinition


# Canonical tool names (prefix mcp__gtd-graph-memory__)
READ_ONLY = {
    "mcp__gtd-graph-memory__get_node",
    "mcp__gtd-graph-memory__get_node_content",
    "mcp__gtd-graph-memory__query_nodes",
    "mcp__gtd-graph-memory__query_connections",
    "mcp__gtd-graph-memory__get_connected_nodes",
    "mcp__gtd-graph-memory__search_content",
    "mcp__gtd-graph-memory__validate_connection",
    "mcp__gtd-graph-memory__get_ontology",
}


def filter_tools_for_role(role: str, tools: Iterable[ToolDefinition]) -> Tuple[ToolDefinition, ...]:
    """Return the subset of tools a role may use.

    - assistant: all tools
    - judge: read-only
    - interrogator: read-only
    - user_proxy: none (return empty)
    """

    if role == "assistant":
        return tuple(tools)
    if role in ("judge", "interrogator"):
        return tuple(t for t in tools if t.name in READ_ONLY)
    if role == "user_proxy":
        return tuple()
    return tuple(tools)


__all__ = ["filter_tools_for_role", "READ_ONLY"]

