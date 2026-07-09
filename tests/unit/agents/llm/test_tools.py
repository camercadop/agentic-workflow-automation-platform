"""Unit tests for src/agents/llm/tools.py."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.llm.tools import (
    _resolve_path,
    clear_written_files,
    execute_list_directory,
    execute_read_file,
    execute_run_command,
    execute_tool_call,
    execute_write_file,
    get_modified_files,
    get_written_files,
    set_workspace,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    set_workspace(tmp_path)
    return tmp_path


class TestResolvePath:
    def test_valid_path(self, workspace: Path) -> None:
        resolved = _resolve_path("src/foo.py")
        assert resolved == workspace / "src" / "foo.py"

    def test_traversal_blocked(self, workspace: Path) -> None:
        with pytest.raises(ValueError, match="escapes workspace"):
            _resolve_path("../../etc/passwd")


class TestReadFile:
    def test_read_existing(self, workspace: Path) -> None:
        (workspace / "test.txt").write_text("hello")
        assert execute_read_file("test.txt") == "hello"

    def test_read_nonexistent(self, workspace: Path) -> None:
        assert "not found" in execute_read_file("missing.txt").lower()

    def test_read_directory(self, workspace: Path) -> None:
        (workspace / "adir").mkdir()
        assert "not a file" in execute_read_file("adir").lower()

    def test_read_large_file_truncated(self, workspace: Path) -> None:
        (workspace / "big.txt").write_text("x" * 60_000)
        assert "truncated" in execute_read_file("big.txt")


class TestWriteFile:
    def test_write_new_file(self, workspace: Path) -> None:
        result = execute_write_file("src/new.py", "print('hi')\n")
        assert "Successfully wrote" in result
        assert "src/new.py" in get_written_files()

    def test_write_creates_parents(self, workspace: Path) -> None:
        execute_write_file("src/deep/nested/file.py", "x = 1\n")
        assert (workspace / "src" / "deep" / "nested" / "file.py").exists()

    def test_write_outside_allowed_dirs(self, workspace: Path) -> None:
        assert "Error" in execute_write_file("config/bad.py", "x")

    def test_write_syntax_error_warning(self, workspace: Path) -> None:
        result = execute_write_file("src/bad.py", "def f(\n")
        assert "syntax error" in result.lower()

    def test_modify_existing_file(self, workspace: Path) -> None:
        (workspace / "src").mkdir(exist_ok=True)
        (workspace / "src" / "existing.py").write_text("old")
        execute_write_file("src/existing.py", "new = 1\n")
        assert "src/existing.py" in get_modified_files()


class TestListDirectory:
    def test_list_existing(self, workspace: Path) -> None:
        (workspace / "src").mkdir()
        (workspace / "src" / "a.py").write_text("")
        (workspace / "src" / "b.py").write_text("")
        result = execute_list_directory("src")
        assert "a.py" in result
        assert "b.py" in result

    def test_list_nonexistent(self, workspace: Path) -> None:
        assert "not found" in execute_list_directory("nope").lower()

    def test_list_file_not_dir(self, workspace: Path) -> None:
        (workspace / "f.txt").write_text("")
        assert "not a directory" in execute_list_directory("f.txt").lower()

    def test_list_hides_pycache(self, workspace: Path) -> None:
        (workspace / "src").mkdir()
        (workspace / "src" / "__pycache__").mkdir()
        (workspace / "src" / "real.py").write_text("")
        result = execute_list_directory("src")
        assert "__pycache__" not in result


class TestRunCommand:
    def test_allowed_command(self, workspace: Path) -> None:
        result = execute_run_command("ls .")
        assert "[exit code:" in result

    def test_disallowed_command(self, workspace: Path) -> None:
        assert "not allowed" in execute_run_command("rm -rf /").lower()

    def test_command_timeout(self, workspace: Path) -> None:
        with patch(
            "src.agents.llm.tools.subprocess.run",
            side_effect=subprocess.TimeoutExpired("cmd", 120),
        ):
            result = execute_run_command("uv run pytest")
            assert "timed out" in result.lower()


class TestToolDispatch:
    def test_unknown_tool(self, workspace: Path) -> None:
        assert "Unknown tool" in execute_tool_call("nonexistent", {})

    def test_invalid_arguments(self, workspace: Path) -> None:
        assert "Invalid arguments" in execute_tool_call("read_file", {"wrong": "x"})

    def test_dispatch_read_file(self, workspace: Path) -> None:
        (workspace / "hi.txt").write_text("content")
        assert execute_tool_call("read_file", {"path": "hi.txt"}) == "content"


class TestSessionTracking:
    def test_clear_written_files(self, workspace: Path) -> None:
        execute_write_file("src/a.py", "x = 1\n")
        assert len(get_written_files()) > 0
        clear_written_files()
        assert get_written_files() == []
        assert get_modified_files() == []
