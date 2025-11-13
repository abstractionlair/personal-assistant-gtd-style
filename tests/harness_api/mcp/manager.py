"""Lifecycle management for local MCP servers used by the API harness."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(slots=True)
class McpServerSpec:
    """Definition of a single MCP server process."""

    name: str
    command: list[str]
    cwd: Optional[Path] = None
    env: Dict[str, str] = field(default_factory=dict)
    log_path: Optional[Path] = None


@dataclass(slots=True)
class McpServerProcess:
    spec: McpServerSpec
    process: subprocess.Popen[str]

    def stop(self, timeout_s: float = 10.0) -> None:
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            self.process.kill()


class McpLifecycleManager:
    """Starts and stops MCP server processes for the harness."""

    def __init__(self, specs: Iterable[McpServerSpec]) -> None:
        self.specs = list(specs)
        self.processes: Dict[str, McpServerProcess] = {}

    def start_all(self) -> None:
        if self.processes:
            return
        for spec in self.specs:
            env = os.environ.copy()
            env.update(spec.env)
            if spec.log_path:
                spec.log_path.parent.mkdir(parents=True, exist_ok=True)
                env["MCP_CALL_LOG"] = str(spec.log_path)
            cwd = str(spec.cwd) if spec.cwd else None
            proc = subprocess.Popen(
                spec.command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.processes[spec.name] = McpServerProcess(spec=spec, process=proc)
        # TODO: replace sleep with health probe once MCP exposes readiness signal.
        time.sleep(2.0)

    def stop_all(self) -> None:
        for process in self.processes.values():
            process.stop()
        self.processes.clear()

    def __enter__(self) -> "McpLifecycleManager":
        self.start_all()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.stop_all()


def default_graph_memory_spec(
    data_dir: Path,
    log_path: Optional[Path] = None,
) -> McpServerSpec:
    """Return a spec for the graph-memory MCP server bundled with the repo."""

    dist_entry = REPO_ROOT / "src" / "graph-memory-core" / "mcp" / "dist" / "index.js"
    if not dist_entry.exists():
        raise FileNotFoundError(
            "Graph memory MCP dist build not found. Run the build before starting harness." \
        )
    command = ["node", str(dist_entry)]
    env = {"BASE_PATH": str(data_dir)}
    return McpServerSpec(
        name="gtd-graph-memory",
        command=command,
        env=env,
        log_path=log_path,
    )


__all__ = [
    "McpLifecycleManager",
    "McpServerProcess",
    "McpServerSpec",
    "default_graph_memory_spec",
]
