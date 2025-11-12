"""Bridge helpers connecting the tool router to MCP server processes."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Dict, Mapping, Any, Optional

from .client import GraphMemoryClient
from .manager import McpLifecycleManager, McpServerSpec, default_graph_memory_spec
from .cli_bridge import McpCliBridge
from .mcp_client_stub import McpClientStub


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
                self.executor = self._gateway_http
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

    def _gateway_http(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        import urllib.request
        import urllib.error
        import os
        import json as _json
        if not self.gateway_base_url:
            raise RuntimeError("Gateway base URL not configured")
        url = self.gateway_base_url.rstrip('/') + '/call_tool'
        data = {
            # Prefer canonical name (mcp__server__tool), gateway can parse it
            "tool": tool_name,
            # For non-canonical fall back to default server used in this project
            "server": "gtd-graph-memory",
            "arguments": dict(arguments),
        }
        req = urllib.request.Request(url, data=_json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = _json.loads(resp.read().decode('utf-8'))
                if 'error' in payload:
                    raise RuntimeError(payload['error'])
                return payload.get('result')
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Gateway HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}") from e

    def _stub_executor(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        """Return canned responses. Temporary until real transport is wired."""

        if self.stub_responses and tool_name in self.stub_responses:
            return self.stub_responses[tool_name]
        raise NotImplementedError(
            f"GraphMemoryBridge stub has no response for '{tool_name}'. Arguments: {arguments}"
        )


__all__ = ["GraphMemoryBridge"]
