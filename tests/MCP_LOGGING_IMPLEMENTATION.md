# MCP Tool Call Logging Implementation

## Overview

Added MCP (Model Context Protocol) tool call logging to the test framework so both the judge and humans can see what operations were performed during test execution. This addresses the concern that MCP call logs might have been lost when the judge was given direct access to query the graph.

## Implementation Details

### 1. MCP Server Logging Configuration

**File:** `tests/mcp-config.json`

Added `MCP_CALL_LOG` environment variable to enable MCP server's built-in logging:

```json
{
  "mcpServers": {
    "gtd-graph-memory": {
      "command": "node",
      "args": ["/Users/scottmcguire/Share1/Projects/personal-assistant-gtd-style/src/graph-memory-core/mcp/dist/index.js"],
      "env": {
        "BASE_PATH": "/Users/scottmcguire/Share1/Projects/personal-assistant-gtd-style/.data/gtd-memory",
        "MCP_CALL_LOG": "/Users/scottmcguire/Share1/Projects/personal-assistant-gtd-style/.data/gtd-memory/mcp-calls.log"
      }
    }
  }
}
```

### 2. Test Runner Updates

**File:** `tests/conversational_layer/runner.py`

#### Added Constants and Helper Functions

```python
import os  # Added

MCP_LOG_PATH = Path("/Users/scottmcguire/Share1/Projects/personal-assistant-gtd-style/.data/gtd-memory/mcp-calls.log")

def clear_mcp_log() -> None:
    """Clear MCP call log file before test execution."""
    try:
        if MCP_LOG_PATH.exists():
            MCP_LOG_PATH.unlink()
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Failed to clear MCP log: {e}")

def read_mcp_log() -> str:
    """Read MCP call log file after test execution.

    Returns:
        String content of MCP log file, or empty string if not found
    """
    try:
        if MCP_LOG_PATH.exists():
            return MCP_LOG_PATH.read_text(encoding='utf-8')
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Failed to read MCP log: {e}")

    return ""
```

#### Updated `run_assistant_single_attempt()` Function

Lines 108-196:

- **Before execution:** Call `clear_mcp_log()` to ensure clean state
- **After execution:** Call `read_mcp_log()` to capture MCP logs
- **In result dict:** Add `mcp_logs` field and append to `full_output`

```python
# Clear MCP log before execution
clear_mcp_log()

try:
    result = run_claude_assistant(...)

    # Read MCP logs after execution
    mcp_logs = read_mcp_log()

    # ... process result ...

    # Combine stdout and MCP logs in full_output
    full_output = result.stdout.strip()
    if mcp_logs:
        full_output += "\n\n=== MCP Tool Calls ===\n" + mcp_logs

    return {
        "pass": True,
        "assistant": assistant_text,
        "full_output": full_output,
        "mcp_logs": mcp_logs,
        "session_id": session_id,
        "retry": False
    }
```

#### Updated Conversational Test Handling

Lines 261-306:

Same pattern for multi-turn conversational tests:

```python
elif is_conversational_test(case):
    # Clear MCP log before conversation
    clear_mcp_log()

    # ... run conversation ...

    # Read MCP logs after conversation completes
    mcp_logs = read_mcp_log()

    # Combine transcript and MCP logs
    full_output = conv_result.full_transcript
    if mcp_logs:
        full_output += "\n\n=== MCP Tool Calls ===\n" + mcp_logs
```

## What Gets Logged

The MCP server logs each tool call as a JSON line with:

- **timestamp**: ISO 8601 timestamp
- **tool**: Tool name (e.g., `create_node`, `query_nodes`, `search_content`)
- **input**: Tool input parameters
- **result**: Tool result (if successful)
- **error**: Error message (if failed)

### Example Log Output

```json
{"timestamp":"2025-11-11T13:29:46.647Z","tool":"SERVER_START","input":{}}
{"timestamp":"2025-11-11T13:29:51.656Z","tool":"create_node","input":{"type":"Task","content":"Call dentist to schedule cleaning","encoding":"utf-8","format":"text/plain","properties":{"isComplete":false}},"error":"Error: Ontology has not been created yet"}
{"timestamp":"2025-11-11T13:29:56.007Z","tool":"create_ontology","input":{"node_types":["Task","Context","State","UNSPECIFIED"],"connection_types":[{"name":"DependsOn","from_types":["Task"],"to_types":["Task","Context","State","UNSPECIFIED"],"required_properties":[]}]}}
{"timestamp":"2025-11-11T13:30:00.649Z","tool":"create_node","input":{"type":"Task","content":"Call dentist to schedule cleaning","encoding":"utf-8","format":"text/plain","properties":{"isComplete":false}},"result":{"node_id":"mem_mhulz0hy_e7ggugi"}}
```

## Benefits

1. **Judge Visibility**: The judge now receives MCP logs in `full_output` along with the Claude JSON response, enabling evaluation of:
   - Whether correct MCP tools were called
   - Order of operations
   - What data was passed to tools
   - Whether operations succeeded or failed

2. **Human Analysis**: Test transcripts and markdown reports include MCP logs for debugging and analysis

3. **Markdown Reports**: MCP logs are automatically pretty-printed in generated reports with proper JSON formatting

4. **Database Storage**: MCP logs are stored in `full_transcript` column for historical analysis

## Testing

Verified with `capture_simple_task` test:

```bash
python tests/test_conversational_layer_new.py --test-name capture_simple_task --runs 1
```

Results:
- ✅ Test passed
- ✅ MCP logs captured in database (`full_transcript` column)
- ✅ MCP logs included in markdown report with pretty-printed JSON
- ✅ Log shows complete sequence of operations

## Files Modified

1. `tests/mcp-config.json` - Added `MCP_CALL_LOG` environment variable
2. `tests/conversational_layer/runner.py` - Added MCP log capture logic

## Related Code

MCP server logging implementation: `src/graph-memory-core/mcp/src/server.ts` lines 177-208
