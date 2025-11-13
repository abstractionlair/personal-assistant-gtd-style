"""Skeleton runner wiring config, adapters, and prompts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from .config import HarnessConfig
from .adapters.base import ProviderAdapter, ChatMessage
from .adapters.openai_adapter import OpenAIAdapter
from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.xai_adapter import XaiAdapter
from .adapters.stub_adapter import StubAdapter
from .engines.assistant import AssistantEngine
from .engines.base import ConversationTranscript, ConversationTurn
from .engines.user_proxy import UserProxyEngine
from .engines.judge import JudgeEngine
from .engines.judge_openai import run_openai_judge
from .engines.interrogator import InterrogatorEngine
from .mcp.bridge import GraphMemoryBridge
from .mcp.log_reader import McpLogReader
from .mcp.tool_router import ToolRouter
from .mcp.fixtures import ensure_ontology, clean_graph


class HarnessRunner:
    """Entry point for executing conversational tests via the new API harness."""

    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or HarnessConfig.default()
        self.adapters = self._init_adapters()
        self.tool_router = ToolRouter()
        self.mcp_bridge = GraphMemoryBridge(
            data_dir=Path(".tmp/harness/mcp/data"),
            log_dir=Path(".tmp/harness/mcp/logs"),
        )
        # Prefer gateway HTTP if configured
        if self.config.gateway_base_url:
            self.mcp_bridge.use_gateway(self.config.gateway_base_url)
        # TODO (Transport Milestone): remove stub injection when real MCP transport is ready.
        if self.config.stub_tool_responses:
            for tool, response in self.config.stub_tool_responses.items():
                self.mcp_bridge.set_stub_response(tool, response)
        self.mcp_bridge.start()
        if not self.mcp_bridge.client:
            raise RuntimeError("GraphMemoryBridge failed to initialize client")
        # Ensure ontology exists for the run
        try:
            ensure_ontology(self.mcp_bridge)
            # Start each run with a clean graph so tests do not leak state.
            clean_graph(self.mcp_bridge)
        except Exception as e:
            # Non-fatal: surface later if tools fail
            print(f"[WARN] ensure_ontology failed: {e}")
        self.tool_router.attach_mcp_client(self.mcp_bridge.client)
        log_path = self.mcp_bridge.log_dir / "graph-memory.log"
        self.log_reader = McpLogReader(log_path)
        self.assistant_engine = AssistantEngine(
            config=self.config,
            adapter=self.adapters["assistant"],
            tool_router=self.tool_router,
        )
        self.user_proxy_engine = UserProxyEngine(
            config=self.config,
            adapter=self.adapters.get("user_proxy", self.adapters["assistant"]),
        )
        self.judge_engine = JudgeEngine(
            config=self.config,
            adapter=self.adapters.get("judge", self.adapters["assistant"]),
            log_reader=self.log_reader,
        )
        self.interrogator_engine = InterrogatorEngine(
            config=self.config,
            adapter=self.adapters.get("interrogator", self.adapters["assistant"]),
        )

    def _init_adapters(self) -> Dict[str, ProviderAdapter]:
        adapters: Dict[str, ProviderAdapter] = {}
        cache: Dict[str, ProviderAdapter] = {}
        for role, role_cfg in self.config.roles.items():
            adapter = cache.get(role_cfg.provider)
            if adapter is None:
                adapter = self._create_adapter(role_cfg.provider)
                cache[role_cfg.provider] = adapter
            adapters[role] = adapter
        return adapters

    def _create_adapter(self, provider: str) -> ProviderAdapter:
        if provider == "openai":
            return OpenAIAdapter()
        if provider == "anthropic":
            return AnthropicAdapter()
        if provider == "xai":
            return XaiAdapter()
        if provider == "stub":
            return StubAdapter()
        raise ValueError(f"Unsupported provider: {provider}")

    def run_test_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Single-turn execution placeholder that records transcript structure."""

        history: List[ChatMessage] = []
        transcript = ConversationTranscript()
        user_prompt = case.get("prompt", "")
        transcript.add_turn(ConversationTurn(role="user", message=user_prompt))
        response = self.assistant_engine.run_turn(history, user_prompt)
        transcript.add_turn(
            ConversationTurn(
                role="assistant",
                message=response.message.content,
            )
        )
        history.append(ChatMessage(role="user", content=user_prompt))
        history.append(response.message)

        conv = case.get("conversational", {})
        if conv.get("enabled"):
            scripted = conv.get("user_responses") or []
            reply = self.user_proxy_engine.scripted_response(scripted, turn_index=0)
            transcript.add_turn(ConversationTurn(role="user", message=reply))
            proxy_message = ChatMessage(role="user", content=reply)
            follow_up = self.assistant_engine.run_turn(history, reply)
            transcript.add_turn(
                ConversationTurn(role="assistant", message=follow_up.message.content)
            )
            history.append(proxy_message)
            history.append(follow_up.message)
            response = follow_up
        return {
            "assistant_text": response.message.content,
            "tool_calls": [tc.name for tc in response.tool_calls],
            "transcript": transcript,
            "judgment": self.judge_engine.evaluate(case, transcript) if self.config.roles.get('judge', None) and self.config.roles['judge'].provider == 'stub' else run_openai_judge(case, transcript),
            "interrogation": self.interrogator_engine.interrogate(transcript),
        }


__all__ = ["HarnessRunner"]
