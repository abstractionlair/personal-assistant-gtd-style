"""Stub MCP client for testing stdio integration."""

class McpClientStub:
    def call_tool(self, tool_name: str, arguments):
        return {"tool": tool_name, "arguments": arguments}
