"""Canonical tool definitions shared across providers."""

from __future__ import annotations

from typing import Tuple

from ..adapters.base import ToolDefinition


# NOTE: Input schemas are currently simplified placeholders (real schemas live in
# src/graph-memory-core/mcp). We'll hydrate them from source or the running MCP
# server in a future milestone to ensure perfect parity.
_SIMPLE_OBJECT_SCHEMA = {"type": "object", "properties": {}, "additionalProperties": True}

_CREATE_NODE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "content": {"type": "string"},
        "encoding": {"type": "string", "enum": ["utf-8", "base64"]},
        "format": {"type": "string"},
        "properties": {"type": "object", "additionalProperties": {"type": ["string", "number", "boolean"]}},
    },
    "required": ["type", "content", "encoding", "format"],
    "additionalProperties": False,
}

_UPDATE_NODE_SCHEMA = {
    "type": "object",
    "properties": {
        "node_id": {"type": "string"},
        "properties": {"type": "object", "additionalProperties": {"type": ["string", "number", "boolean"]}},
        "content": {"type": "string"},
        "encoding": {"type": "string", "enum": ["utf-8", "base64"]},
        "format": {"type": "string"},
    },
    "required": ["node_id"],
    "additionalProperties": False,
}

_DELETE_NODE_SCHEMA = {
    "type": "object",
    "properties": {"node_id": {"type": "string"}},
    "required": ["node_id"],
    "additionalProperties": False,
}

_CREATE_CONNECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "from_node_id": {"type": "string"},
        "to_node_id": {"type": "string"},
        "properties": {"type": "object", "additionalProperties": {"type": ["string", "number", "boolean"]}},
        "content": {"type": "string"},
        "format": {"type": "string"},
    },
    "required": ["type", "from_node_id", "to_node_id"],
    "additionalProperties": False,
}

_QUERY_NODES_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "properties": {"type": "object", "additionalProperties": {"type": ["string", "number", "boolean"]}},
    },
    "additionalProperties": False,
}


GRAPH_MEMORY_TOOLS: Tuple[ToolDefinition, ...] = (
    ToolDefinition(
        name="mcp__gtd-graph-memory__create_node",
        description="Create a GTD node (Task, Context, State, or UNSPECIFIED).",
        input_schema=_CREATE_NODE_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__get_node",
        description="Retrieve node metadata by ID.",
        input_schema=_DELETE_NODE_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__get_node_content",
        description="Retrieve node content by ID.",
        input_schema=_DELETE_NODE_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__update_node",
        description="Update node properties or content.",
        input_schema=_UPDATE_NODE_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__delete_node",
        description="Delete a node and cascade.",
        input_schema=_DELETE_NODE_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__create_connection",
        description="Create a DependsOn connection.",
        input_schema=_CREATE_CONNECTION_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__get_connection",
        description="Retrieve connection metadata by ID.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__update_connection",
        description="Update connection properties/content.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__delete_connection",
        description="Delete a connection without affecting nodes.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__query_nodes",
        description="Query nodes by type/properties.",
        input_schema=_QUERY_NODES_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__query_connections",
        description="Query connections by direction/type.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__get_connected_nodes",
        description="List connected nodes (dependents/dependencies).",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__search_content",
        description="Search nodes by content text.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__validate_connection",
        description="Validate allowed connection types.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__create_ontology",
        description="Initialize ontology definitions.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__add_node_type",
        description="Add a new node type to ontology.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__add_connection_type",
        description="Add a new connection type to ontology.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__get_ontology",
        description="Retrieve ontology definition.",
        input_schema={"type": "object", "properties": {}},
    ),
    ToolDefinition(
        name="mcp__gtd-graph-memory__ensure_singleton_node",
        description="Ensure/get singleton node for a type.",
        input_schema=_SIMPLE_OBJECT_SCHEMA,
    ),
)


__all__ = ["GRAPH_MEMORY_TOOLS"]
