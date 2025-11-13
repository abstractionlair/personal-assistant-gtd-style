"""Simple reader for MCP JSONL logs produced during harness runs."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import json


class McpLogReader:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path

    def tail(self, max_lines: int = 200) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        selected = lines[-max_lines:]
        entries: List[Dict[str, Any]] = []
        for line in selected:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                entries.append({"parse_error": line})
        return entries
