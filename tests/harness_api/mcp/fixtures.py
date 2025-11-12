from __future__ import annotations

from typing import Any, Mapping

from .bridge import GraphMemoryBridge


def ensure_ontology(bridge: GraphMemoryBridge) -> None:
    """Ensure the graph ontology exists; create it if missing."""
    try:
        bridge.call_tool("mcp__gtd-graph-memory__get_ontology", {})
        return
    except Exception:
        pass
    create_req: Mapping[str, Any] = {
        "node_types": ["Task", "Context", "State", "UNSPECIFIED"],
        "connection_types": [
            {
                "name": "DependsOn",
                "from_types": ["Task"],
                "to_types": ["Task"],
            },
            {"name": "DependsOn", "from_types": ["Task"], "to_types": ["Context"]},
            {"name": "DependsOn", "from_types": ["Task"], "to_types": ["State"]},
            {"name": "DependsOn", "from_types": ["Task"], "to_types": ["UNSPECIFIED"]},
        ],
    }
    bridge.call_tool("mcp__gtd-graph-memory__create_ontology", create_req)


def clean_graph(bridge: GraphMemoryBridge) -> None:
    """Delete all nodes in the graph to reset state."""
    # Query all nodes; the server supports optional filters so empty means all
    res = bridge.call_tool("mcp__gtd-graph-memory__query_nodes", {})
    node_ids = []
    if isinstance(res, dict):
        node_ids = list(res.get("node_ids") or res.get("result", {}).get("node_ids", []) or [])
    for node_id in node_ids:
        try:
            bridge.call_tool("mcp__gtd-graph-memory__delete_node", {"node_id": node_id})
        except Exception:
            # Best-effort cleanup
            pass

