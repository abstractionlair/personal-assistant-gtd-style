"""Graph fixture setup and cleanup for test isolation.

Provides functions to clean graph state between tests and populate
test fixtures.
"""

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

from .config import Config
from .errors import handle_subprocess_error
from .logging_config import get_logger


# Constants from main test file
CLAUDE_CMD = "claude"


def parse_payload(raw: str) -> Optional[Dict[str, Any]]:
    """Parse JSON payload from Claude CLI output.

    Args:
        raw: Raw output string from Claude CLI

    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_text(payload: Dict[str, Any]) -> str:
    """Extract text content from Claude CLI JSON payload.

    Args:
        payload: Parsed JSON payload

    Returns:
        Extracted text content

    Tries multiple keys in order: result, text, output, outputs.
    Falls back to JSON dump if no text found.
    """
    for key in ("result", "text", "output"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    outputs = payload.get("outputs")
    if isinstance(outputs, list):
        return "\n".join(str(item.get("text", "")) for item in outputs if isinstance(item, dict))

    return json.dumps(payload, indent=2)


def clean_graph_state(config: Config) -> bool:
    """Delete all nodes in the graph to ensure clean state between tests.

    Args:
        config: Test configuration

    Returns:
        True if cleanup succeeded, False otherwise

    Notes:
        - Requires MCP config path to be set
        - Deletes all nodes (connections cascade automatically)
        - Logs warnings on failure but doesn't raise exceptions
    """
    logger = get_logger()

    if not config.mcp_config_path:
        logger.error("MCP config path is required for graph cleanup")
        return False  # Cannot clean without MCP config

    logger.info("Cleaning graph state...")

    cleanup_prompt = textwrap.dedent("""
        Delete all nodes in the graph to prepare for the next test.

        Steps:
        1. Query all nodes (no filters)
        2. Delete each node (connections will cascade automatically)
        3. Confirm the graph is empty

        Be thorough - we need a completely clean slate for test isolation.
    """).strip()

    cleanup_system = textwrap.dedent("""
        You are a graph cleanup utility. Your job is to delete all nodes in the graph.
        Use query_nodes with no filters to find all nodes, then delete each one.
        Be concise - just do the cleanup and confirm when done.
    """).strip()

    try:
        args = [CLAUDE_CMD]
        if config.mcp_config_path:
            args += ["--mcp-config", str(config.mcp_config_path)]
        args += [
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json",
            "--system-prompt", cleanup_system,
            cleanup_prompt
        ]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=config.cleanup_timeout,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Graph cleanup failed: {result.stderr.strip()}")
            return False

        payload = parse_payload(result.stdout)
        if payload is None:
            logger.warning("Graph cleanup returned non-JSON output")
            return False

        logger.info("Graph cleanup completed successfully")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Graph cleanup timed out after {config.cleanup_timeout}s")
        return False
    except Exception as e:
        error_dict = handle_subprocess_error(e, "clean_graph_state")
        logger.error(f"Graph cleanup error: {error_dict['reason']}")
        return False


def setup_graph_from_fixture(
    fixture: Dict[str, Any],
    config: Config
) -> bool:
    """Populate graph with fixture data for test setup.

    Args:
        fixture: Dictionary with 'tasks', 'contexts', 'states' arrays
        config: Test configuration

    Returns:
        True if setup succeeded, False otherwise

    Fixture format:
        {
            "tasks": [
                {
                    "content": "Task description",
                    "isComplete": false,
                    "depends_on": ["other_task_id"],
                    "id": "task_1"  # Optional, for referencing
                }
            ],
            "contexts": [
                {
                    "content": "@office",
                    "isAvailable": true
                }
            ],
            "states": [
                {
                    "content": "Weather is good",
                    "isTrue": false
                }
            ]
        }
    """
    logger = get_logger()

    if not fixture:
        logger.debug("No fixture data to set up")
        return True  # No setup needed

    if not config.mcp_config_path:
        logger.error("MCP config path is required for fixture setup")
        return False

    # Convert fixture to natural language setup instructions
    setup_instructions = []

    # Tasks
    for task in fixture.get("tasks", []):
        content = task.get("content", "")
        is_complete = task.get("isComplete", False)
        depends_on = task.get("depends_on", [])
        task_id = task.get("id", "")

        if is_complete:
            setup_instructions.append(f"Create a completed task: '{content}'")
        else:
            setup_instructions.append(f"Create an incomplete task: '{content}'")

        if task_id:
            setup_instructions.append(f"  (Store this task ID as '{task_id}' for later reference)")

        for dep in depends_on:
            setup_instructions.append(f"  Make this task depend on: {dep}")

    # Contexts
    for context in fixture.get("contexts", []):
        content = context.get("content", "")
        is_available = context.get("isAvailable", False)
        avail_str = "available" if is_available else "unavailable"
        setup_instructions.append(f"Create context {content} (currently {avail_str})")

    # States
    for state in fixture.get("states", []):
        content = state.get("content", "")
        is_true = state.get("isTrue", False)
        state_str = "true" if is_true else "false"
        setup_instructions.append(f"Create manual state: '{content}' (currently {state_str})")

    if not setup_instructions:
        logger.debug("No fixture instructions to execute")
        return True  # Nothing to set up

    setup_prompt = "Set up the following test data:\n\n" + "\n".join(setup_instructions)

    setup_system = textwrap.dedent("""
        You are a test fixture setup utility for a GTD system.
        Your job is to create nodes and connections as requested.

        Execute all setup commands precisely, then confirm completion.
        Be concise - just create what's needed and confirm when done.
    """).strip()

    logger.info(f"Setting up fixture with {len(setup_instructions)} instructions")

    try:
        args = [CLAUDE_CMD]
        if config.mcp_config_path:
            args += ["--mcp-config", str(config.mcp_config_path)]
        args += [
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json",
            "--system-prompt", setup_system,
            setup_prompt
        ]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=config.cleanup_timeout,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Graph setup failed: {result.stderr.strip()}")
            return False

        payload = parse_payload(result.stdout)
        if payload is None:
            logger.warning("Graph setup returned non-JSON output")
            return False

        logger.info("Fixture setup completed successfully")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Graph setup timed out after {config.cleanup_timeout}s")
        return False
    except Exception as e:
        error_dict = handle_subprocess_error(e, "setup_graph_from_fixture")
        logger.error(f"Graph setup error: {error_dict['reason']}")
        return False


def verify_mcp_server(mcp_config_path: Path, timeout: float = 10.0) -> bool:
    """Verify MCP server is accessible and responding.

    Args:
        mcp_config_path: Path to MCP configuration file
        timeout: Timeout for health check (seconds)

    Returns:
        True if server is healthy, False otherwise

    Performs a simple query to verify the MCP server is running and responding.
    """
    logger = get_logger()

    logger.debug(f"Verifying MCP server at {mcp_config_path}")

    try:
        # Simple ping query
        ping_system = "You are a health check utility. Just confirm the system is working."
        ping_prompt = "Ping - respond if you can access the graph memory."

        args = [
            CLAUDE_CMD,
            "--mcp-config", str(mcp_config_path),
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json",
            "--system-prompt", ping_system,
            ping_prompt
        ]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode == 0:
            logger.info("MCP server health check passed")
            return True
        else:
            logger.warning(f"MCP server health check failed: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"MCP server health check timed out after {timeout}s")
        return False
    except Exception as e:
        error_dict = handle_subprocess_error(e, "verify_mcp_server")
        logger.error(f"MCP server health check error: {error_dict['reason']}")
        return False
