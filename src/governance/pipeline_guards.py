"""Pipeline guards for the agentic orchestrator.

These guards run between pipeline steps to prevent phantom implementations,
hallucinated test coverage, and inconsistent reports from advancing through
the pipeline. Each guard returns a list of error strings (empty = pass).

Guards are organized by priority:
  P0 - Artifact existence, test execution
  P1 - Report-to-git consistency, reviewer precondition
  P2 - Syntax validation, path normalization
  P3 - Structured output validation (via Pydantic in the orchestrator)
"""

from __future__ import annotations

import ast
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Allowed top-level directories for created/modified files
_ALLOWED_PREFIXES = ("src/", "tests/", "migrations/", "scripts/", "docs/")


# ---------------------------------------------------------------------------
# P0: Artifact Existence Guard
# ---------------------------------------------------------------------------


def verify_artifacts_exist(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[str]:
    """Verify that every claimed file actually exists on disk.

    Args:
        files_created: Paths the developer claims to have created.
        files_modified: Paths the developer claims to have modified.
        workspace: Project root directory.

    Returns:
        List of error strings for files that don't exist.
    """
    errors: list[str] = []
    for file_path in files_created:
        full_path = workspace / file_path
        if not full_path.exists():
            errors.append(f"Claimed created file not found on disk: {file_path}")
        elif not full_path.is_file():
            errors.append(f"Path exists but is not a file: {file_path}")

    for file_path in files_modified:
        full_path = workspace / file_path
        if not full_path.exists():
            errors.append(f"Claimed modified file not found on disk: {file_path}")

    if errors:
        logger.error("Artifact existence check failed: %s", errors)
    else:
        logger.info(
            "Artifact existence check passed: %d created, %d modified",
            len(files_created),
            len(files_modified),
        )
    return errors


# ---------------------------------------------------------------------------
# P0: Test Execution Guard
# ---------------------------------------------------------------------------


def verify_tests_pass(workspace: Path, timeout: int = 120) -> list[str]:
    """Actually run pytest and verify tests pass.

    Args:
        workspace: Project root directory.
        timeout: Maximum seconds to wait for test execution.

    Returns:
        List of error strings if tests fail or cannot be run.
    """
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--tb=short", "-q", "--no-header"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            # Extract last few lines for context
            output_lines = (result.stdout + result.stderr).strip().splitlines()
            summary = "\n".join(output_lines[-10:]) if output_lines else "No output"
            errors.append(
                f"Test execution failed (exit code {result.returncode}):\n{summary}"
            )
            logger.error("Test execution failed: exit_code=%d", result.returncode)
        else:
            logger.info("Test execution passed")
    except subprocess.TimeoutExpired:
        errors.append(f"Test execution timed out after {timeout}s")
        logger.error("Test execution timed out after %ds", timeout)
    except FileNotFoundError:
        errors.append("'uv' command not found — cannot execute tests")
        logger.error("uv command not found")
    return errors


# ---------------------------------------------------------------------------
# P1: Report-to-Git Consistency Guard
# ---------------------------------------------------------------------------


def verify_report_matches_git(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[str]:
    """Cross-reference the implementation report against git status.

    Detects:
      - Files claimed in the report but not tracked/changed in git (phantom files).
      - Files changed in git but not mentioned in the report (undocumented changes).

    Args:
        files_created: Paths claimed as created.
        files_modified: Paths claimed as modified.
        workspace: Project root directory.

    Returns:
        List of error strings for inconsistencies.
    """
    errors: list[str] = []
    try:
        # Get all files changed since last commit (staged + unstaged + untracked)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=10,
        )
        tracked_changes = (
            set(result.stdout.strip().splitlines()) if result.stdout.strip() else set()
        )

        # Also get untracked files
        result_untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=10,
        )
        untracked = (
            set(result_untracked.stdout.strip().splitlines())
            if result_untracked.stdout.strip()
            else set()
        )

        git_changed = tracked_changes | untracked

        # Filter to only source/test files (ignore docs, configs)
        source_changed = {
            f
            for f in git_changed
            if any(f.startswith(prefix) for prefix in ("src/", "tests/"))
        }

        claimed = set(files_created + files_modified)

        # Phantom files: claimed but not in git
        phantom = claimed - git_changed
        for f in sorted(phantom):
            # Only flag if it's a source file path
            if any(f.startswith(prefix) for prefix in ("src/", "tests/")):
                errors.append(f"File claimed in report but has no git changes: {f}")

        # Undocumented: changed in git (source only) but not in report
        undocumented = source_changed - claimed
        for f in sorted(undocumented):
            # Warning-level: these are informational but worth flagging
            logger.warning("File changed in git but not documented in report: %s", f)

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("Git consistency check skipped: %s", e)
        # Non-fatal: skip this guard if git is unavailable
    return errors


# ---------------------------------------------------------------------------
# P1: Reviewer Precondition Guard
# ---------------------------------------------------------------------------


def verify_reviewer_precondition(
    files_created: list[str],
    workspace: Path,
) -> list[str]:
    """Ensure actual source files exist before allowing reviewer to run.

    The reviewer must have real code to inspect. This guard prevents
    reviewing phantom implementations.

    Args:
        files_created: Paths the developer claims to have created.
        workspace: Project root directory.

    Returns:
        List of error strings if preconditions are not met.
    """
    errors: list[str] = []
    source_files = [f for f in files_created if f.startswith(("src/", "tests/"))]

    if not source_files:
        errors.append("No source files declared in implementation — nothing to review")
        return errors

    existing = [f for f in source_files if (workspace / f).exists()]
    if not existing:
        errors.append(
            f"None of the declared source files exist on disk: {source_files}. "
            "Cannot proceed to review."
        )
    elif len(existing) < len(source_files):
        missing = [f for f in source_files if not (workspace / f).exists()]
        errors.append(f"Some declared source files are missing: {missing}")

    return errors


# ---------------------------------------------------------------------------
# P2: Syntax Validation Guard
# ---------------------------------------------------------------------------


def verify_syntax(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[str]:
    """Validate that all Python files have correct syntax.

    Args:
        files_created: Paths claimed as created.
        files_modified: Paths claimed as modified.
        workspace: Project root directory.

    Returns:
        List of error strings for files with syntax errors.
    """
    errors: list[str] = []
    all_files = files_created + files_modified

    for file_path in all_files:
        full_path = workspace / file_path
        if not full_path.exists():
            continue  # Already caught by artifact existence guard
        if not file_path.endswith(".py"):
            continue

        try:
            source = full_path.read_text(encoding="utf-8")
            ast.parse(source, filename=file_path)
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path} (line {e.lineno}): {e.msg}")
        except UnicodeDecodeError:
            errors.append(f"Cannot decode {file_path} as UTF-8")

    if errors:
        logger.error("Syntax validation failed: %s", errors)
    else:
        py_files = [f for f in all_files if f.endswith(".py")]
        logger.info("Syntax validation passed for %d Python files", len(py_files))
    return errors


# ---------------------------------------------------------------------------
# P2: Path Normalization & Validation Guard
# ---------------------------------------------------------------------------


def verify_paths_valid(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[str]:
    """Validate that all declared paths are within expected project boundaries.

    Detects:
      - Paths that escape the project root (e.g., ../../../etc/passwd)
      - Paths not under recognized top-level directories
      - Inconsistent paths pointing to the same logical location

    Args:
        files_created: Paths claimed as created.
        files_modified: Paths claimed as modified.
        workspace: Project root directory.

    Returns:
        List of error strings for invalid paths.
    """
    errors: list[str] = []
    all_paths = files_created + files_modified

    if not all_paths:
        errors.append("Implementation declares no files created or modified")
        return errors

    seen_resolved: dict[Path, str] = {}

    for file_path in all_paths:
        # Check for path traversal
        try:
            resolved = (workspace / file_path).resolve()
        except (OSError, ValueError) as e:
            errors.append(f"Invalid path '{file_path}': {e}")
            continue

        if not resolved.is_relative_to(workspace.resolve()):
            errors.append(f"Path escapes project root: {file_path}")
            continue

        # Check allowed prefixes
        if not any(file_path.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
            errors.append(
                f"Path '{file_path}' is not under an expected directory "
                f"({', '.join(_ALLOWED_PREFIXES)})"
            )

        # Detect duplicates that resolve to same location
        if resolved in seen_resolved:
            errors.append(
                f"Duplicate path detected: '{file_path}' resolves to same "
                f"location as '{seen_resolved[resolved]}'"
            )
        else:
            seen_resolved[resolved] = file_path

    return errors


# ---------------------------------------------------------------------------
# Guard Runner
# ---------------------------------------------------------------------------

# Guard definitions grouped by pipeline step
DEVELOPER_GUARDS = [
    ("artifact_existence", verify_artifacts_exist),
    ("path_validation", verify_paths_valid),
    ("syntax_validation", verify_syntax),
]

TESTER_GUARDS = [
    ("test_execution", verify_tests_pass),
]

REVIEWER_GUARDS = [
    ("reviewer_precondition", verify_reviewer_precondition),
    ("report_git_consistency", verify_report_matches_git),
]


def run_developer_guards(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[tuple[str, list[str]]]:
    """Run all post-developer step guards.

    Args:
        files_created: Paths the developer claims to have created.
        files_modified: Paths the developer claims to have modified.
        workspace: Project root directory.

    Returns:
        List of (guard_name, errors) tuples. Only failed guards are included.
    """
    failures: list[tuple[str, list[str]]] = []

    # Path validation
    path_errors = verify_paths_valid(files_created, files_modified, workspace)
    if path_errors:
        failures.append(("path_validation", path_errors))

    # Artifact existence (only run if paths are valid)
    if not path_errors:
        exist_errors = verify_artifacts_exist(files_created, files_modified, workspace)
        if exist_errors:
            failures.append(("artifact_existence", exist_errors))

    # Syntax validation (only run if files exist)
    if not path_errors and not any(
        name == "artifact_existence" for name, _ in failures
    ):
        syntax_errors = verify_syntax(files_created, files_modified, workspace)
        if syntax_errors:
            failures.append(("syntax_validation", syntax_errors))

    return failures


def run_tester_guards(workspace: Path) -> list[tuple[str, list[str]]]:
    """Run all post-tester step guards.

    Args:
        workspace: Project root directory.

    Returns:
        List of (guard_name, errors) tuples. Only failed guards are included.
    """
    failures: list[tuple[str, list[str]]] = []

    test_errors = verify_tests_pass(workspace)
    if test_errors:
        failures.append(("test_execution", test_errors))

    return failures


def run_reviewer_guards(
    files_created: list[str],
    files_modified: list[str],
    workspace: Path,
) -> list[tuple[str, list[str]]]:
    """Run all pre-reviewer step guards.

    Args:
        files_created: Paths the developer claims to have created.
        files_modified: Paths the developer claims to have modified.
        workspace: Project root directory.

    Returns:
        List of (guard_name, errors) tuples. Only failed guards are included.
    """
    failures: list[tuple[str, list[str]]] = []

    precondition_errors = verify_reviewer_precondition(files_created, workspace)
    if precondition_errors:
        failures.append(("reviewer_precondition", precondition_errors))

    git_errors = verify_report_matches_git(files_created, files_modified, workspace)
    if git_errors:
        failures.append(("report_git_consistency", git_errors))

    return failures


def run_all_guards_for_step(
    step: str,
    implementation: dict[str, Any],
    workspace: Path,
) -> list[tuple[str, list[str]]]:
    """Run the appropriate guards for a given pipeline step.

    This is the main entry point used by the orchestrator to enforce
    guards between pipeline steps.

    Args:
        step: Pipeline step name ("developer", "tester", "reviewer").
        implementation: Implementation metadata dictionary containing
            files_created, files_modified, etc.
        workspace: Project root directory.

    Returns:
        List of (guard_name, errors) tuples. Empty list means all passed.

    Raises:
        ValueError: If step name is not recognized.
    """
    files_created = implementation.get("files_created", [])
    files_modified = implementation.get("files_modified", [])

    if step == "developer":
        return run_developer_guards(files_created, files_modified, workspace)
    elif step == "tester":
        return run_tester_guards(workspace)
    elif step == "reviewer":
        return run_reviewer_guards(files_created, files_modified, workspace)
    else:
        raise ValueError(f"Unknown pipeline step: {step}")
