"""Configuration primitives for the API-driven conversational harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, MutableMapping, Optional
import json
import tomllib

# Canonical prompt locations (relative to repo root)
BASE_SYSTEM_PROMPT = Path("src/conversational-layer/system-prompt-full.md")
TEST_OVERLAY_PROMPT = Path("tests/fixtures/system-prompt-live-mcp-overlay.md")
SKILL_PROMPT = Path("src/conversational-layer/skill-converted.md")


@dataclass(slots=True)
class RoleModelConfig:
    """Model selection for a single role in the harness."""

    provider: str
    model: str
    temperature: float = 0.0
    top_p: float = 1.0
    seed: Optional[int] = None


@dataclass(slots=True)
class PromptConfig:
    """File locations for canonical prompts."""

    base_prompt_path: Path = BASE_SYSTEM_PROMPT
    overlay_paths: tuple[Path, ...] = (SKILL_PROMPT, TEST_OVERLAY_PROMPT)

    def load_prompts(self) -> tuple[str, ...]:
        """Return prompt texts (base first, then overlays)."""

        texts: list[str] = []
        paths = (self.base_prompt_path,) + self.overlay_paths
        for path in paths:
            if not path:
                continue
            resolved = path if path.is_absolute() else Path.cwd() / path
            try:
                texts.append(resolved.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Prompt file not found: {resolved}") from exc
        return tuple(texts)


@dataclass(slots=True)
class HarnessConfig:
    """Top-level harness configuration."""

    roles: Dict[str, RoleModelConfig] = field(default_factory=dict)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    enable_prompt_cache: bool = False
    stub_tool_responses: Dict[str, object] = field(default_factory=dict)
    gateway_base_url: Optional[str] = None

    @classmethod
    def default(cls) -> "HarnessConfig":
        """Return deterministic defaults targeting GPT-5 Codex for assistant role."""

        default_roles = {
            "assistant": RoleModelConfig(provider="openai", model="gpt-5-codex"),
            "user_proxy": RoleModelConfig(provider="openai", model="gpt-4o-mini"),
            "judge": RoleModelConfig(provider="openai", model="gpt-4o-mini"),
            "interrogator": RoleModelConfig(provider="openai", model="gpt-4o-mini"),
        }
        return cls(roles=default_roles)

    @classmethod
    def load(cls, path: Optional[Path]) -> "HarnessConfig":
        """Load configuration from JSON/TOML; fall back to defaults when path is None."""

        if path is None:
            return cls.default()
        resolved = path if path.is_absolute() else Path.cwd() / path
        if not resolved.exists():
            raise FileNotFoundError(f"Config file not found: {resolved}")
        raw = resolved.read_text(encoding="utf-8")
        data: MutableMapping[str, object]
        if resolved.suffix.lower() == ".json":
            data = json.loads(raw)
        elif resolved.suffix.lower() in {".toml", ".tml"}:
            data = tomllib.loads(raw)
        else:
            raise ValueError("Harness config must be .json or .toml")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: MutableMapping[str, object]) -> "HarnessConfig":
        roles_cfg = {
            role: RoleModelConfig(**cfg)  # type: ignore[arg-type]
            for role, cfg in data.get("roles", {}).items()
        }
        prompts_cfg = data.get("prompts", {})
        overlay_paths = tuple(
            Path(p) for p in prompts_cfg.get("overlay_paths", [str(TEST_OVERLAY_PROMPT)])
        )
        prompt_config = PromptConfig(
            base_prompt_path=Path(prompts_cfg.get("base_prompt_path", BASE_SYSTEM_PROMPT)),
            overlay_paths=overlay_paths,
        )
        gateway_cfg = data.get("gateway", {})
        return cls(
            roles=roles_cfg or cls.default().roles,
            prompts=prompt_config,
            enable_prompt_cache=bool(data.get("enable_prompt_cache", False)),
            stub_tool_responses=data.get("stub_tool_responses", {}),
            gateway_base_url=gateway_cfg.get("base_url") or data.get("gateway_base_url"),
        )


__all__ = [
    "HarnessConfig",
    "PromptConfig",
    "RoleModelConfig",
    "BASE_SYSTEM_PROMPT",
    "TEST_OVERLAY_PROMPT",
]
