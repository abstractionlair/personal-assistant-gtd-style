# Plan: MCP Tool Gateway (Generic Bridge + Clients)

Status: Approved for design + implementation
Last Updated: 2025-11-12

## Rationale

We want a provider-agnostic way for LLMs and arbitrary code (Python/TS) to call MCP servers:
- Keep MCP as the spec-aligned boundary for graph operations and logging
- Expose a simple HTTP/stdio API that any client can call
- Auto-generate enumerated provider tools for OpenAI/Anthropic/xAI adapters
- Avoid vendor lock-in and reduce per-call overhead vs CLI

## Scope

Generic, reusable repo “mcp-tool-gateway” that provides:
- Node bridge service:
  - Connects to MCP servers using official JS client over stdio
  - Exposes HTTP endpoints:
    - POST `/call_tool` → `{ server, tool, arguments }` → `{ result, correlation_id }`
    - GET `/tools` → discovery + JSON Schemas
    - GET `/logs` → recent MCP log entries (uses MCP_CALL_LOG)
    - GET `/health`
- Clients:
  - Python client (`mcp_tool_gateway`) for call_tool/tools/logs
  - TypeScript client (`@mcp-tool-gateway/client`)
- Tool discovery / schema gen:
  - Emit canonical tool list with JSON Schemas from a running MCP server (tools/list)
  - Optional build-time Zod→JSON Schema for servers that register Zod schemas

Out of scope (now): AuthN/AuthZ, rate limiting, multi-tenant isolation, CI/CD, hosted images.

## API Sketch

- POST `/call_tool`
  - req: `{ server: string, tool: string, arguments: object }`
  - res: `{ result: any, correlation_id: string }`
  - 4xx: `{ error: { code, message, details? } }`

- GET `/tools?server=...`
  - res: `[{ server, tool, description, json_schema }]`

- GET `/logs?server=...&since=iso8601&limit=100`
  - res: `[{ timestamp, tool, input, result?, error? }]`

- GET `/health`
  - res: `{ ok: true, servers: [{ name, status }] }`

## Transport to MCP Server

- Use official JS MCP client to connect to each server via stdio (one per run)
- Server lifecycle:
  - Option A: Connect to an already-running server (preferred)
  - Option B: Spawn the server (node dist/index.js) with env (BASE_PATH, MCP_CALL_LOG)
- Multiple servers supported (named), configured via env or JSON

## Provider Tool Exposure (in this project)

- Generate enumerated provider tools (one per MCP command) from discovery JSON
- Keep canonical names: `mcp__<server>__<tool>`
- Per-role exposure policy:
  - Assistant: read/write tools
  - Judge: read-only + logs
  - Interrogator: read-only
  - User-proxy: usually none
- Optionally slim schemas to control token usage

## Integration Here (personal-assistant-gtd-style)

- Add the gateway as a submodule, then consume via Python client in `GraphMemoryBridge`
- Retain current CLI/per-call runner as fallback for offline/stub modes
- Update adapters to enumerate tools from discovery JSON at startup
- Keep judge log access via gateway `/logs`

## Milestones

M1 — Repo scaffold (Node service + minimal HTTP) [0.5–1 day]
- package.json, tsconfig, dev server, OpenAPI skeleton

M2 — Connect to MCP servers [0.5–1 day]
- Integrate JS MCP client over stdio, server lifecycle options

M3 — call_tool endpoint [0.5–1 day]
- Proxy name/arguments to MCP, return structured result/errors

M4 — tools endpoint [0.5 day]
- Discover tools + JSON Schemas (tools/list or Zod→JSON Schema)

M5 — logs endpoint [0.5 day]
- Tail MCP_CALL_LOG with filters; support since/limit

M6 — Python + TS clients [0.5–1 day]
- Thin wrappers; retries, timeouts, error mapping

M7 — Integrate here [0.5–1 day]
- Wire GraphMemoryBridge to Python client; keep stub/CLI fallback
- Enumerated provider tools per role from discovery JSON

M8 — E2E test [0.5 day]
- Run one `test_cases_refactored` scenario end-to-end using gateway

## Assignments: GPT-5 vs GPT-5 Codex

GPT-5 (reasoning/docs/design)
- Finalize API contract and exposure policy per role
- Prompt/UX guidance for tool usage and process constraints (search-first, confirm-before-delete)
- Discovery schema slimming rules and testing plan
- Review adapter prompt snippets to ensure good tool selection

GPT-5 Codex (coding/implementation)
- Scaffold Node gateway service, implement `/call_tool`, `/tools`, `/logs`, `/health`
- Integrate JS MCP client over stdio + server lifecycle
- Build Python + TS clients
- Integrate gateway client into `GraphMemoryBridge`
- Implement enumerated tools generation + wiring in adapters
- Add smoke tests and harness tweaks (t=0, single-threaded calls)

## gh Steps (once repo exists)

1) Create repo
```
gh repo create mcp-tool-gateway --public --source=. --remote=origin --enable-wiki=false --enable-issues=true
```

2) Push initial scaffold (Node service + clients dirs)
```
git add node/ python/ ts/ tools/ README.md package.json
git commit -m "scaffold gateway"
git push -u origin main
```

3) In this project, add as submodule and wire client
```
git submodule add https://github.com/<you>/mcp-tool-gateway external/mcp-tool-gateway
```

4) Update `GraphMemoryBridge` to use Python client; keep CLI/stub fallback

## Risks / Notes

- Token budgets: enumerate tools but consider slimming (drop verbose descriptions)
- Safety: per-role allowlists and process constraints remain in this repo (judge enforces)
- Anthropic fast path: later, add HTTP/SSE transport to our MCP server and enable `mcp_servers` as optional optimization

