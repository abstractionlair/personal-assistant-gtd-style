"""Interrogator engine scaffold built on shared role base."""

from __future__ import annotations

from typing import Dict, Any

from ..adapters.base import ChatMessage, ProviderAdapter
from ..config import HarnessConfig
from .base import ConversationTranscript, RoleEngine


class InterrogatorEngine(RoleEngine):
    def __init__(self, config: HarnessConfig, adapter: ProviderAdapter) -> None:
        super().__init__("interrogator", config, adapter)
        self.system_prompts = self.build_system_prompts([
            "You are a placeholder interrogator. Ask follow-up questions about the assistant's reasoning."
        ])

    def interrogate(self, transcript: ConversationTranscript) -> Dict[str, Any]:
        messages = list(self.system_prompts)
        messages.append(
            ChatMessage(
                role="user",
                content=f"Transcript: {transcript}. Provide placeholder interrogation output.",
            )
        )
        return {
            "questions": [
                {
                    "q": "Placeholder question",
                    "a": "Interrogator not implemented yet",
                }
            ]
        }


__all__ = ["InterrogatorEngine"]
