"""Assistant engine that orchestrates prompts, history, and tool definitions."""

from __future__ import annotations

from typing import List

from ..adapters.base import ChatMessage, ChatResponse, ProviderAdapter
from ..config import HarnessConfig
from ..mcp.tool_router import ToolRouter
from ..mcp.policies import filter_tools_for_role
from .base import RoleEngine
import json


class AssistantEngine(RoleEngine):
    def __init__(
        self,
        config: HarnessConfig,
        adapter: ProviderAdapter,
        tool_router: ToolRouter,
    ) -> None:
        super().__init__("assistant", config, adapter)
        self.tool_router = tool_router
        self.system_prompts = self.build_system_prompts(list(config.prompts.load_prompts()))

    def run_turn(self, history: List[ChatMessage], user_text: str, max_steps: int = 6) -> ChatResponse:
        """Execute an assistant turn and resolve tool calls until completion or max_steps."""

        messages = list(self.system_prompts)
        messages.extend(history)
        messages.append(ChatMessage(role="user", content=user_text))
        tools = filter_tools_for_role("assistant", self.tool_router.list_tools())

        response = self.adapter.send_chat(
            role_config=self.role_config,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        steps = 0
        while response.tool_calls and steps < max_steps:
            # Append the assistant turn with tool_calls so providers accept tool messages next
            tool_calls_payload = []
            for idx, call in enumerate(response.tool_calls):
                tool_calls_payload.append({
                    "type": "function",
                    "id": call.call_id or f"call_{idx}",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                })
            messages.append(ChatMessage(role="assistant", content={"tool_calls": tool_calls_payload}))
            for call in response.tool_calls:
                result = self.tool_router.execute(call.name, call.arguments)
                tool_msg = ChatMessage(
                    role="tool",
                    content={
                        "tool_call_id": call.call_id or call.name,
                        "content": json.dumps(result.output),
                    },
                )
                messages.append(tool_msg)

            response = self.adapter.send_chat(
                role_config=self.role_config,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            steps += 1

        return response


__all__ = ["AssistantEngine"]
