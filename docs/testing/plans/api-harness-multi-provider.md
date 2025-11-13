# Implementation Plan: API-Driven, Multi-Provider Conversational Test Harness

Status: Approved (in progress)
Priority: High
Last Updated: 2025-11-13

## Objectives

- Switch testing to an API-driven harness with swappable models per role (Anthropic, OpenAI, xAI first; expansion-ready).
- Use API-key billing (separate from subscription-based CLI), reducing pressure on shared chat subscription.
- Preserve Live MCP ground truth; judge also consumes MCP logs.
- Deterministic first pass: run all tests at temperature=0 (and top_p=1 where applicable); only later explore t > 0.
- Build a parallel system (do not incrementally migrate the existing CLI runner) so current flow remains intact during development.
- Convert Claude Skill-dependent GTD instructions into a provider-agnostic system prompt; introduce optional caching hooks.

## Current Implementation Status (Harness + Gateway)

- Harness runner (`tests/harness_api/runner.py`) is wired to the `mcp-tool-gateway` Python client; when `gateway.base_url` is set, all MCP calls go through the HTTP gateway.
- Ontology bootstrap now uses `create_ontology` via the gateway and treats \"already exists\" errors as success; each harness run starts with a clean graph (`clean_graph`) for isolation.
- OpenAI adapter exposes canonical MCP tools with JSON Schemas; a simple capture test (`capture_simple_task`) now passes end-to-end at `t=0` using OpenAI → gateway → graph-memory MCP.

## Out of Scope (Now)

- Budget tracking, token estimation, smaller/cheaper default models (keep option to switch models, but do not optimize costs now).
- Key management/encryption and CI/CD integration (address later).
- Local models (not a priority now; keep path open for future).

## Architecture Overview

### Components

- Role engines: `AssistantEngine`, `UserProxyEngine`, `JudgeEngine`, `InterrogatorEngine`.
- Provider adapters: `AnthropicAdapter`, `OpenAIAdapter`, `XaiAdapter` implementing a uniform interface:
  - Chat completion, function-calls/tools, strict JSON outputs (for judge), temperature/top_p, optional seed.
- Tool router: exposes a stable set of tools to models and executes them against our MCP servers.
- Normalized transcript: provider-agnostic schema capturing messages, tool calls, tool results, timing, and errors.
- Config layer: per-role provider+model mapping; deterministic flags (temperature=0, top_p=1; seed if supported).

### Identical Tool Names

- Canonical tool naming: `mcp__<server>__<tool>` across all providers.
- If a provider later constrains tool name shape/length, add a naming shim at the adapter boundary while preserving canonical names in the normalized transcript and logs.

## MCP Integration

- Harness launches required MCP servers (Node) per run or per test:
  - Start `src/graph-memory-core/mcp` (and others as needed) with ephemeral data directories for isolation/determinism.
  - Set `MCP_CALL_LOG` so servers emit JSONL logs; collect and index per test.
  - Health checks and graceful shutdown; optional reuse per run for speed.

- Tool router execution paths:
  - Preferred: lightweight MCP client to invoke server tools directly.
  - Fallback: small Node bridge exposing MCP tools over a local HTTP/IPC endpoint that the harness calls.

## Conversation Orchestration

Per test flow (deterministic defaults):

1. Assistant ↔ User-Proxy conversation on a shared assistant session/history until completion or max turns.
2. Judge evaluates with full transcript, read-only MCP tools via the tool router, and access to MCP logs.
3. Assistant ↔ Interrogator conversation resumes the same assistant session for reasoning/inspection (optional in initial pass).

Determinism controls:
- temperature=0, top_p=1 (all roles)
- seed where supported
- fixed prompts and fixtures; isolated graph data per test
- single-threaded per test execution

## Prompts and Caching

- Convert Claude Skill knowledge into a single provider-agnostic system prompt (based on `src/conversational-layer/system-prompt-full.md`) plus concise testing overlays.
- Explicit tool-usage policy: “Call tools to perform actions; only claim outcomes after a successful tool result.”
- Optional harness-side caching keyed by (provider, model, messages, tools, parameters); disabled by default. Keep hooks for provider-side caching.

## Judge Access to Logs

- Judge receives MCP ground-truth in two ways:
  - Read-only MCP tools via the same tool router for validating graph state.
  - Access to MCP server logs (JSONL) through a read-only tool, e.g., `mcp_logs.get_recent({ since, limit, filter })` to avoid bloating prompts.

## Model Swapping (Initial Targets)

- Providers: Anthropic, OpenAI, xAI (future expansion supported by the adapter interface).
- Per-role configuration example (not binding):
  - assistant: OpenAI (e.g., GPT-5 Codex) or Anthropic Sonnet
  - user_proxy: xAI Grok-mini or Anthropic Haiku
  - judge: OpenAI or Anthropic model with reliable JSON outputs
  - interrogator: any reasoning-capable model

## Tolerance for Functional Differences in Tool-Calling

Models differ in how they plan and call tools (e.g., search-first discipline, argument accuracy, extra/reordered calls, recovery after tool errors). Our policy:

- Outcome-first by default: pass if graph state and safety/clarity criteria are met, regardless of extra or reordered valid tool calls.
- Procedure-strict tests are opted-in via flags like `require_search_first`, `confirm_before_delete`; those enforce process invariants in addition to outcomes.
- Strict schema adherence: tool inputs/outputs validated by Pydantic; minor shape repairs logged and applied conservatively.
- Judge reasons over transcript, tool results, and logs; different-but-correct paths are acceptable unless a test mandates a specific procedure.

## Risks and Mitigations

- Provider gaps in native tool-calling: use a universal tool JSON-block fallback with strict parsing.
- Prompt/log size: prefer logs tool with filtering/windowing; include only relevant excerpts.
- Determinism limits: enforce t=0/top_p=1, seeds, isolated data, and consistent fixtures; accept residual provider variability.
- MCP client complexity: ship a minimal Node bridge first if needed, then upgrade to a direct client.

## Implementation Milestones (Parallel to existing runner)

1) Scaffolding (2–3 days)
- Create `tests/harness_api/` with adapters, engines, tool router interface, config loader.
- Extract/normalize canonical system prompt; add role→model config with deterministic defaults.

2) MCP Lifecycle + Logs (2–3 days)
- Launch/shutdown MCP servers with `MCP_CALL_LOG`; readiness probes; ephemeral stores and log collectors.

3) Tool Router + Schemas (3–5 days)
- Define canonical tool schemas; implement router; Node bridge/client; deterministic fixture setup and graph cleanup via router.

4) Assistant + User-Proxy Engines (3–5 days)
- Deterministic conversational loop (t=0) with unified transcripts across Anthropic/OpenAI/xAI; universal tool-call fallback where needed.

5) Judge + Interrogator (3–4 days)
- Judge with read-only tools and logs access; strict JSON verdicts.
- Interrogator resumes assistant session; optional in initial pass.

6) Runner + Reporting (2–3 days)
- Execute tests from `tests/test_cases_refactored.json` end-to-end; console summary; minimal JSON or DB outputs compatible with current analysis.

7) Docs + Model Swap UX (1–2 days)
- Document configuration and examples; presets for Anthropic/OpenAI/xAI; add usage to testing index.

## Open Decisions

- xAI adapter details for tool-calling: start with universal JSON-block fallback if native tools are limited.
- Judge logs integration default: embed filtered excerpt vs. logs tool. Recommendation: logs tool by default for scalability.
- Default role→model mapping: decide defaults after adapters compile; allow per-run overrides.

## Next Steps

- Gateway integration baseline is complete:
  - `external/mcp-tool-gateway` hosts the generic MCP bridge + clients
  - HTTP endpoints (`/call_tool`, `/tools`, `/logs`, `/health`) are implemented and tested
  - Harness can talk to MCP via `gateway_base_url` using the gateway's Python client (preferred) or CLI fallback.
- Proceed with harness refinement under `tests/harness_api/` using the gateway as the default transport:
  - Tighten tool schemas (optionally from gateway `/tools`/`/tools/openai`)
  - Improve prompts and role policies for consistent tool use
  - Add graph cleanup between tests where needed.
- Defer provider fast paths (OpenAI Agents, xAI remote MCP tools) to `docs/testing/plans/provider-fast-paths-todo.md`.
