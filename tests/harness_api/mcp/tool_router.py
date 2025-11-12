"""Tool routing interface that maps canonical tool names to MCP executions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Callable

from ..adapters.base import ToolDefinition
from .client import McpToolClient
from .tool_definitions import GRAPH_MEMORY_TOOLS


@dataclass(slots=True)
class ToolExecutionResult:
    name: str
    output: Any


class ToolRouter:
    """Dispatches tool calls to registered executors."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable[[Mapping[str, Any]], Any]] = {}
        self.register_many(GRAPH_MEMORY_TOOLS)

    def register(self, definition: ToolDefinition, executor: Callable[[Mapping[str, Any]], Any] | None = None) -> None:
        self._tools[definition.name] = definition
        if executor:
            self._executors[definition.name] = executor

    def register_many(
        self,
        definitions: Iterable[ToolDefinition],
        executor: Callable[[Mapping[str, Any]], Any] | None = None,
    ) -> None:
        for item in definitions:
            self.register(item, executor)

    def attach_executor(self, name: str, executor: Callable[[Mapping[str, Any]], Any]) -> None:
        self._executors[name] = executor

    def attach_mcp_client(self, client: McpToolClient) -> None:
        """Attach an MCP client so canonical tool names invoke the server."""

        for definition in self._tools.values():
            server_name, tool_name = _split_canonical_name(definition.name)
            if server_name != client.server_name:
                continue
            self.attach_executor(
                definition.name,
                _build_executor(client, tool_name),
            )

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._tools.values())

    def execute(self, name: str, arguments: Mapping[str, Any]) -> ToolExecutionResult:
        executor = self._executors.get(name)
        if executor is None:
            raise RuntimeError(f"No executor registered for tool '{name}'")
        output = executor(arguments)
        return ToolExecutionResult(name=name, output=output)


__all__ = ["ToolRouter", "ToolExecutionResult"]


def _split_canonical_name(name: str) -> tuple[str, str]:
    parts = name.split("__", 2)
    if len(parts) != 3 or parts[0] != "mcp":
        raise ValueError(f"Invalid canonical tool name: {name}")
    return parts[1], parts[2]


def _build_executor(client: McpToolClient, tool_name: str) -> Callable[[Mapping[str, Any]], Any]:
    def _executor(arguments: Mapping[str, Any]) -> Any:
        return client.call_tool(tool_name, arguments)

    return _executor
