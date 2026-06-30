"""Unit tests for pipeline guards.

Tests the governance pipeline guards that prevent phantom implementations,
hallucinated outputs, and inconsistent reports from advancing through the pipeline.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.governance.pipeline_errors import PipelineGateError
from src.governance.pipeline_guards import (
    run_all_guards_for_step,
    run_developer_guards,
    run_reviewer_guards,
    run_tester_guards,
    verify_artifacts_exist,
    verify_paths_valid,
    verify_reviewer_precondition,
    verify_syntax,
    verify_tests_pass,
)


class TestVerifyArtifactsExist:
    """Tests for the artifact existence guard."""

    def test_all_files_exist(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "plugins").mkdir(parents=True)
        (tmp_path / "src" / "plugins" / "foo.py").write_text("x = 1")

        errors = verify_artifacts_exist(
            files_created=["src/plugins/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert errors == []

    def test_created_file_missing(self, tmp_path: Path) -> None:
        errors = verify_artifacts_exist(
            files_created=["src/plugins/phantom.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "phantom.py" in errors[0]
        assert "not found on disk" in errors[0]

    def test_modified_file_missing(self, tmp_path: Path) -> None:
        errors = verify_artifacts_exist(
            files_created=[],
            files_modified=["src/core/registry.py"],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "registry.py" in errors[0]

    def test_path_is_directory_not_file(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "plugins").mkdir(parents=True)

        errors = verify_artifacts_exist(
            files_created=["src/plugins"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "not a file" in errors[0]

    def test_empty_lists_pass(self, tmp_path: Path) -> None:
        errors = verify_artifacts_exist(
            files_created=[],
            files_modified=[],
            workspace=tmp_path,
        )
        assert errors == []


class TestVerifyTestsPass:
    """Tests for the test execution guard."""

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_tests_pass(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        errors = verify_tests_pass(tmp_path)
        assert errors == []

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_tests_fail(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAILED test_foo.py::test_bar\n1 failed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        errors = verify_tests_pass(tmp_path)
        assert len(errors) == 1
        assert "exit code 1" in errors[0]

    @patch(
        "src.governance.pipeline_guards.subprocess.run",
        side_effect=FileNotFoundError("uv not found"),
    )
    def test_uv_not_found(self, mock_run: object, tmp_path: Path) -> None:
        errors = verify_tests_pass(tmp_path)
        assert len(errors) == 1
        assert "'uv' command not found" in errors[0]

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_timeout(self, mock_run: object, tmp_path: Path) -> None:
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)  # type: ignore[attr-defined]

        errors = verify_tests_pass(tmp_path, timeout=120)
        assert len(errors) == 1
        assert "timed out" in errors[0]


class TestVerifySyntax:
    """Tests for the syntax validation guard."""

    def test_valid_python(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "valid.py").write_text("def foo():\n    return 42\n")

        errors = verify_syntax(
            files_created=["src/valid.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert errors == []

    def test_invalid_python(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "broken.py").write_text("def foo(\n")

        errors = verify_syntax(
            files_created=["src/broken.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "Syntax error" in errors[0]
        assert "broken.py" in errors[0]

    def test_skips_non_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "readme.md").write_text("# Hello {{{")

        errors = verify_syntax(
            files_created=["docs/readme.md"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert errors == []

    def test_skips_missing_files(self, tmp_path: Path) -> None:
        errors = verify_syntax(
            files_created=["src/missing.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert errors == []


class TestVerifyPathsValid:
    """Tests for the path normalization/validation guard."""

    def test_valid_paths(self, tmp_path: Path) -> None:
        errors = verify_paths_valid(
            files_created=["src/plugins/foo.py"],
            files_modified=["tests/unit/test_foo.py"],
            workspace=tmp_path,
        )
        assert errors == []

    def test_empty_file_lists(self, tmp_path: Path) -> None:
        errors = verify_paths_valid(
            files_created=[],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "no files created or modified" in errors[0].lower()

    def test_path_outside_allowed_prefixes(self, tmp_path: Path) -> None:
        errors = verify_paths_valid(
            files_created=["random_dir/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "not under an expected directory" in errors[0]

    def test_exact_duplicate_paths_are_deduplicated(self, tmp_path: Path) -> None:
        """Exact-string duplicates are silently deduplicated (not errors)."""
        errors = verify_paths_valid(
            files_created=["src/foo.py", "src/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(errors) == 0

    def test_ambiguous_paths_detected(self, tmp_path: Path) -> None:
        """Different path strings resolving to the same file are flagged."""
        errors = verify_paths_valid(
            files_created=["src/foo.py", "./src/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert any("Ambiguous paths" in e for e in errors)

    def test_same_path_in_created_and_modified_is_ok(self, tmp_path: Path) -> None:
        """Same path in both created and modified lists is deduplicated."""
        errors = verify_paths_valid(
            files_created=["src/foo.py"],
            files_modified=["src/foo.py"],
            workspace=tmp_path,
        )
        assert len(errors) == 0

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        errors = verify_paths_valid(
            files_created=["src/../../../etc/passwd"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert any("escapes project root" in e for e in errors)


class TestVerifyReviewerPrecondition:
    """Tests for the reviewer precondition guard."""

    def test_source_files_exist(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "plugins").mkdir(parents=True)
        (tmp_path / "src" / "plugins" / "cond.py").write_text("x = 1")

        errors = verify_reviewer_precondition(
            files_created=["src/plugins/cond.py"],
            workspace=tmp_path,
        )
        assert errors == []

    def test_no_source_files_declared(self, tmp_path: Path) -> None:
        errors = verify_reviewer_precondition(
            files_created=["docs/adr/adr-010.md"],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "No source files" in errors[0]

    def test_source_files_missing(self, tmp_path: Path) -> None:
        errors = verify_reviewer_precondition(
            files_created=["src/plugins/phantom.py"],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "None of the declared source files exist" in errors[0]

    def test_partial_files_missing(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "plugins").mkdir(parents=True)
        (tmp_path / "src" / "plugins" / "real.py").write_text("x = 1")

        errors = verify_reviewer_precondition(
            files_created=["src/plugins/real.py", "src/plugins/phantom.py"],
            workspace=tmp_path,
        )
        assert len(errors) == 1
        assert "missing" in errors[0].lower()


class TestRunDeveloperGuards:
    """Tests for the combined developer guard runner."""

    def test_all_pass(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "plugins").mkdir(parents=True)
        (tmp_path / "src" / "plugins" / "foo.py").write_text("x = 1\n")

        failures = run_developer_guards(
            files_created=["src/plugins/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert failures == []

    def test_fails_on_phantom_file(self, tmp_path: Path) -> None:
        failures = run_developer_guards(
            files_created=["src/plugins/phantom.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(failures) >= 1
        guard_names = [name for name, _ in failures]
        assert "artifact_existence" in guard_names

    def test_fails_on_invalid_path(self, tmp_path: Path) -> None:
        failures = run_developer_guards(
            files_created=["random_place/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(failures) >= 1
        guard_names = [name for name, _ in failures]
        assert "path_validation" in guard_names

    def test_fails_on_syntax_error(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "bad.py").write_text("def (broken:\n")

        failures = run_developer_guards(
            files_created=["src/bad.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(failures) >= 1
        guard_names = [name for name, _ in failures]
        assert "syntax_validation" in guard_names


class TestRunTesterGuards:
    """Tests for the combined tester guard runner."""

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_pass_when_tests_succeed(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        failures = run_tester_guards(tmp_path)
        assert failures == []

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_fail_when_tests_fail(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        failures = run_tester_guards(tmp_path)
        assert len(failures) == 1
        assert failures[0][0] == "test_execution"


class TestRunReviewerGuards:
    """Tests for the combined reviewer guard runner."""

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_pass_when_files_exist(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        # Mock git commands to return the file as changed
        mock_result = MagicMock()
        mock_result.stdout = "src/foo.py\n"
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").write_text("x = 1")

        failures = run_reviewer_guards(
            files_created=["src/foo.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert failures == []

    def test_fail_when_files_missing(self, tmp_path: Path) -> None:
        failures = run_reviewer_guards(
            files_created=["src/phantom.py"],
            files_modified=[],
            workspace=tmp_path,
        )
        assert len(failures) >= 1
        guard_names = [name for name, _ in failures]
        assert "reviewer_precondition" in guard_names


class TestRunAllGuardsForStep:
    """Tests for the unified guard runner entry point."""

    def test_unknown_step_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unknown pipeline step"):
            run_all_guards_for_step("unknown_step", {}, tmp_path)

    def test_developer_step(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").write_text("x = 1\n")

        impl = {"files_created": ["src/foo.py"], "files_modified": []}
        failures = run_all_guards_for_step("developer", impl, tmp_path)
        assert failures == []

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_tester_step(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        failures = run_all_guards_for_step("tester", {}, tmp_path)
        assert failures == []

    @patch("src.governance.pipeline_guards.subprocess.run")
    def test_reviewer_step(self, mock_run: object, tmp_path: Path) -> None:
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.stdout = "src/foo.py\n"
        mock_run.return_value = mock_result  # type: ignore[attr-defined]

        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").write_text("x = 1")

        impl = {"files_created": ["src/foo.py"], "files_modified": []}
        failures = run_all_guards_for_step("reviewer", impl, tmp_path)
        assert failures == []


class TestPipelineGateError:
    """Tests for the custom pipeline error class."""

    def test_error_message_format(self) -> None:
        err = PipelineGateError("developer", ["file missing", "syntax error"])
        assert err.step == "developer"
        assert len(err.errors) == 2
        assert "developer" in str(err)
        assert "file missing" in str(err)

    def test_single_error(self) -> None:
        err = PipelineGateError("tester", ["tests failed"])
        assert "tester" in str(err)
        assert "tests failed" in str(err)
