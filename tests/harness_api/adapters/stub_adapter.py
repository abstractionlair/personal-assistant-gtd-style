"""Stub adapter for offline harness testing."""

from __future__ import annotations

from .base import (
    ChatMessage,
    ChatResponse,
    ProviderAdapter,
    ResponseFormat,
    ToolCall,
    ToolDefinition,
)
from ..config import RoleModelConfig


class StubAdapter(ProviderAdapter):
    provider_name = "stub"

    def send_chat(
        self,
        role_config: RoleModelConfig,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
        response_format: ResponseFormat | None = None,
    ) -> ChatResponse:
        return ChatResponse(
            message=ChatMessage(role="assistant", content=f"[stub:{role_config.model}]"),
            tool_calls=tuple(),
            raw={"stub": True},
        )

    def supports_tools(self) -> bool:
        return False


__all__ = ["StubAdapter"]
