"""Minimal MCP stdio client to communicate with running Node server."""

from __future__ import annotations

import json
import threading
from typing import Any, Mapping, Optional


class McpStdioClient:
    def __init__(self, process) -> None:
        self.process = process
        self._lock = threading.Lock()
        self._counter = 0
        self._responses: dict[int, Any] = {}
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()

    def _reader(self) -> None:
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp_id = message.get("id")
            if resp_id is not None:
                self._responses[resp_id] = message

    def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Any:
        import time
        import json
        with self._lock:
            self._counter += 1
            req_id = self._counter
            request = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "call_tool",
                "params": {"name": tool_name, "arguments": arguments},
            }
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
        while True:
            if req_id in self._responses:
                response = self._responses.pop(req_id)
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result")
            time.sleep(0.01)
