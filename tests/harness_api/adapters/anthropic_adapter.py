"""Anthropic adapter scaffold for the API-driven harness."""

from __future__ import annotations

import os

from .base import (
    ChatMessage,
    ChatResponse,
    ProviderAdapter,
    ResponseFormat,
    ToolDefinition,
)
from ..config import RoleModelConfig


class AnthropicAdapter(ProviderAdapter):
    provider_name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def send_chat(
        self,
        role_config: RoleModelConfig,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
        response_format: ResponseFormat | None = None,
    ) -> ChatResponse:
        raise NotImplementedError("Anthropic adapter not yet implemented")

    def supports_tools(self) -> bool:
        return True


__all__ = ["AnthropicAdapter"]
