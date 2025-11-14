# Plan: Extract Generic Multi‑Agent Test Harness

Status: Draft  
Priority: Medium‑High  
Last Updated: 2025-11-13

## Motivation

The new API harness under `tests/harness_api/` is already close to a reusable framework for:
- Wiring up multiple LLM instances (roles) into structured conversations.
- Letting those roles use tools/functions.
- Having other models (judges) review the resulting transcripts.

Today this harness is embedded in this GTD project and coupled to:
- GTD‑specific prompts and expectations.
- The graph‑memory MCP server + mcp-tool-gateway.
- This repo’s test case schema.

Extracting the generic core into a standalone library would:
- Make it easier to reuse the “assistant/user‑proxy/judge/interrogator” pattern in other projects.
- Let us evolve multi‑role orchestration once and share improvements.
- Keep this repo focused on GTD semantics, ontology, and test cases.

## Scope

### In Scope

- A small, provider‑agnostic Python library that:
  - Defines normalized chat + tool abstractions.
  - Supports multiple roles (assistant, user‑proxy, judge, interrogator, plus custom).
  - Uses pluggable provider adapters (OpenAI, Anthropic, xAI).
  - Produces structured transcripts and per‑test results.
- Minimal runner API for “run this scenario and get a transcript + verdict”.
- Reusing this library in this repo for the GTD conversational tests.

### Out of Scope (for first extraction)

- MCP transport and graph‑memory specifics (stay in this repo + mcp-tool-gateway).
- Full reporting/DB pipelines (SQLite reports, HTML, etc.).
- Non‑Python implementations.
- Highly opinionated CI integration.

## Target Library Shape

Proposed package name: `multi_agent_harness` (working name).

### Core Types

- `ChatMessage` – normalized `{role, content}` (plus optional `tool_calls` / metadata).
- `ToolDefinition` – provider‑agnostic tool spec (name, description, JSON Schema parameters).
- `ToolCall` – model‑initiated tool invocation (name, arguments, id).
- `ToolInvocationRecord` – concrete execution of a tool within a run (arguments, result/error).
- `ConversationTurn` / `ConversationTranscript` – ordered turns + tool invocations.

These closely mirror what we already have in:
- `tests/harness_api/adapters/base.py`
- `tests/harness_api/engines/base.py`

### Provider Adapters

Subpackage: `multi_agent_harness.adapters`

Interfaces:
- `ProviderAdapter` (abstract):
  - `send_chat(role_config, messages, tools, response_format, tool_choice) -> ChatResponse`
  - `supports_tools() -> bool`

Concrete adapters:
- `OpenAIAdapter` (initially copied from `tests/harness_api/adapters/openai_adapter.py`).
- `AnthropicAdapter`, `XaiAdapter` based on existing stubs.
- `StubAdapter` for offline/unit testing.

The library does **not** import or know about MCP; it only sees `ToolDefinition`s and returns `ToolCall`s.

### Role Engines

Subpackage: `multi_agent_harness.engines`

- `RoleEngine` (abstract base for all roles).
- `AssistantEngine`:
  - Takes provider adapter, role config, and a tool router.
  - Orchestrates tool‑call loops (assistant → tools → assistant) until completion or step limit.
  - Emits `ChatResponse` plus `ToolInvocationRecord`s.
- `UserProxyEngine`:
  - Generates user turns based on scripted responses or an LLM prompt.
  - No tools by default (but design should allow tools if needed later).
- `JudgeEngine`:
  - Wraps a model that outputs a structured verdict JSON about a transcript.
  - Keeps verdict schema generic; domain‑specific judgment prompts live in the host project.
- `InterrogatorEngine`:
  - Runs follow‑up questions to the assistant after the main interaction.

All engines work only with generic prompts; GTD content and judgment criteria remain here.

### Tool Routing

The harness needs a generic hook for executing tools, but not MCP specifics.

In the library:
- Provide a minimal `ToolRouter`:
  - `register(definition, executor)` for arbitrary tools.
  - `execute(name, arguments) -> ToolExecutionResult`.
- No knowledge of MCP; just a dictionary of executors.

In this repo:
- Continue to define canonical MCP tools under `tests/harness_api/mcp/tool_definitions.py`.
- Continue to bridge those to graph‑memory via `GraphMemoryBridge` + `mcp-tool-gateway`.
- Attach the resulting `McpToolClient` to the generic `ToolRouter`.

### Config + Runner

The library can expose:
- `RoleModelConfig` – provider, model, temperature, top_p, seed.
- `HarnessConfig` – per‑role configs, tool policy, etc. (minus GTD‑specific prompt paths).
- A simple runner API:

```python
from multi_agent_harness import HarnessRunner

runner = HarnessRunner(config=..., adapters=..., tool_router=..., prompts=...)
result = runner.run_test_case(case)
# result: { "assistant_text", "transcript", "judgment", "interrogation", ... }
```

This mirrors `tests/harness_api/runner.py` but removes GTD‑specific defaults (like prompt paths and MCP ontology setup).

## What Stays In This Repo

- GTD prompts and instructions:
  - `src/conversational-layer/system-prompt-full.md`
  - `src/conversational-layer/skill-converted.md`
  - `tests/fixtures/system-prompt-live-mcp-overlay.md`
- MCP and graph‑memory transport:
  - `tests/harness_api/mcp/bridge.py`
  - `tests/harness_api/mcp/fixtures.py` (ontology + cleanup)
  - `tests/harness_api/mcp/tool_definitions.py`
- Test case definitions and GTD‑specific judging logic:
  - `tests/test_cases_refactored.json`
  - GTD judgment prompts (currently baked into `judge_openai`, etc.).
- Test selection, CLI wiring, and storage/reporting specific to this project.

## Mapping From Current Files

**Candidates to move into the library (with light cleanup):**
- `tests/harness_api/adapters/base.py`
- `tests/harness_api/adapters/openai_adapter.py`
- `tests/harness_api/adapters/anthropic_adapter.py`
- `tests/harness_api/adapters/xai_adapter.py`
- `tests/harness_api/adapters/stub_adapter.py`
- `tests/harness_api/engines/base.py`
- `tests/harness_api/engines/assistant.py` (minus GTD‑specific behavior)
- `tests/harness_api/engines/user_proxy.py`
- `tests/harness_api/engines/judge.py` (core, not the GTD prompt)
- `tests/harness_api/engines/interrogator.py`
- `tests/harness_api/run_cases.py` logic (as a reusable runner pattern).

**To remain here and depend on the library:**
- `tests/harness_api/config.py` (prompt paths, GTD defaults, gateway URL).
- `tests/harness_api/runner.py` (GTD‑specific wiring: prompts, MCP fixtures, judge prompt).
- Everything under `tests/harness_api/mcp/`.

## Extraction Phases

### Phase 1: Internal Clean‑Up (No New Repo Yet)

1. Reduce GTD coupling in harness code:
   - Ensure `engines/*` and `adapters/*` don’t directly import GTD prompts or MCP code.
   - Make the judge engine operate purely on transcripts + a configurable system prompt.
2. Add a thin “integration” layer in this repo:
   - Keep GTD prompts, MCP bridge, and ontology setup in `tests/harness_api/runner.py` and `config.py`.
   - Confirm tests still pass (at least the small OpenAI + gateway subset).

### Phase 2: New Library Repo

1. Create new repo `multi-agent-harness` (or similar).
2. Copy the generic modules over:
   - `adapters/base.py`, concrete adapters.
   - `engines/base.py`, assistant/user‑proxy/judge/interrogator.
   - Core types and runner.
3. Add minimal packaging:
   - `pyproject.toml` with standard dependencies.
   - `README.md` with example of two agents + judge.
4. Add a small test suite:
   - Unit tests for adapters (tool wiring, JSON schemas).
   - Simple “toy tool” conversations (e.g., calculator or in‑memory task list).

### Phase 3: Wire This Repo to the Library

1. Replace local imports with library imports:
   - `from tests.harness_api.adapters import ...` → `from multi_agent_harness.adapters import ...`
   - `from tests.harness_api.engines import ...` → `from multi_agent_harness.engines import ...`
2. Keep `tests/harness_api/mcp/*`, `config.py`, and `runner.py` as the GTD‑specific integration.
3. Reconfirm that:
   - The `capture_simple_task` test still passes via the library.
   - MCP plumbing via `mcp-tool-gateway` is unchanged.

### Phase 4: Optional Enhancements

- Add richer logging hooks in the library:
  - Callbacks on each tool invocation and each role turn.
  - Pluggable storage (e.g., write transcripts to JSONL or a DB).
- Add convenience helpers for:
  - Running multiple cases and aggregating judge results.
  - Comparing behavior across models/providers for the same scenario.

## Open Questions

- Naming:
  - Final package name (`multi-agent-harness`, `llm-multi-role`, etc.).
- Surface area:
  - How much of the current `HarnessConfig` should live in the library vs. be left to host projects?
- Judge responsibilities:
  - Should the library ship a “generic” judge prompt, or only the mechanics and let every host define its own?

These do not block Phase 1; they are mostly about user experience of the standalone project.

