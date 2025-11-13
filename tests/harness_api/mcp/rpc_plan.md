# MCP Transport Plan (Python ↔ GraphMemory Server)

## Goals
- Replace per-call `tool_runner.mjs` invocation with a persistent connection to the Node MCP server.
- Reuse the running server launched by `McpLifecycleManager` for all tool calls in a test run.
- Surface MCP call logs and errors cleanly to the judge/interrogator.
- Keep stub mode (`stub_tool_responses`) available as a fallback/offline option.

## Transport Options

1. **Stdio MCP Client (Preferred)**
   - Use Anthropic's MCP client libraries or implement a minimal Python client that speaks MCP JSON-RPC over stdio.
   - `GraphMemoryBridge` launches the Node server via `McpLifecycleManager` (already done) and then spawns a dedicated client process or uses asyncio subprocess pipes to send `tool` requests and read responses.
   - Pros: aligns with MCP spec, no extra HTTP bridge, can multiplex tool calls.
   - Cons: requires implementing MCP stdio framing in Python (JSON-RPC 2.0 with headers or newline framing).

2. **HTTP/IPC Bridge**
   - Wrap Node server with an HTTP or IPC layer (e.g., Express server exposing `/call_tool`).
   - Python harness issues HTTP requests per tool call.
   - Pros: simpler client implementation.
   - Cons: requires additional Node service; less aligned with MCP stdio design.

3. **Extend tool_runner.mjs**
   - Keep CLI approach but change it to connect to the running server instead of reinitializing the graph.
   - Requires implementing a Node MCP client that communicates with the server via stdio and exposes a lightweight CLI for each call.

## Selected Approach

Adopt **Option 1 (Stdio MCP Client)**:
- Implement a small Python MCP client that:
  1. Opens the Node MCP server's stdio pipes (thru the child process created by `McpLifecycleManager`).
  2. Sends MCP JSON-RPC `call_tool` requests and awaits responses.
  3. Manages request IDs, timeouts, and error propagation.
- `GraphMemoryBridge` stores the child process handle from `McpLifecycleManager` and passes it to the MCP client.
- Each tool call becomes `client.call_tool(tool_name, arguments)` which writes a JSON message to server stdin and reads a JSON response from stdout.

## Implementation Steps

1. **Expose Process Handles**
   - Update `McpLifecycleManager` to return references to running processes (already available via `McpServerProcess`).
   - Provide helper methods to access stdin/stdout pipes.

2. **Create `McpStdioClient`**
   - New module `tests/harness_api/mcp/stdio_client.py` with methods:
     - `call_tool(tool_name: str, args: Mapping[str, Any]) -> Any`
     - Manage JSON-RPC IDs, encode/decode messages, handle timeouts.

3. **Bridge Integration**
   - `GraphMemoryBridge` instantiates `McpStdioClient` after `start_all()` finishes.
   - `_execute` uses the stdio client when `stub_tool_responses` is empty.
   - Keep CLI bridge as fallback until stdio client is fully tested.

4. **Log Tool**
   - Add a tool definition (e.g., `mcp_logs.get_recent`) backed by MCP log reader to expose log events to judge/interrogator.

5. **Cleanup**
   - On `stop()`, ensure stdio client closes pipes and `McpLifecycleManager` terminates the server.

## Timeline
- **Milestone 1**: Implement `McpStdioClient`, integrate with bridge, run single tool call end-to-end.
- **Milestone 2**: Replace CLI bridge usage entirely, remove per-call Node bootstrap.
- **Milestone 3**: Add log-access tool and connect judge/interrogator to it.

