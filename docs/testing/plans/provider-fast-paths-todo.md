# TODO: Provider Fast Paths for MCP

Status: Backlog (defer until gateway baseline is stable)
Last Updated: 2025-11-12

## Context

We now have a provider-agnostic baseline (gateway + enumerated tools), and we’ve confirmed provider docs point to optional "fast paths" where a provider API can connect to MCP servers directly:
- OpenAI Agents SDK MCP (hosted/HTTP/SSE/stdio transports)
- xAI Remote MCP Tools (HTTP/SSE, docs blocked via Cloudflare in curl, but feature exists)

We’ll keep the gateway path as the default because it works across providers and roles. These fast paths are optimizations we can enable per role when available.

## Goals

- Enable Anthropic/OpenAI/xAI roles to connect directly to remote MCP servers when it’s beneficial.
- Keep provider-agnostic gateway as the fallback/baseline.
- Ensure judge/interrogator maintain consistent log access and state verification regardless of path.

## Tasks

1) OpenAI Agents SDK MCP integration
- Add adapter mode for OpenAI "Agents/Responses API" that uses HostedMCPTool or the appropriate SDK transport.
- Config flag: `providers.openai.use_agents_mcp = true` (role-level override allowed).
- Requirements: public MCP server (HTTP/SSE) or stdio-compatible environment depending on transport.
- Keep gateway as fallback when using plain Chat Completions or when transport isn’t feasible.
- Deliverables:
  - Adapter branch that constructs HostedMCPTool (or equivalent) and passes configuration
  - Docs describing when to enable, and how this differs from gateway execution
  - Smoke test: one role via Agents MCP, others via gateway

2) xAI Remote MCP Tools integration
- Add adapter mode to configure xAI "remote MCP tools" for roles on xAI.
- Requirements: expose our MCP over HTTP/SSE (add transport or serve via gateway).
- Config flag: `providers.xai.use_remote_mcp = true` (role-level override allowed).
- Deliverables:
  - Adapter changes to pass remote MCP configuration
  - Docs and quickstart
  - Smoke test with at least one read-only tool (query/search) then a write tool

3) HTTP/SSE transport exposure for our MCP
- Option A: Add HTTP/SSE transport in our MCP server (Node) alongside stdio.
- Option B: Add SSE endpoint to the gateway that proxies to MCP client (preferred for simplicity/consistency).
- Deliverables:
  - Endpoint design and implementation (SSE) in gateway
  - Rate limiting and basic auth hooks (optional, later)

4) Role alignment and safety
- Keep per-role allowlists and process flags identical across fast paths and gateway (assistant can write; judge/interrogator read-only).
- Ensure destructive operations still require confirm-before-delete behaviors.
- Deliverables:
  - Policy consistency tests across both execution paths

5) Logs + ground-truth preservation
- Ensure judge/interrogator can still fetch MCP logs in fast-path modes.
- If provider path hides logs, rely on gateway /logs or add a provider-independent logs fetcher.
- Deliverables:
  - Unified logs abstraction in harness
  - Tests showing identical verification across paths

6) Caching compatibility
- Validate that provider’s own caching doesn’t break tool discovery or access policies.
- Decide whether to leverage provider caching for tool lists (optional, later).

7) Test plan
- Single-role fast path: assistant via provider MCP, judge/interrogator via gateway
- All-roles fast path (where supported)
- Failure modes: server unreachable, auth failures, mixed providers
- Determinism at t=0 preserved

8) Rollout
- Feature flags per provider + role
- Docs: how to enable, when to avoid
- Keep gateway as the default and stable path

## Nice-to-haves (Later)

- Automatic tool discovery across providers with schema slimming rules
- Tool exposure analytics (token impact, selection quality)
- Per-provider tutorial snippets

