# API-Driven Conversational Test Harness (Scaffolding)

This package hosts the new multi-provider harness described in docs/testing/plans/api-harness-multi-provider.md.

Initial milestones:
1. Provider-agnostic config + canonical prompt loader (temperature=0 defaults)
2. Provider adapters (OpenAI, Anthropic, xAI) with shared interface
3. Tool router + MCP lifecycle manager
4. Role engines (assistant, user proxy, judge, interrogator)
5. Runner + reporting glue

## Current Status (2025-11-12)

- Package structure (`tests/harness_api/`) created with adapters/engines/mcp namespaces.
- Config/prompt loader (`config.py`) provides deterministic defaults (temperature=0, GPT-5 Codex assistant) and supports JSON/TOML overrides.
- Harness config supports stub tool responses for offline execution (see `stub_tool_responses`).
- Stub adapter (`provider = "stub"`) enables running the harness without API keys (see `example_stub_config.toml`).
- Example stub config + runners: `python -m tests.harness_api.run_stub` (stub-only) or `python -m tests.harness_api.run_cases --config <config> --cases <json>`.
- MCP build helper: `tests/harness_api/mcp/setup_env.sh` (runs `npm install && npm run build` in `src/graph-memory-core/mcp`). `GraphMemoryBridge` now launches the Node server via `McpLifecycleManager` whenever stub responses are disabled.
- Adapter base interface plus OpenAI adapter scaffold (real API payload path pending credentials) (`adapters/base.py`, `adapters/openai_adapter.py`).
- MCP lifecycle + tool-router scaffolding with canonical tool defs, clients/bridge, CLI bridge placeholder, Node tool runner, and log reader (`mcp/manager.py`, `mcp/tool_router.py`, `mcp/tool_definitions.py`, `mcp/client.py`, `mcp/bridge.py`, `mcp/cli_bridge.py`, `mcp/tool_runner.mjs`, `mcp/log_reader.py`).
- Runner scaffold wiring config, prompts, adapters (OpenAI/Anthropic/xAI), tool router, assistant, judge, user-proxy, and interrogator engines (`runner.py`).
- Assistant, user-proxy, judge, and interrogator engines plus shared transcript base classes (`engines/assistant.py`, `engines/user_proxy.py`, `engines/judge.py`, `engines/interrogator.py`, `engines/base.py`).
- Role-based tool exposure policy (assistant: all; judge/interrogator: read-only) via `mcp/policies.py`.
- Runner scaffold that wires config, prompts, and adapters (`runner.py`).

## Immediate Next Steps

1. Wire GraphMemoryBridge executor to real MCP transport:
   - Build `src/graph-memory-core/mcp` (npm install + build) via `tests/harness_api/mcp/setup_env.sh`
   - Launch `node dist/index.js` via lifecycle manager per run/test
   - Implement `McpCliBridge.run_tool` (subprocess call with JSON I/O)
   - Capture stdout/stderr + MCP logs and expose log-access tool
   - Keep stub mode optional for offline development
2. Finish OpenAI adapter polish (stream/error metadata) and implement Anthropic/xAI adapters using the shared interface.
3. Build full judge/interrogator engines (LLM-backed, with MCP log/tool access) and upgrade user-proxy to LLM-driven conversations.
4. Execute at least one `test_cases_refactored` scenario end-to-end through the new runner (single-/multi-turn), keeping the existing CLI runner untouched for current workflows.
