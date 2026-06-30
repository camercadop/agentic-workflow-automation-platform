"""Tool definitions and executor for agentic LLM interactions.

Converts skill descriptions into OpenAI-compatible tool schemas and
provides execution logic for each tool. The tool loop allows agents
to call tools iteratively until they produce a final text response.
"""

from __future__ import annotations

import ast
import json as _json
import logging
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Workspace root — resolved at import time, overridable via env var
_WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT", Path.cwd()))

# Maximum iterations to prevent infinite tool-call loops
MAX_TOOL_ITERATIONS = 20

# Tracks files successfully written during the current tool-calling session
_WRITTEN_FILES: list[str] = []


# ---------------------------------------------------------------------------
# Tool Schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

_SCHEMAS_PATH = Path(__file__).parent / "tool_schemas.json"
TOOL_SCHEMAS: list[dict[str, Any]] = _json.loads(
    _SCHEMAS_PATH.read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# Tool Execution Functions
# ---------------------------------------------------------------------------

# Allowed commands (prefix match) to prevent arbitrary code execution
_ALLOWED_COMMAND_PREFIXES = (
    "uv run ruff",
    "uv run mypy",
    "uv run pytest",
    "ruff",
    "mypy",
    "pytest",
    "cat ",
    "head ",
    "tail ",
    "find ",
    "ls ",
    "grep ",
)


def _resolve_path(relative_path: str) -> Path:
    """Resolve a relative path against the workspace, preventing traversal.

    Args:
        relative_path: Path relative to workspace root.

    Returns:
        Resolved absolute path.

    Raises:
        ValueError: If path escapes workspace root.
    """
    resolved = (_WORKSPACE / relative_path).resolve()
    if not resolved.is_relative_to(_WORKSPACE.resolve()):
        raise ValueError(f"Path escapes workspace root: {relative_path}")
    return resolved


def execute_read_file(path: str) -> str:
    """Read a file and return its content.

    Args:
        path: Relative path from workspace root.

    Returns:
        File content or error message.
    """
    try:
        resolved = _resolve_path(path)
        if not resolved.exists():
            return f"Error: File not found: {path}"
        if not resolved.is_file():
            return f"Error: Not a file: {path}"
        content = resolved.read_text(encoding="utf-8")
        # Truncate very large files
        if len(content) > 50_000:
            return content[:50_000] + f"\n\n[... truncated, {len(content)} total chars]"
        return content
    except (ValueError, OSError) as e:
        return f"Error: {e}"


def execute_write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories.

    Args:
        path: Relative path from workspace root.
        content: Content to write.

    Returns:
        Success confirmation or error message.
    """
    try:
        resolved = _resolve_path(path)
        # Only allow writing under src/, tests/, docs/
        allowed_write_prefixes = ("src/", "tests/", "docs/")
        if not any(path.startswith(p) for p in allowed_write_prefixes):
            return f"Error: Writing only allowed under {allowed_write_prefixes}"
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        # Quick syntax check for Python files
        if path.endswith(".py"):
            try:
                ast.parse(content, filename=path)
            except SyntaxError as e:
                return (
                    f"Warning: File written but has syntax error "
                    f"at line {e.lineno}: {e.msg}"
                )
        _WRITTEN_FILES.append(path)
        logger.info("Tool write_file: wrote %d bytes to %s", len(content), path)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except (ValueError, OSError) as e:
        return f"Error: {e}"


def execute_list_directory(path: str) -> str:
    """List directory contents.

    Args:
        path: Relative path from workspace root.

    Returns:
        Directory listing or error message.
    """
    try:
        resolved = _resolve_path(path)
        if not resolved.exists():
            return f"Error: Directory not found: {path}"
        if not resolved.is_dir():
            return f"Error: Not a directory: {path}"
        entries: list[str] = []
        for entry in sorted(resolved.iterdir()):
            # Skip hidden and common noise directories
            if entry.name.startswith(".") or entry.name in (
                "__pycache__",
                "node_modules",
                ".git",
            ):
                continue
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        return "\n".join(entries) if entries else "(empty directory)"
    except (ValueError, OSError) as e:
        return f"Error: {e}"


def _load_test_env_overrides() -> dict[str, str]:
    """Load test environment overrides from .env.test file."""
    overrides: dict[str, str] = {}
    env_test_path = _WORKSPACE / ".env.test"
    if not env_test_path.exists():
        # Fallback: check relative to this file's project root
        env_test_path = Path(__file__).resolve().parents[3] / ".env.test"
    if env_test_path.exists():
        for line in env_test_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                overrides[key.strip()] = value.strip()
    return overrides


def execute_run_command(command: str) -> str:
    """Execute a shell command with safety restrictions.

    Args:
        command: Shell command to run.

    Returns:
        Command output (stdout + stderr + exit code) or error message.
    """
    # Safety: only allow whitelisted command prefixes
    cmd_stripped = command.strip()
    if not any(cmd_stripped.startswith(prefix) for prefix in _ALLOWED_COMMAND_PREFIXES):
        return (
            f"Error: Command not allowed. Only these prefixes are permitted: "
            f"{_ALLOWED_COMMAND_PREFIXES}"
        )

    # Build environment: inherit parent env but override for test isolation
    env = os.environ.copy()
    if any(cmd_stripped.startswith(p) for p in ("uv run pytest", "pytest")):
        env.update(_load_test_env_overrides())

    try:
        result = subprocess.run(
            cmd_stripped,
            shell=True,
            cwd=str(_WORKSPACE),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        output_parts: list[str] = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")
        output_parts.append(f"[exit code: {result.returncode}]")
        full_output = "\n".join(output_parts)
        # Truncate if too long
        if len(full_output) > 10_000:
            full_output = (
                full_output[:10_000] + f"\n[... truncated, {len(full_output)} chars]"
            )
        logger.info(
            "Tool run_command: '%s' exit_code=%d", cmd_stripped, result.returncode
        )
        return full_output
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 120s: {command}"
    except OSError as e:
        return f"Error running command: {e}"


# ---------------------------------------------------------------------------
# Tool Dispatch
# ---------------------------------------------------------------------------

_TOOL_EXECUTORS: dict[str, Callable[..., str]] = {
    "read_file": execute_read_file,
    "write_file": execute_write_file,
    "list_directory": execute_list_directory,
    "run_command": execute_run_command,
}


def execute_tool_call(name: str, arguments: dict[str, Any]) -> str:
    """Dispatch a tool call to the appropriate executor.

    Args:
        name: Tool function name.
        arguments: Parsed arguments dictionary.

    Returns:
        Tool execution result as a string.
    """
    executor = _TOOL_EXECUTORS.get(name)
    if executor is None:
        return f"Error: Unknown tool '{name}'"
    try:
        return executor(**arguments)
    except TypeError as e:
        return f"Error: Invalid arguments for '{name}': {e}"


def set_workspace(workspace: Path) -> None:
    """Override the workspace root path.

    Also resets the written-files tracker for a fresh session.

    Args:
        workspace: New workspace root path.
    """
    global _WORKSPACE  # noqa: PLW0603
    _WORKSPACE = workspace.resolve()
    _WRITTEN_FILES.clear()
    logger.info("Tool workspace set to: %s", _WORKSPACE)


def get_written_files() -> list[str]:
    """Return the list of file paths written during the current session.

    Returns:
        List of relative paths that were successfully written via write_file.
    """
    return list(_WRITTEN_FILES)


def clear_written_files() -> None:
    """Reset the written-files tracker (for testing)."""
    _WRITTEN_FILES.clear()
