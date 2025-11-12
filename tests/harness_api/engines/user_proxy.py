"""Deterministic user-proxy engine scaffolding."""

from __future__ import annotations

from typing import List, Optional

from ..adapters.base import ChatMessage, ProviderAdapter
from ..config import HarnessConfig
from .base import RoleEngine


class UserProxyEngine(RoleEngine):
    def __init__(self, config: HarnessConfig, adapter: ProviderAdapter) -> None:
        super().__init__("user_proxy", config, adapter)

    def scripted_response(
        self,
        scripted: Optional[List[str]],
        turn_index: int,
        fallback: str = "Thanks, that clarifies it."
    ) -> str:
        if scripted and turn_index < len(scripted):
            return scripted[turn_index]
        return fallback

    def as_chat_message(self, content: str) -> ChatMessage:
        return ChatMessage(role="user", content=content)


__all__ = ["UserProxyEngine"]
