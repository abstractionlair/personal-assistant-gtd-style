"""MCP client abstractions for bridging canonical tools to real servers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Callable


class McpToolClient(ABC):
    """Abstract client capable of invoking tools on an MCP server."""

    server_name: str

    @abstractmethod
    def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        """Invoke a tool and return the raw JSON result."""


class GraphMemoryClient(McpToolClient):
    server_name = "gtd-graph-memory"

    def __init__(self) -> None:
        self.executor: Callable[[str, Mapping[str, Any]], Any] | None = None

    def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        if not self.executor:
            raise RuntimeError("GraphMemoryClient executor not configured")
        return self.executor(tool_name, arguments)


__all__ = ["McpToolClient", "GraphMemoryClient"]
