"""Bridge helpers connecting the tool router to MCP server processes."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from pathlib import Path
from typing import Callable, Dict, Mapping, Any, Optional, TYPE_CHECKING

from .client import GraphMemoryClient
from .manager import McpLifecycleManager, McpServerSpec, default_graph_memory_spec
from .cli_bridge import McpCliBridge
from .mcp_client_stub import McpClientStub

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from mcp_tool_gateway import GatewayClient


@dataclass(slots=True)
class GraphMemoryBridge:
    """Placeholder bridge that will eventually invoke MCP commands."""

    data_dir: Path
    log_dir: Path
    lifecycle_manager: Optional[McpLifecycleManager] = None
    client: Optional[GraphMemoryClient] = None
    executor: Optional[Callable[[str, Mapping[str, Any]], Any]] = None
    stub_responses: Dict[str, Any] = None  # type: ignore[assignment]
    last_calls: list[dict[str, Any]] = None  # type: ignore[assignment]
    cli_bridge: Optional[McpCliBridge] = None
    gateway_base_url: Optional[str] = None
    gateway_client: Optional["GatewayClient"] = None

    def start(self) -> None:
        data_dir = self.data_dir
        log_dir = self.log_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "graph-memory.log"
        if not self.gateway_base_url:
            spec: McpServerSpec = default_graph_memory_spec(data_dir=data_dir, log_path=log_path)
            self.lifecycle_manager = McpLifecycleManager([spec])
            self.lifecycle_manager.start_all()
        # TODO (Transport Milestone):
        #   1. Ensure `src/graph-memory-core/mcp` is built (`npm install && npm run build`).
        #   2. Launch `node dist/index.js` via McpLifecycleManager (one per run/test).
        #   3. Stream stdout/stderr to log files for debugging/failures.
        #   4. Initialize `McpCliBridge` (or JSON-RPC client) pointing at a helper script
        #      that can execute tools against the running server.
        #   5. Surface MCP logs through a read-only tool (judge/interrogator use).
        # For now we stay in stub mode so other harness pieces can be developed in parallel.
        self.client = GraphMemoryClient()
        tool_runner = Path(__file__).resolve().parent / "tool_runner.mjs"
        if self.executor is None and not self.stub_responses:
            if self.gateway_base_url:
                # Prefer the shared Python client from mcp-tool-gateway when a base URL is configured.
                self._init_gateway_client()
                self.executor = self._gateway_client_executor
            else:
                self.cli_bridge = McpCliBridge(
                    cli_path=tool_runner,
                    env={
                        "BASE_PATH": str(data_dir),
                        "MCP_CALL_LOG": str(log_path),
                    },
                )
                # TODO: replace CLI bridge with stdio client once MCP transport is wired.
                self.executor = self.cli_bridge.run_tool
        if self.executor is None:
            self.executor = self._stub_executor
        self.client.executor = self._execute
        self.last_calls = []

    def stop(self) -> None:
        if self.lifecycle_manager:
            self.lifecycle_manager.stop_all()
            self.lifecycle_manager = None
        self.client = None

    def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        if not self.client:
            raise RuntimeError("GraphMemoryBridge not started")
        return self._execute(tool_name, arguments)

    def set_stub_response(self, tool_name: str, response: Any) -> None:
        if self.stub_responses is None:
            self.stub_responses = {}
        self.stub_responses[tool_name] = response

    def _execute(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        if not self.executor:
            raise RuntimeError("GraphMemoryBridge executor missing")
        # TODO: When real transport is wired, this will call out to the MCP server via
        # JSON-RPC or a local CLI bridge, capture tool results/errors, and stream logs.
        result = self.executor(tool_name, arguments)
        if self.last_calls is not None:
            self.last_calls.append(
                {
                    "timestamp": time.time(),
                    "tool": tool_name,
                    "arguments": json.loads(json.dumps(arguments)),
                    "result": result,
                }
            )
        return result

    def use_gateway(self, base_url: str) -> None:
        self.gateway_base_url = base_url

    def _init_gateway_client(self) -> None:
        """Initialize GatewayClient from the external mcp-tool-gateway repo.

        We import the client dynamically so the harness can run without requiring
        the gateway package to be installed globally. This expects the cloned
        gateway repo at external/mcp-tool-gateway/python.
        """
        if self.gateway_client is not None:
            return
        if not self.gateway_base_url:
            raise RuntimeError("Gateway base URL not configured")

        # Add external/mcp-tool-gateway/python to sys.path for this process.
        import sys
        from importlib import import_module

        repo_root = Path(__file__).resolve().parents[3]
        gateway_python = repo_root / "external" / "mcp-tool-gateway" / "python"
        if not gateway_python.is_dir():
            raise RuntimeError(
                f"mcp-tool-gateway Python client not found at {gateway_python}. "
                "Ensure the gateway repo is cloned under external/mcp-tool-gateway."
            )
        gateway_path = str(gateway_python)
        if gateway_path not in sys.path:
            sys.path.insert(0, gateway_path)

        try:
            module = import_module("mcp_tool_gateway")
        except ImportError as exc:  # pragma: no cover - import failure path
            raise RuntimeError(
                "Unable to import mcp_tool_gateway. "
                "Verify the gateway Python package is available."
            ) from exc

        GatewayClientCls = getattr(module, "GatewayClient")
        self.gateway_client = GatewayClientCls(self.gateway_base_url.rstrip("/"))

    def _gateway_client_executor(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        if not self.gateway_client:
            raise RuntimeError("Gateway client not initialized")
        # Graph memory server is currently bootstrapped as "gtd-graph-memory"
        # inside the gateway. Tool names coming from the router are bare
        # ("create_node"); internal helpers may use canonical names
        # ("mcp__gtd-graph-memory__create_node"). Normalize to bare names and
        # derive the server from the canonical name when present.
        server = "gtd-graph-memory"
        if tool_name.startswith("mcp__"):
            parts = tool_name.split("__", 2)
            if len(parts) == 3:
                server = parts[1] or server
                tool = parts[2]
            else:
                tool = tool_name
        else:
            tool = tool_name
        return self.gateway_client.call_tool(server, tool, dict(arguments))

    def _stub_executor(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        """Return canned responses. Temporary until real transport is wired."""

        if self.stub_responses and tool_name in self.stub_responses:
            return self.stub_responses[tool_name]
        raise NotImplementedError(
            f"GraphMemoryBridge stub has no response for '{tool_name}'. Arguments: {arguments}"
        )


__all__ = ["GraphMemoryBridge"]
