"""Judge engine scaffold using canonical prompts and MCP log awareness."""

from __future__ import annotations

from typing import Dict, Any

from ..adapters.base import ChatMessage, ProviderAdapter
from ..config import HarnessConfig
from ..mcp.log_reader import McpLogReader
from .base import ConversationTranscript, RoleEngine


class JudgeEngine(RoleEngine):
    def __init__(
        self,
        config: HarnessConfig,
        adapter: ProviderAdapter,
        log_reader: McpLogReader,
    ) -> None:
        super().__init__("judge", config, adapter)
        self.log_reader = log_reader
        self.system_prompts = self.build_system_prompts([
            "You are a placeholder judge. Real evaluation pending MCP integration.",
        ])

    def evaluate(self, case: Dict[str, Any], transcript: ConversationTranscript) -> Dict[str, Any]:
        logs = self.log_reader.tail(max_lines=50)
        messages = list(self.system_prompts)
        messages.append(
            ChatMessage(
                role="user",
                content=f"Case: {case.get('name')}\nTranscript: {transcript}\nLogs: {logs}\nProvide a JSON verdict.",
            )
        )
        # Placeholder verdict until real judge logic implemented.
        return {
            "pass": False,
            "reason": "Judge engine not fully implemented",
            "logs_considered": len(logs),
        }


__all__ = ["JudgeEngine"]
