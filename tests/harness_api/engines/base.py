"""Shared engine scaffolding and transcript models."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, List

from ..adapters.base import ChatMessage, ProviderAdapter
from ..config import HarnessConfig, RoleModelConfig


@dataclass(slots=True)
class ToolInvocationRecord:
    tool_name: str
    arguments: dict[str, Any]
    result: Any | None = None
    error: str | None = None


@dataclass(slots=True)
class ConversationTurn:
    role: str
    message: str
    tool_invocations: List[ToolInvocationRecord] = field(default_factory=list)


@dataclass(slots=True)
class ConversationTranscript:
    turns: List[ConversationTurn] = field(default_factory=list)

    def add_turn(self, turn: ConversationTurn) -> None:
        self.turns.append(turn)


class RoleEngine(ABC):
    role: str

    def __init__(self, role: str, config: HarnessConfig, adapter: ProviderAdapter) -> None:
        self.role = role
        self.config = config
        self.role_config: RoleModelConfig = config.roles[role]
        self.adapter = adapter

    def build_system_prompts(self, prompt_texts: List[str]) -> List[ChatMessage]:
        return [ChatMessage(role="system", content=text) for text in prompt_texts]


__all__ = [
    "ConversationTranscript",
    "ConversationTurn",
    "RoleEngine",
    "ToolInvocationRecord",
]
