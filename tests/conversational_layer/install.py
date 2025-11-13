"""Test installation builder for isolated test environments.

Creates clean test installation directories that mimic production deployment,
removing development environment artifacts while keeping production tools available.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from .config import Config
from .logging_config import get_logger


class TestInstallation:
    """Manages isolated test installation environments.

    Creates a clean installation directory structure:
        .test-install/
          └── gtd-assistant/
              ├── system-prompt.md (bundled with overlays)
              ├── mcp-config.json (isolated data path)
              └── data/  (isolated graph storage)

    Working directory during tests: /tmp/gtd-test-workspace
    """

    def __init__(self, config: Config, install_root: Optional[Path] = None):
        """Initialize test installation manager.

        Args:
            config: Test configuration
            install_root: Root directory for test installations (default: .test-install/)
        """
        self.config = config
        self.logger = get_logger()

        # Installation paths
        if install_root is None:
            install_root = Path.cwd() / ".test-install"
        self.install_root = install_root
        self.install_dir = install_root / "gtd-assistant"

        # Working directory for test execution
        self.workspace_dir = Path("/tmp/gtd-test-workspace")

        # Paths within installation
        self.system_prompt_path = self.install_dir / "system-prompt.md"
        self.mcp_config_path = self.install_dir / "mcp-config.json"
        self.data_dir = self.install_dir / "data"

    def build(self, force: bool = False) -> None:
        """Build clean test installation.

        Args:
            force: If True, remove existing installation first

        Raises:
            RuntimeError: If installation already exists and force=False
        """
        self.logger.info("Building test installation...")

        # Check for existing installation
        if self.install_dir.exists():
            if force:
                self.logger.info(f"Removing existing installation: {self.install_dir}")
                shutil.rmtree(self.install_dir)
            else:
                raise RuntimeError(
                    f"Installation already exists: {self.install_dir}\n"
                    "Use force=True to rebuild or call cleanup() first"
                )

        # Create directory structure
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Bundle system prompt with overlays
        self._bundle_system_prompt()

        # Create isolated MCP config
        self._create_mcp_config()

        # Create workspace directory
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Test installation created: {self.install_dir}")
        self.logger.info(f"Working directory: {self.workspace_dir}")

    def _bundle_system_prompt(self) -> None:
        """Bundle system prompt with test overlays into single file."""
        self.logger.debug("Bundling system prompt with overlays...")

        # Read base system prompt
        base_prompt = self.config.system_prompt_path.read_text(encoding='utf-8')

        # Read and append overlays
        overlays = self.config.get_test_overlays()
        overlay_content = []

        for overlay_path in overlays:
            if overlay_path.exists():
                self.logger.debug(f"Adding overlay: {overlay_path}")
                content = overlay_path.read_text(encoding='utf-8')
                overlay_content.append(f"\n\n<!-- Overlay: {overlay_path.name} -->\n\n{content}")

        # Combine into single file
        bundled_prompt = base_prompt + "".join(overlay_content)
        self.system_prompt_path.write_text(bundled_prompt, encoding='utf-8')

        self.logger.debug(f"System prompt bundled: {self.system_prompt_path}")

    def _create_mcp_config(self) -> None:
        """Create isolated MCP config with isolated data path."""
        self.logger.debug("Creating isolated MCP config...")

        # Read original MCP config
        if not self.config.mcp_config_path:
            raise RuntimeError("MCP config path not set in config")

        with open(self.config.mcp_config_path, 'r', encoding='utf-8') as f:
            mcp_config = json.load(f)

        # Update data path to isolated location
        if "mcpServers" in mcp_config and "gtd-graph-memory" in mcp_config["mcpServers"]:
            server_config = mcp_config["mcpServers"]["gtd-graph-memory"]

            # Update BASE_PATH to isolated data directory
            if "env" not in server_config:
                server_config["env"] = {}
            server_config["env"]["BASE_PATH"] = str(self.data_dir.resolve())

            # Update MCP_CALL_LOG to isolated log file
            mcp_log_path = self.data_dir / "mcp-calls.log"
            server_config["env"]["MCP_CALL_LOG"] = str(mcp_log_path.resolve())

        # Write isolated config
        with open(self.mcp_config_path, 'w', encoding='utf-8') as f:
            json.dump(mcp_config, f, indent=2)

        self.logger.debug(f"MCP config created: {self.mcp_config_path}")
        self.logger.debug(f"Data directory: {self.data_dir}")

    def cleanup(self) -> None:
        """Remove test installation and workspace directories."""
        self.logger.info("Cleaning up test installation...")

        if self.install_dir.exists():
            shutil.rmtree(self.install_dir)
            self.logger.debug(f"Removed: {self.install_dir}")

        if self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
            self.logger.debug(f"Removed: {self.workspace_dir}")

        self.logger.info("Test installation cleaned up")

    def get_system_prompt_path(self) -> Path:
        """Get path to bundled system prompt in installation.

        Returns:
            Path to system prompt file
        """
        return self.system_prompt_path

    def get_mcp_config_path(self) -> Path:
        """Get path to MCP config in installation.

        Returns:
            Path to MCP config file
        """
        return self.mcp_config_path

    def get_workspace_dir(self) -> Path:
        """Get working directory for test execution.

        Returns:
            Path to workspace directory
        """
        return self.workspace_dir

    def get_mcp_log_path(self) -> Path:
        """Get path to MCP call log in isolated installation.

        Returns:
            Path to MCP log file
        """
        return self.data_dir / "mcp-calls.log"


def create_test_installation(config: Config, force: bool = False) -> TestInstallation:
    """Create and build a test installation.

    Args:
        config: Test configuration
        force: If True, remove existing installation first

    Returns:
        TestInstallation instance

    Raises:
        RuntimeError: If installation fails
    """
    installation = TestInstallation(config)
    installation.build(force=force)
    return installation
