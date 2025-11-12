"""Placeholder CLI bridge for invoking MCP server tools via subprocess."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


class McpCliBridge:
    """Runs MCP tool commands by shelling out to a CLI helper.

    The real implementation will likely:
      1. Launch the MCP server (via GraphMemoryBridge lifecycle manager).
      2. Call a CLI helper (e.g., `node cli.js call --tool create_node --input '{...}'`).
      3. Capture stdout/stderr, parse JSON result, propagate errors, and emit logs.
    """

    def __init__(self, cli_path: Path, env: Mapping[str, str] | None = None, timeout: float = 60.0) -> None:
        self.cli_path = cli_path
        self.env = dict(env or {})
        self.timeout = timeout
        if not self.cli_path.exists():
            raise FileNotFoundError(f"MCP tool runner not found: {self.cli_path}")

    def run_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        command = self._build_command(tool_name, arguments)
        env = os.environ.copy()
        env.update(self.env)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - integration path
            raise RuntimeError(f"MCP CLI bridge timed out calling {tool_name}") from exc

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            raise RuntimeError(
                f"MCP CLI bridge failed for {tool_name}: code={result.returncode} stderr={stderr}"
            )
        if not stdout:
            raise RuntimeError(f"MCP CLI bridge produced no output for {tool_name}")
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse CLI output for {tool_name}: {stdout}"
            ) from exc
        if not parsed.get("ok"):
            raise RuntimeError(f"CLI reported error for {tool_name}: {parsed.get('error')}")
        return parsed.get("result")

    def _build_command(self, tool_name: str, arguments: Mapping[str, Any]) -> Sequence[str]:
        return [
            "node",
            str(self.cli_path),
            "call",
            tool_name,
            json.dumps(arguments),
        ]


__all__ = ["McpCliBridge"]
