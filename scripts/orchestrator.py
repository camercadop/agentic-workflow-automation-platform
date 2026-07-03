#!/usr/bin/env python3
"""Semi-Automatic Agent Orchestrator CLI.

Provides semi-automatic orchestration of AI agents for development tasks.
Automates routine steps while maintaining human oversight and manual checkpoints.
"""

import json
import logging
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False) -> None:
    """Configure logging with colored console output via Rich.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(name)s: %(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_level=True,
                show_path=verbose,
                markup=True,
            )
        ],
        force=True,
    )
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Load .env from workspace root (if present)
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.llm.client import (  # noqa: E402
    LLMClient,
    LLMConfigError,
    LLMError,
    load_system_prompt,
    parse_json_response,
)
from src.agents.llm.tools import (  # noqa: E402
    get_modified_files,
    get_written_files,
)
from src.agents.llm.tools import set_workspace as set_tool_workspace  # noqa: E402
from src.governance.pipeline_errors import PipelineGateError  # noqa: E402
from src.governance.pipeline_guards import (  # noqa: E402
    check_linting,
    check_type_checking,
    measure_test_coverage,
    run_all_guards_for_step,
)

_DEFAULT_WORKSPACE = Path.cwd()


def _run_pipeline_guards(
    step: str,
    implementation: dict[str, Any],
    workspace: Path,
    dry_run: bool = False,
) -> None:
    """Execute pipeline guards for the given step and abort on failure.

    Args:
        step: Pipeline step name ("developer", "tester", "reviewer").
        implementation: Implementation metadata dictionary.
        workspace: Project root directory.
        dry_run: If True, report failures but don't abort.

    Raises:
        PipelineGateError: If any guard fails and dry_run is False.
    """
    console.print(f"\n  [dim]Running pipeline guards for '{step}'...[/dim]")
    logger.info("Running pipeline guards for step '%s'", step)

    failures = run_all_guards_for_step(step, implementation, workspace)

    if not failures:
        console.print("  [green]✓[/green] All pipeline guards passed")
        logger.info("All pipeline guards passed for step '%s'", step)
        return

    # Display failures
    all_errors: list[str] = []
    for guard_name, errors in failures:
        for error in errors:
            console.print(f"  [red]✗[/red] [{guard_name}] {error}")
            all_errors.append(f"[{guard_name}] {error}")

    if dry_run:
        console.print(
            "  [yellow]⚠ Guards failed but continuing (dry-run mode)[/yellow]"
        )
        logger.warning(
            "Pipeline guards failed in dry-run mode for step '%s': %s",
            step,
            all_errors,
        )
        return

    logger.error("Pipeline guards failed for step '%s': %s", step, all_errors)
    raise PipelineGateError(step, all_errors)


app = typer.Typer(
    name="orchestrator",
    help="Semi-Automatic Agent Orchestrator for Agentic Workflow Automation Platform",
    no_args_is_help=True,
)
console = Console()

STEPS = ["Planner", "Architect", "Developer", "Tester", "Reviewer"]


def render_step_flow(current: int, results: dict[int, str] | None = None) -> None:
    """Display a prominent flow indicator showing pipeline progress.

    Args:
        current: Zero-based index of the currently active step.
        results: Optional dict mapping step index to 'pass' or 'skip'.
    """
    if results is None:
        results = {}
    parts: list[str] = []
    for i, name in enumerate(STEPS):
        if i in results:
            if results[i] == "skip":
                parts.append(f"[yellow]⏭ {name}[/yellow]")
            else:
                parts.append(f"[green]✓ {name}[/green]")
        elif i == current:
            parts.append(f"[bold cyan on grey23] ▶ {name} [/bold cyan on grey23]")
        else:
            parts.append(f"[dim]○ {name}[/dim]")
    flow_line = "  →  ".join(parts)
    console.print()
    console.print(
        Panel(
            flow_line,
            border_style="bright_blue",
            padding=(0, 2),
        )
    )


def print_json(data: Any, title: str | None = None) -> None:
    """Pretty-print a JSON-serializable object with syntax highlighting.

    Args:
        data: Any JSON-serializable Python object (dict, list, etc.).
        title: Optional panel title to wrap the output.
    """
    try:
        json_str = json.dumps(data, indent=2, default=str)
    except (TypeError, ValueError):
        console.print(f"  [dim]{data}[/dim]")
        return
    rendered = JSON(json_str)
    if title:
        console.print(Panel(rendered, title=title, border_style="dim"))
    else:
        console.print(rendered)


# --- Domain Models ---


class ProgressTracker:
    """Track progress and maintain audit trails."""

    def __init__(self) -> None:
        """Initialize empty tracking collections."""
        self.task_history: list[dict[str, Any]] = []
        self.agent_interactions: list[dict[str, Any]] = []
        self.decision_log: list[dict[str, str]] = []
        self.quality_gate_results: list[dict[str, Any]] = []

    def log(self, agent: str, action: str, result: dict[str, Any]) -> None:
        """Record an agent interaction.

        Args:
            agent: Name of the agent performing the action.
            action: Description of the action taken.
            result: Dictionary containing the action outcome.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": result,
        }
        self.agent_interactions.append(entry)
        logger.info("Agent interaction: agent=%s action=%s", agent, action)
        logger.debug("Agent interaction detail: %s", json.dumps(entry, default=str))

    def log_decision(self, decision: str, reason: str, made_by: str) -> None:
        """Record a decision made during the pipeline.

        Args:
            decision: The decision identifier or short label.
            reason: Justification for the decision.
            made_by: Who made the decision (e.g., "human", "agent").
        """
        self.decision_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "reason": reason,
                "made_by": made_by,
            }
        )
        logger.info(
            "Decision recorded: decision=%s reason=%s made_by=%s",
            decision,
            reason,
            made_by,
        )

    def log_quality_gate(self, gate: str, passed: bool, message: str) -> None:
        """Record the result of a quality gate check.

        Args:
            gate: Name of the quality gate.
            passed: Whether the gate passed.
            message: Human-readable result message.
        """
        self.quality_gate_results.append(
            {
                "timestamp": datetime.now().isoformat(),
                "gate": gate,
                "passed": passed,
                "message": message,
            }
        )
        log_fn = logger.info if passed else logger.warning
        log_fn("Quality gate '%s': passed=%s message=%s", gate, passed, message)


# --- Quality Gates ---

GateFn = Callable[[dict[str, Any]], tuple[bool, str]]
"""Type alias for quality gate check functions.

A gate function receives an implementation metadata dictionary and returns
a tuple of (passed, human-readable message).
"""


def _check_linting(impl: dict[str, Any]) -> tuple[bool, str]:
    """Check whether linting passed.

    Args:
        impl: Implementation metadata dictionary.

    Returns:
        Tuple of (passed, message).
    """
    if impl.get("linting_passed"):
        return (True, "Linting passed")
    return (False, "Linting failed")


def _check_type_checking(impl: dict[str, Any]) -> tuple[bool, str]:
    """Check whether type checking passed.

    Args:
        impl: Implementation metadata dictionary.

    Returns:
        Tuple of (passed, message).
    """
    if impl.get("type_checking_passed"):
        return (True, "Type checking passed")
    return (False, "Type checking failed")


def _check_test_coverage(impl: dict[str, Any]) -> tuple[bool, str]:
    """Check whether test coverage meets the minimum threshold.

    Args:
        impl: Implementation metadata dictionary.

    Returns:
        Tuple of (passed, message).
    """
    coverage = impl.get("test_coverage", 0)
    if isinstance(coverage, int | float) and coverage >= 80:
        return (True, f"Coverage {coverage}%")
    return (False, f"Coverage {coverage}% < 80%")


QUALITY_GATES: dict[str, GateFn] = {
    "linting": _check_linting,
    "type_checking": _check_type_checking,
    "test_coverage": _check_test_coverage,
}
"""Registry of quality gate checks executed during the Tester step.

Each entry maps a gate name to a callable that evaluates one aspect
of the implementation (linting, type checking, or test coverage).
"""

STRUCTURAL_KEYWORDS = [
    "core engine",
    "plugin contract",
    "workflow execution",
    "registry",
    "isolation",
    "governance",
    "architecture",
    "plugin registration",
    "lifecycle",
    "execution context",
]
"""Keywords that indicate a task touches core architecture.

When any of these appear in the task objective or scope, the pipeline
requires an architect review step before proceeding.
"""


def _needs_architect_review(objective: str, scope: str) -> bool:
    """Determine whether architect review is required.

    Args:
        objective: The task objective text.
        scope: The task scope description.

    Returns:
        True if the objective or scope contains structural keywords.
    """
    text = f"{objective} {scope}".lower()
    matched = [kw for kw in STRUCTURAL_KEYWORDS if kw in text]
    needs_review = len(matched) > 0
    logger.debug(
        "Architect review check: needs_review=%s matched_keywords=%s",
        needs_review,
        matched,
    )
    return needs_review


def _task_dir(workspace: Path, task_number: int) -> Path:
    """Return the per-task directory path.

    Args:
        workspace: Root path of the project workspace.
        task_number: The task number.

    Returns:
        Path to the task's dedicated directory.
    """
    return workspace / "docs" / "tasks" / f"{task_number:04d}"


def _get_next_task_number(workspace: Path) -> int:
    """Compute the next sequential task number from existing task directories.

    Args:
        workspace: Root path of the project workspace.

    Returns:
        The next available task number (1-based).
    """
    tasks_dir = workspace / "docs" / "tasks"
    if not tasks_dir.exists():
        return 1
    max_num = 0
    for d in tasks_dir.iterdir():
        if d.is_dir() and re.match(r"\d{4}$", d.name):
            max_num = max(max_num, int(d.name))
    return max_num + 1


def _build_file_contents_block(
    file_paths: list[str], workspace: Path, max_chars: int = 50000
) -> str:
    """Read files from disk and format their contents for inclusion in prompts.

    Args:
        file_paths: Relative file paths to read.
        workspace: Project root directory.
        max_chars: Maximum total characters to include (prevents token overflow).

    Returns:
        Formatted string with file contents in fenced code blocks.
    """
    blocks: list[str] = []
    total_chars = 0

    for file_path in file_paths:
        full_path = workspace / file_path
        if not full_path.exists() or not full_path.is_file():
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if total_chars + len(content) > max_chars:
            blocks.append(f"### {file_path}\n(truncated — file too large)\n")
            break

        ext = full_path.suffix.lstrip(".")
        blocks.append(f"### {file_path}\n```{ext}\n{content}\n```\n")
        total_chars += len(content)

    return "\n".join(blocks) if blocks else "(no file contents available)"


def _save_markdown(path: Path, content: str) -> None:
    """Write markdown content to a file, creating parent directories as needed.

    Args:
        path: Destination file path.
        content: Markdown text to write.
    """
    logger.debug("Writing markdown file: %s (%d bytes)", path, len(content))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    logger.info("Saved file: %s", path)
    console.print(f"  [dim]Saved:[/dim] {path}")


# --- Commands ---


def _init_llm_client() -> LLMClient | None:
    """Attempt to initialize the LLM client.

    Returns:
        An LLMClient instance, or None if credentials are missing.
    """
    logger.info("Initializing LLM client...")
    try:
        client = LLMClient()
        logger.info("LLM client initialized successfully")
        return client
    except LLMConfigError as e:
        logger.warning("LLM client initialization failed: %s", e)
        console.print(f"  [yellow]⚠ LLM unavailable: {e}[/yellow]")
        console.print("  [dim]Falling back to static mode.[/dim]")
        return None


# Agents that should use tool-calling (they need to read/write files)
# The reviewer also uses tools to read source files for inspection.
_TOOL_ENABLED_AGENTS = {"developer", "tester", "reviewer"}


def _invoke_agent(
    llm: LLMClient | None,
    agent_name: str,
    user_message: str,
    workspace: Path = _DEFAULT_WORKSPACE,
) -> str | None:
    """Invoke an agent via the LLM, returning the response or None on failure.

    Automatically uses tool-calling for agents that need file/command access
    (developer, tester). Other agents use single-shot invocation.

    Args:
        llm: The LLM client instance (or None for static fallback).
        agent_name: Agent role name matching a prompt file.
        user_message: Context to send to the agent.
        workspace: Workspace root for tool execution.

    Returns:
        The LLM response text, or None if unavailable.
    """
    if llm is None:
        logger.debug(
            "Skipping agent '%s' invocation: LLM client unavailable", agent_name
        )
        console.print(
            f"  [dim]LLM unavailable — using static fallback for '{agent_name}'[/dim]"
        )
        return None
    msg_len = len(user_message)
    use_tools = agent_name in _TOOL_ENABLED_AGENTS
    mode = "with tools" if use_tools else "single-shot"
    logger.info(
        "Invoking agent '%s' (message length: %d chars, mode: %s)",
        agent_name,
        len(user_message),
        mode,
    )
    start_time = time.monotonic()
    try:
        system_prompt = load_system_prompt(agent_name)
        logger.debug(
            "Loaded system prompt for '%s' (%d chars)", agent_name, len(system_prompt)
        )
        spinner_msg = (
            f"[bold]{agent_name}[/bold] agent thinking... "
            f"[dim]({msg_len} chars, {mode})[/dim]"
        )
        with console.status(spinner_msg, spinner="dots"):
            if use_tools:
                set_tool_workspace(workspace)
                response = llm.invoke_with_tools(
                    system_prompt, user_message, workspace=workspace
                )
            else:
                response = llm.invoke(system_prompt, user_message)
        elapsed = time.monotonic() - start_time
        logger.info(
            "Agent '%s' responded in %.2fs (response length: %d chars)",
            agent_name,
            elapsed,
            len(response) if response else 0,
        )
        console.print(
            f"  [green]✓[/green] [bold]{agent_name}[/bold] responded "
            f"in {elapsed:.1f}s [dim]({len(response) if response else 0} chars)[/dim]"
        )
        return response
    except FileNotFoundError as e:
        elapsed = time.monotonic() - start_time
        logger.error(
            "Agent '%s' failed after %.2fs: prompt file not found: %s",
            agent_name,
            elapsed,
            e,
        )
        console.print(
            f"  [red]✗ Agent '{agent_name}' error: prompt file not found[/red]"
        )
        console.print(f"    [dim]{e}[/dim]")
        return None
    except LLMError as e:
        elapsed = time.monotonic() - start_time
        logger.error("Agent '%s' failed after %.2fs: %s", agent_name, elapsed, e)
        console.print(
            f"  [red]✗ Agent '{agent_name}' LLM error after {elapsed:.1f}s[/red]"
        )
        console.print(f"    [dim]{e}[/dim]")
        return None


@app.command()
def run(
    requirement: Annotated[
        str | None, typer.Argument(help="Feature requirement to implement")
    ] = None,
    workspace: Annotated[
        Path, typer.Option(help="Workspace root path")
    ] = _DEFAULT_WORKSPACE,
    skip_architect: Annotated[
        bool, typer.Option("--skip-architect", help="Skip architect review")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Simulate without writing files")
    ] = False,
    auto_approve: Annotated[
        bool, typer.Option("--auto-approve", help="Skip manual confirmations")
    ] = False,
) -> None:
    """Execute the full agentic pipeline for a requirement."""
    _configure_logging(verbose=dry_run)

    if not requirement:
        requirement = typer.prompt("Enter the feature requirement to implement")

    logger.info("=== Pipeline started ===")
    logger.info(
        "Parameters: workspace=%s skip_architect=%s dry_run=%s auto_approve=%s",
        workspace,
        skip_architect,
        dry_run,
        auto_approve,
    )
    logger.info("Requirement: %s", requirement.strip())
    pipeline_start = time.monotonic()

    tracker = ProgressTracker()
    task_number = _get_next_task_number(workspace)
    logger.info("Assigned task number: %d", task_number)

    # Initialize LLM (None if unavailable — falls back to static mode)
    if dry_run:
        logger.info("Dry-run mode: skipping LLM initialization")
    llm = None if dry_run else _init_llm_client()

    console.print(
        Panel(
            f"[bold]Task {task_number}:[/bold] {requirement.strip()}",
            title="Agentic Pipeline",
        )
    )

    step_results: dict[int, str] = {}

    # Step 1: Planner
    logger.info("--- Step 1: Planner ---")
    step_start = time.monotonic()
    render_step_flow(0, step_results)
    console.print("\n[bold blue]Step 1: Planner[/bold blue]")
    planner_context = (
        f"Requirement: {requirement.strip()}\n\n"
        f"Task number: {task_number}\n"
        f"Workspace structure: src/core/, src/plugins/, src/api/, tests/\n\n"
        "Respond with a JSON object containing:\n"
        '  - "objective": clear statement of what to accomplish\n'
        '  - "scope": boundaries (included/excluded)\n'
        '  - "plan": array of implementation steps\n'
        '  - "risks": array of potential risks\n'
        '  - "acceptance_criteria": array of completion conditions\n'
    )
    planner_response = _invoke_agent(llm, "planner", planner_context)

    if planner_response:
        try:
            planner_data = parse_json_response(planner_response)
            objective = planner_data.get(
                "objective", f"Implement feature: {requirement.strip()}"
            )
            scope = planner_data.get("scope", "Core functionality")
            plan = planner_data.get(
                "plan", ["Analyze", "Design", "Implement", "Test", "Review"]
            )
            print_json(planner_data, title="Planner Output")
        except ValueError:
            # LLM didn't return valid JSON — use the raw text as objective
            objective = f"Implement feature: {requirement.strip()}"
            scope = "Core functionality"
            plan = ["Analyze", "Design", "Implement", "Test", "Review"]
            console.print(
                "  [yellow]⚠ Could not parse structured"
                " plan from LLM, using defaults[/yellow]"
            )
            console.print(
                f"  [dim]Raw response preview: {planner_response[:200]}...[/dim]"
            )
    else:
        objective = f"Implement feature: {requirement.strip()}"
        scope = "Core functionality"
        plan = [
            "Analyze requirements",
            "Design approach",
            "Implement",
            "Test",
            "Review",
        ]
        console.print("  [dim]Using default plan (no LLM response)[/dim]")

    created_at = datetime.now().isoformat()
    task_doc: dict[str, Any] = {
        "task_number": task_number,
        "requirement": requirement.strip(),
        "objective": objective,
        "scope": scope,
        "plan": plan,
        "architect_review": _needs_architect_review(objective, scope),
        "created_at": created_at,
    }
    tracker.log("planner", "create_task", task_doc)

    if not dry_run:
        task_content = (
            f"# Task {task_number}\n\n"
            f"## Requirement\n{requirement.strip()}\n\n"
            f"## Objective\n{objective}\n\n"
            f"## Scope\n{scope}\n\n## Plan\n"
            + "\n".join(f"- {s}" for s in plan)
            + f"\n\n## Created\n- Date: {created_at}\n- By: planner\n"
        )
        _save_markdown(
            _task_dir(workspace, task_number) / "task.md",
            task_content,
        )
    logger.info(
        "Step 1 completed in %.2fs: objective=%s",
        time.monotonic() - step_start,
        objective[:80],
    )
    console.print("  [green]✓[/green] Task document created")
    step_results[0] = "pass"

    # Step 2: Architect (conditional)
    logger.info("--- Step 2: Architect ---")
    step_start = time.monotonic()
    render_step_flow(1, step_results)
    console.print("\n[bold blue]Step 2: Architect[/bold blue]")
    if skip_architect or not task_doc["architect_review"]:
        logger.info(
            "Architect review skipped (skip_architect=%s, required=%s)",
            skip_architect,
            task_doc["architect_review"],
        )
        console.print("  [yellow]⏭ Skipped (not required)[/yellow]")
        step_results[1] = "skip"
    else:
        console.print("  [yellow]Architect review required[/yellow]")
        architect_context = (
            f"Task: {objective}\nScope: {scope}\n"
            f"Plan: {json.dumps(plan)}\n\n"
            "Review this task for architectural alignment with ADRs. "
            "Respond with a JSON object containing:\n"
            '  - "approved": boolean\n'
            '  - "feedback": string with review notes\n'
            '  - "adrs_referenced": array of relevant ADR numbers\n'
        )
        architect_response = _invoke_agent(llm, "architect", architect_context)
        if architect_response:
            console.print("  [dim]Architect feedback:[/dim]")
            # Show a truncated preview
            preview = architect_response[:300].replace("\n", " ")
            console.print(
                f"  {preview}{'...' if len(architect_response) > 300 else ''}"
            )

        if not auto_approve:
            typer.confirm("  Approve architect review and continue?", abort=True)
        tracker.log_decision("architect_approved", "Review approved", "human")
        logger.info(
            "Step 2 completed in %.2fs: architect review approved",
            time.monotonic() - step_start,
        )
        console.print("  [green]✓[/green] Architect review approved")
        step_results[1] = "pass"

    # Step 3: Developer
    logger.info("--- Step 3: Developer ---")
    step_start = time.monotonic()
    render_step_flow(2, step_results)
    console.print("\n[bold blue]Step 3: Developer[/bold blue]")
    developer_context = (
        f"Task: {objective}\nScope: {scope}\n"
        f"Plan: {json.dumps(plan)}\n\n"
        "Implement this feature using the tools provided to you.\n"
        "You MUST use write_file to create actual files on disk and "
        "run_command to validate with ruff, mypy, and pytest.\n"
        "Do NOT just output code in your response — use the write_file tool.\n\n"
        "After completing all tool-based implementation, respond with a "
        "JSON summary containing:\n"
        '  - "files_created": array of relative file paths you wrote\n'
        '  - "files_modified": array of relative file paths you modified\n'
        '  - "design_decisions": array of key decisions made\n'
        '  - "tests_passed": boolean indicating if pytest passed\n'
    )
    developer_response = _invoke_agent(llm, "developer", developer_context)

    # Ground truth: files the agent actually wrote via write_file tool
    actual_written = get_written_files()
    actual_modified = get_modified_files()

    if developer_response:
        try:
            dev_data = parse_json_response(developer_response)
            claimed_created = dev_data.get("files_created", [])
            claimed_modified = dev_data.get("files_modified", [])
            design_decisions = dev_data.get("design_decisions", [])
            tests_passed = dev_data.get("tests_passed", False)
        except ValueError:
            claimed_created = []
            claimed_modified = []
            design_decisions = []
            tests_passed = False
            console.print(
                "  [yellow]⚠ Could not parse developer"
                " response, using tool tracker[/yellow]"
            )
    else:
        claimed_created = []
        claimed_modified = []
        design_decisions = []
        tests_passed = False

    # Prefer actual tool-tracked writes over LLM claims.
    # The tool tracker is ground truth — LLM claims are only used as fallback
    # when the agent didn't use write_file at all.
    has_tool_activity = actual_written or actual_modified

    if has_tool_activity:
        files_created = list(dict.fromkeys(actual_written))
        files_modified = list(dict.fromkeys(actual_modified))
        # Log discrepancies for debugging
        all_tool_files = set(actual_written) | set(actual_modified)
        all_claimed = set(claimed_created) | set(claimed_modified)
        if all_claimed and all_claimed != all_tool_files:
            logger.warning(
                "LLM claimed files=%s but tool tracker recorded=%s",
                sorted(all_claimed),
                sorted(all_tool_files),
            )
            console.print(
                "  [yellow]⚠ LLM file list differs from actual writes "
                "— using tool tracker as source of truth[/yellow]"
            )
    elif claimed_created or claimed_modified:
        files_created = list(dict.fromkeys(claimed_created))
        files_modified = list(dict.fromkeys(claimed_modified))
    else:
        files_created = []
        files_modified = []
        console.print(
            "  [yellow]⚠ No files written by agent (no tool calls "
            "and no parseable response)[/yellow]"
        )

    console.print(f"  [dim]Files created:[/dim] {files_created}")
    console.print(f"  [dim]Files modified:[/dim] {files_modified}")
    console.print(f"  [dim]Tests passed:[/dim] {tests_passed}")
    if design_decisions:
        print_json(design_decisions, title="Design Decisions")

    impl_created_at = datetime.now().isoformat()
    implementation: dict[str, Any] = {
        "task_number": task_number,
        "files_created": files_created,
        "files_modified": files_modified,
        "tests_written": any("tests/" in f for f in files_created),
        "linting_passed": False,
        "type_checking_passed": False,
        "test_coverage": 0,
        "created_at": impl_created_at,
    }
    tracker.log("developer", "implement", implementation)

    # --- Post-Developer Guards (P0/P2) ---
    try:
        _run_pipeline_guards("developer", implementation, workspace, dry_run=dry_run)
    except PipelineGateError as e:
        console.print(
            "\n  [red bold]✗ Pipeline blocked after Developer step:[/red bold]"
        )
        for err in e.errors:
            console.print(f"    [red]• {err}[/red]")
        resume_cmd = (
            f"uv run python scripts/orchestrator.py resume {task_number} --from-step 3"
        )
        console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
        raise typer.Exit(code=1) from None

    # Guards passed — now save the implementation report
    if not dry_run:
        impl_content = (
            f"# Implementation Report - Task {task_number}\n\n"
            f"## Files Created\n"
            + "\n".join(f"- {f}" for f in files_created)
            + "\n\n## Files Modified\n"
            + "\n".join(f"- {f}" for f in files_modified)
            + "\n\n## Quality Score\n"
            + f"- Tests Written: {implementation['tests_written']}\n"
            + f"- Tests Passed: {tests_passed}\n"
            + f"- Created: {impl_created_at}\n"
        )
        if developer_response:
            impl_content += f"\n## LLM Output\n\n```json\n{developer_response}\n```\n"
        _save_markdown(
            _task_dir(workspace, task_number) / "implementation.md",
            impl_content,
        )

    logger.info(
        "Step 3 completed in %.2fs: files_created=%s files_modified=%s",
        time.monotonic() - step_start,
        files_created,
        files_modified,
    )
    console.print("  [green]✓[/green] Implementation complete")
    step_results[2] = "pass"

    # Step 4: Tester
    logger.info("--- Step 4: Tester ---")
    step_start = time.monotonic()
    render_step_flow(3, step_results)
    console.print("\n[bold blue]Step 4: Tester[/bold blue]")

    # --- Post-Tester Guards (P0: actual test execution) ---
    try:
        _run_pipeline_guards("tester", implementation, workspace, dry_run=dry_run)
    except PipelineGateError as e:
        console.print("\n  [red bold]✗ Pipeline blocked after Tester step:[/red bold]")
        for err in e.errors:
            console.print(f"    [red]• {err}[/red]")
        resume_cmd = (
            f"uv run python scripts/orchestrator.py resume {task_number} --from-step 4"
        )
        console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
        raise typer.Exit(code=1) from None

    # Measure actual test coverage after tests pass
    if not dry_run:
        all_files = files_created + files_modified
        implementation["linting_passed"] = check_linting(workspace, all_files)
        implementation["type_checking_passed"] = check_type_checking(
            workspace, all_files
        )
        actual_coverage = measure_test_coverage(workspace)
        implementation["test_coverage"] = actual_coverage
        console.print(f"  [dim]Measured coverage:[/dim] {actual_coverage:.1f}%")
    else:
        implementation["test_coverage"] = 0

    for gate_name, gate_fn in QUALITY_GATES.items():
        passed, msg = gate_fn(implementation)
        tracker.log_quality_gate(gate_name, passed, msg)
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {icon} {msg}")

    logger.info("Step 4 completed in %.2fs", time.monotonic() - step_start)
    step_results[3] = "pass"

    # Step 5: Reviewer
    logger.info("--- Step 5: Reviewer ---")
    step_start = time.monotonic()
    render_step_flow(4, step_results)
    console.print("\n[bold blue]Step 5: Reviewer[/bold blue]")

    # --- Pre-Reviewer Guards (P1: precondition + git consistency) ---
    try:
        _run_pipeline_guards("reviewer", implementation, workspace, dry_run=dry_run)
    except PipelineGateError as e:
        console.print(
            "\n  [red bold]✗ Pipeline blocked before Reviewer step:[/red bold]"
        )
        for err in e.errors:
            console.print(f"    [red]• {err}[/red]")
        resume_cmd = (
            f"uv run python scripts/orchestrator.py resume {task_number} --from-step 5"
        )
        console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
        raise typer.Exit(code=1) from None

    all_gates_passed = all(r["passed"] for r in tracker.quality_gate_results)
    logger.info("All quality gates passed: %s", all_gates_passed)

    # Build file contents for the reviewer to inspect directly
    file_contents_block = _build_file_contents_block(
        files_created + files_modified, workspace
    )
    reviewer_context = (
        f"Task: {objective}\nScope: {scope}\n"
        f"Files created: {json.dumps(files_created)}\n"
        f"Files modified: {json.dumps(files_modified)}\n"
        f"Quality gates passed: {all_gates_passed}\n"
        f"Test coverage: {implementation['test_coverage']:.1f}%\n\n"
        f"## Source Code\n{file_contents_block}\n\n"
        "Review this implementation. You MUST base your findings on the actual "
        "source code provided above. Do NOT hallucinate missing features that "
        "are present in the code.\n\n"
        "Respond with a JSON object containing:\n"
        '  - "decision": one of "approved", "request_changes", "rejected"\n'
        '  - "findings": array of issues or observations (cite specific lines)\n'
        '  - "suggested_improvements": array of recommendations\n'
    )
    reviewer_response = _invoke_agent(llm, "reviewer", reviewer_context, workspace)

    if reviewer_response:
        try:
            review_data = parse_json_response(reviewer_response)
            review_status = review_data.get(
                "decision", "approved" if all_gates_passed else "request_changes"
            )
            findings = review_data.get("findings", [])
            improvements = review_data.get("suggested_improvements", [])
            console.print(f"  [dim]Decision:[/dim] {review_status}")
            if findings:
                print_json(findings, title=f"Findings ({len(findings)})")
            if improvements:
                print_json(improvements, title=f"Suggestions ({len(improvements)})")
        except ValueError:
            review_status = "approved" if all_gates_passed else "request_changes"
            console.print("  [yellow]⚠ Could not parse reviewer response[/yellow]")
            console.print(
                f"  [dim]Raw response preview: {reviewer_response[:200]}...[/dim]"
            )
    else:
        review_status = "approved" if all_gates_passed else "request_changes"
        console.print(f"  [dim]No LLM response — defaulting to: {review_status}[/dim]")

    if not dry_run:
        review_content = (
            f"# Review Report - Task {task_number}\n\n"
            f"## Status\n{review_status}\n\n"
            f"## Coverage\n{implementation['test_coverage']}%\n\n"
            f"## Created\n{datetime.now().isoformat()}\n"
        )
        if reviewer_response:
            review_content += f"\n## LLM Review\n\n{reviewer_response}\n"
        _save_markdown(
            _task_dir(workspace, task_number) / "review.md",
            review_content,
        )
    logger.info(
        "Step 5 completed in %.2fs: review_status=%s",
        time.monotonic() - step_start,
        review_status,
    )
    console.print(
        f"  Status: [{'green' if all_gates_passed else 'red'}]{review_status}[/]"
    )

    # Pipeline complete
    total_elapsed = time.monotonic() - pipeline_start
    if review_status != "approved":
        logger.warning("Pipeline ended: review_status=%s", review_status)
        console.print(
            f"\n  [red]✗ Review returned '{review_status}' — "
            "run resume --from-step 3 to fix[/red]"
        )
        resume_cmd = (
            f"uv run python scripts/orchestrator.py resume {task_number} --from-step 3"
        )
        console.print(f"  [dim]{resume_cmd}[/dim]")
        raise typer.Exit(code=1) from None

    logger.info(
        "=== Pipeline completed successfully in %.2fs (task=%d) ===",
        total_elapsed,
        task_number,
    )
    console.print(
        Panel(
            "[green bold]Pipeline completed successfully"
            f"[/green bold] ({total_elapsed:.1f}s)",
            title="Done",
        )
    )


def _detect_completed_step(task_number: int, workspace: Path) -> int:
    """Detect the last completed pipeline step for a given task.

    Checks for existence of task artifacts in the per-task directory:
      - Step 1 (Planner): task.md exists
      - Step 3 (Developer): implementation.md exists
      - Step 5 (Reviewer): review.md exists with 'approved'

    Args:
        task_number: The task number to check.
        workspace: Root path of the project workspace.

    Returns:
        The last completed step number (0 if nothing completed).
    """
    task_path = _task_dir(workspace, task_number)
    task_file = task_path / "task.md"
    impl_file = task_path / "implementation.md"
    review_file = task_path / "review.md"

    if not task_file.exists():
        return 0

    # Check if review was completed
    if review_file.exists():
        content = review_file.read_text()
        if "approved" in content.lower():
            return 5  # Review approved → pipeline complete
        return 4  # Review exists but not approved → tester done

    if impl_file.exists():
        return 3  # Developer done

    # Task file exists but no impl → planner done (step 1)
    return 1


def _parse_task_file(task_path: Path) -> dict[str, str]:
    """Parse a task markdown file to extract requirement, objective, and scope.

    Args:
        task_path: Path to the per-task directory.

    Returns:
        Dictionary with 'requirement', 'objective', and 'scope' keys.
    """
    task_file = task_path / "task.md"
    content = task_file.read_text()
    requirement = ""
    objective = "Unknown"
    scope = "Core functionality"

    req_match = re.search(r"## Requirement\n(.+?)\n(?=##)", content, re.DOTALL)
    if req_match:
        requirement = req_match.group(1).strip()

    obj_match = re.search(r"## Objective\n(.+?)\n", content)
    if obj_match:
        objective = obj_match.group(1).strip()

    scope_match = re.search(r"## Scope\n(.+?)\n", content)
    if scope_match:
        scope = scope_match.group(1).strip()

    return {"requirement": requirement, "objective": objective, "scope": scope}


@app.command()
def resume(
    task_number: Annotated[int, typer.Argument(help="Task number to resume (e.g. 1)")],
    workspace: Annotated[
        Path, typer.Option(help="Workspace root path")
    ] = _DEFAULT_WORKSPACE,
    skip_architect: Annotated[
        bool, typer.Option("--skip-architect", help="Skip architect review")
    ] = False,
    auto_approve: Annotated[
        bool, typer.Option("--auto-approve", help="Skip manual confirmations")
    ] = False,
    from_step: Annotated[
        int | None,
        typer.Option("--from-step", help="Force resume from specific step (1-6)"),
    ] = None,
) -> None:
    """Resume a failed or incomplete pipeline from where it left off."""
    _configure_logging()

    task_path = _task_dir(workspace, task_number)
    task_file = task_path / "task.md"
    if not task_file.exists():
        console.print(f"[red]Error: Task {task_number} not found at {task_path}[/red]")
        raise typer.Exit(code=1) from None

    # Determine where to resume
    if from_step is not None:
        if from_step < 1 or from_step > 5:
            console.print("[red]Error: --from-step must be between 1 and 5[/red]")
            raise typer.Exit(code=1) from None
        last_completed = from_step - 1
        logger.info("Forced resume from step %d (--from-step)", from_step)
    else:
        last_completed = _detect_completed_step(task_number, workspace)
        logger.info("Auto-detected last completed step: %d", last_completed)

    if last_completed >= 5:
        console.print(f"[green]Task {task_number} is already fully completed.[/green]")
        raise typer.Exit()

    # Parse task info
    task_info = _parse_task_file(task_path)
    raw_requirement = task_info["requirement"]
    objective = task_info["objective"]
    scope = task_info["scope"]

    logger.info(
        "=== Pipeline resuming (task=%d, from_step=%d) ===",
        task_number,
        last_completed + 1,
    )
    pipeline_start = time.monotonic()

    console.print(
        Panel(
            f"[bold]Resuming Task {task_number}:[/bold] {objective}\n"
            f"[dim]Starting from Step {last_completed + 1}[/dim]",
            title="Agentic Pipeline (Resume)",
        )
    )

    tracker = ProgressTracker()
    llm = _init_llm_client()

    # Build initial step_results from already-completed steps
    step_results: dict[int, str] = {}
    for i in range(min(last_completed, len(STEPS))):
        step_results[i] = "pass"

    # We need a plan for downstream steps — extract from task file or use default
    task_content = (task_path / "task.md").read_text()
    plan: list[str] = []
    in_plan = False
    for line in task_content.splitlines():
        if line.strip() == "## Plan":
            in_plan = True
            continue
        if in_plan:
            if line.startswith("## "):
                break
            if line.startswith("- "):
                plan.append(line[2:].strip())
    if not plan:
        plan = ["Analyze", "Design", "Implement", "Test", "Review"]

    # --- Step 2: Architect (if not yet done) ---
    if last_completed < 2:
        logger.info("--- Step 2: Architect ---")
        step_start = time.monotonic()
        render_step_flow(1, step_results)
        console.print("\n[bold blue]Step 2: Architect[/bold blue]")
        needs_review = _needs_architect_review(objective, scope)
        if skip_architect or not needs_review:
            logger.info("Architect review skipped")
            console.print("  [yellow]⏭ Skipped (not required)[/yellow]")
            step_results[1] = "skip"
        else:
            console.print("  [yellow]Architect review required[/yellow]")
            architect_context = (
                f"Task: {objective}\nScope: {scope}\n"
                f"Plan: {json.dumps(plan)}\n\n"
                "Review this task for architectural alignment with ADRs. "
                "Respond with a JSON object containing:\n"
                '  - "approved": boolean\n'
                '  - "feedback": string with review notes\n'
                '  - "adrs_referenced": array of relevant ADR numbers\n'
            )
            architect_response = _invoke_agent(llm, "architect", architect_context)
            if architect_response:
                preview = architect_response[:300].replace("\n", " ")
                suffix = "..." if len(architect_response) > 300 else ""
                console.print(f"  [dim]{preview}{suffix}[/dim]")

            if not auto_approve:
                typer.confirm("  Approve architect review and continue?", abort=True)
            tracker.log_decision(
                "architect_approved", "Review approved (resume)", "human"
            )
            logger.info("Step 2 completed in %.2fs", time.monotonic() - step_start)
            console.print("  [green]✓[/green] Architect review approved")
            step_results[1] = "pass"

    # --- Step 3: Developer (if not yet done) ---
    if last_completed < 3:
        logger.info("--- Step 3: Developer ---")
        step_start = time.monotonic()
        render_step_flow(2, step_results)
        console.print("\n[bold blue]Step 3: Developer[/bold blue]")

        # Include reviewer feedback and previous implementation context
        reviewer_feedback = ""
        review_file = task_path / "review.md"
        impl_file = task_path / "implementation.md"
        if review_file.exists():
            review_content = review_file.read_text()

            # Build context about what was previously implemented
            prev_impl_context = ""
            if impl_file.exists():
                impl_text = impl_file.read_text()
                prev_files: list[str] = []
                in_created = False
                for line in impl_text.splitlines():
                    if line.strip() == "## Files Created":
                        in_created = True
                        continue
                    if line.startswith("## "):
                        in_created = False
                        continue
                    if in_created and line.startswith("- "):
                        prev_files.append(line[2:].strip())

                if prev_files:
                    prev_impl_context = (
                        "\n## Previously Created Files\n"
                        "These files already exist on disk from the previous "
                        "implementation attempt. You should READ them first, "
                        "then MODIFY them to fix the reviewer's findings "
                        "(use write_file to overwrite):\n"
                        + "\n".join(f"- {f}" for f in prev_files)
                        + "\n\n"
                    )

            reviewer_feedback = (
                "\n## IMPORTANT: This is a RE-IMPLEMENTATION\n"
                "This task was previously implemented but the reviewer "
                "requested changes. The code already exists on disk.\n"
                "You are NOT starting from scratch — you are FIXING "
                "the existing implementation.\n\n"
                "Your workflow:\n"
                "1. Read the existing files to understand current state\n"
                "2. Identify what needs to change based on the findings below\n"
                "3. Write the corrected files (overwrite existing ones)\n"
                "4. Run ruff, mypy, and pytest to validate\n\n"
                f"{prev_impl_context}"
                "## Reviewer Findings (MUST FIX)\n"
                "The reviewer requested the following changes:\n\n"
                f"{review_content}\n\n"
                "You MUST address ALL findings above. "
                "Do not repeat the same mistakes.\n\n"
            )
            console.print(
                "  [dim]Re-implementation mode: "
                "including reviewer feedback + previous file list[/dim]"
            )
            logger.info(
                "Developer context includes reviewer feedback "
                "and previous implementation files"
            )

        req_note = (
            f"\nOriginal requirement: {raw_requirement}\n\n" if raw_requirement else ""
        )
        developer_context = (
            f"Task: {objective}\nScope: {scope}\n"
            f"{req_note}"
            f"Plan: {json.dumps(plan)}\n\n"
            f"{reviewer_feedback}"
            "Implement this feature using the tools provided to you.\n"
            "You MUST use write_file to create actual files on disk and "
            "run_command to validate with ruff, mypy, and pytest.\n"
            "Do NOT just output code in your response — use the write_file tool.\n\n"
            "After completing all tool-based implementation, respond with a "
            "JSON summary containing:\n"
            '  - "files_created": array of relative file paths you wrote\n'
            '  - "files_modified": array of relative file paths you modified\n'
            '  - "design_decisions": array of key decisions made\n'
            '  - "tests_passed": boolean indicating if pytest passed\n'
        )
        developer_response = _invoke_agent(llm, "developer", developer_context)

        # Ground truth: files the agent actually wrote via write_file tool
        actual_written = get_written_files()
        actual_modified = get_modified_files()

        if developer_response:
            try:
                dev_data = parse_json_response(developer_response)
                claimed_created = dev_data.get("files_created", [])
                claimed_modified = dev_data.get("files_modified", [])
                tests_passed = dev_data.get("tests_passed", False)
            except ValueError:
                claimed_created = []
                claimed_modified = []
                tests_passed = False
        else:
            claimed_created = []
            claimed_modified = []
            tests_passed = False

        # Prefer actual tool-tracked writes over LLM claims.
        # The tool tracker is ground truth — LLM claims are only used as
        # fallback when the agent didn't use write_file at all.
        has_tool_activity = actual_written or actual_modified

        if has_tool_activity:
            files_created = list(dict.fromkeys(actual_written))
            files_modified = list(dict.fromkeys(actual_modified))
            all_tool_files = set(actual_written) | set(actual_modified)
            all_claimed = set(claimed_created) | set(claimed_modified)
            if all_claimed and all_claimed != all_tool_files:
                logger.warning(
                    "LLM claimed files=%s but tool tracker recorded=%s",
                    sorted(all_claimed),
                    sorted(all_tool_files),
                )
        elif claimed_created or claimed_modified:
            files_created = list(dict.fromkeys(claimed_created))
            files_modified = list(dict.fromkeys(claimed_modified))
        else:
            files_created = []
            files_modified = []

        impl_created_at = datetime.now().isoformat()
        implementation: dict[str, Any] = {
            "task_number": task_number,
            "files_created": files_created,
            "files_modified": files_modified,
            "tests_written": any("tests/" in f for f in files_created),
            "linting_passed": False,
            "type_checking_passed": False,
            "test_coverage": 0,
            "created_at": impl_created_at,
        }
        tracker.log("developer", "implement", implementation)

        # --- Post-Developer Guards (P0/P2) ---
        try:
            _run_pipeline_guards("developer", implementation, workspace)
        except PipelineGateError as e:
            console.print(
                "\n  [red bold]✗ Pipeline blocked after Developer step:[/red bold]"
            )
            for err in e.errors:
                console.print(f"    [red]• {err}[/red]")
            resume_cmd = (
                "uv run python scripts/orchestrator.py"
                f" resume {task_number} --from-step 3"
            )
            console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
            raise typer.Exit(code=1) from None

        # Guards passed — now save the implementation report (preserve history)
        impl_path = task_path / "implementation.md"
        previous_history = ""
        if impl_path.exists():
            existing_content = impl_path.read_text()
            # Count existing iterations
            iteration_count = existing_content.count("## Iteration ")
            if iteration_count == 0:
                # First re-implementation: wrap existing content as Iteration 1
                previous_history = (
                    f"\n---\n\n## Iteration 1 (original)\n\n{existing_content}\n"
                )
                current_iteration = 2
            else:
                # Subsequent re-implementations: preserve all history
                if "---" in existing_content:
                    history_section = existing_content.split("---", 1)[-1]
                else:
                    history_section = existing_content
                previous_history = f"\n---\n\n{history_section}\n"
                current_iteration = iteration_count + 2
            logger.info(
                "Preserving implementation history: iteration %d",
                current_iteration,
            )
        else:
            current_iteration = 1

        impl_content = (
            f"# Implementation Report - Task {task_number}\n\n"
            f"## Iteration {current_iteration}"
            f"{' (fix)' if current_iteration > 1 else ''}\n\n"
            f"## Files Created\n"
            + "\n".join(f"- {f}" for f in files_created)
            + "\n\n## Files Modified\n"
            + "\n".join(f"- {f}" for f in files_modified)
            + "\n\n## Quality Score\n"
            + f"- Tests Written: {implementation['tests_written']}\n"
            + f"- Tests Passed: {tests_passed}\n"
            + f"- Created: {impl_created_at}\n"
        )
        if developer_response:
            impl_content += f"\n## LLM Output\n\n```json\n{developer_response}\n```\n"
        impl_content += previous_history
        _save_markdown(
            impl_path,
            impl_content,
        )

        logger.info("Step 3 completed in %.2fs", time.monotonic() - step_start)
        console.print("  [green]✓[/green] Implementation complete")
        step_results[2] = "pass"
    else:
        # Load existing implementation data from the saved report
        impl_file = task_path / "implementation.md"
        files_created = []
        files_modified = []
        if impl_file.exists():
            impl_text = impl_file.read_text()
            in_created = False
            in_modified = False
            for line in impl_text.splitlines():
                if line.strip() == "## Files Created":
                    in_created = True
                    in_modified = False
                    continue
                if line.strip() == "## Files Modified":
                    in_modified = True
                    in_created = False
                    continue
                if line.startswith("## "):
                    in_created = False
                    in_modified = False
                    continue
                if in_created and line.startswith("- "):
                    files_created.append(line[2:].strip())
                if in_modified and line.startswith("- "):
                    files_modified.append(line[2:].strip())
        implementation = {
            "task_number": task_number,
            "files_created": files_created,
            "files_modified": files_modified,
            "tests_written": any("tests/" in f for f in files_created),
            "linting_passed": False,
            "type_checking_passed": False,
            "test_coverage": 0,
            "created_at": datetime.now().isoformat(),
        }
        console.print("\n[bold blue]Step 3: Developer[/bold blue]")
        console.print("  [yellow]⏭ Already completed — skipping[/yellow]")
        console.print(f"  [dim]Files from report:[/dim] {files_created}")

    # --- Step 4: Tester (if not yet done) ---
    if last_completed < 4:
        logger.info("--- Step 4: Tester ---")
        step_start = time.monotonic()
        render_step_flow(3, step_results)
        console.print("\n[bold blue]Step 4: Tester[/bold blue]")

        # --- Post-Tester Guards (P0: actual test execution) ---
        try:
            _run_pipeline_guards("tester", implementation, workspace)
        except PipelineGateError as e:
            console.print(
                "\n  [red bold]✗ Pipeline blocked after Tester step:[/red bold]"
            )
            for err in e.errors:
                console.print(f"    [red]• {err}[/red]")
            resume_cmd = (
                "uv run python scripts/orchestrator.py"
                f" resume {task_number} --from-step 4"
            )
            console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
            raise typer.Exit(code=1) from None

        # Measure actual linting, type checking, and test coverage
        all_files = files_created + files_modified
        implementation["linting_passed"] = check_linting(workspace, all_files)
        implementation["type_checking_passed"] = check_type_checking(
            workspace, all_files
        )
        actual_coverage = measure_test_coverage(workspace)
        implementation["test_coverage"] = actual_coverage
        console.print(f"  [dim]Measured coverage:[/dim] {actual_coverage:.1f}%")

        for gate_name, gate_fn in QUALITY_GATES.items():
            passed, msg = gate_fn(implementation)
            tracker.log_quality_gate(gate_name, passed, msg)
            icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
            console.print(f"  {icon} {msg}")

        logger.info("Step 4 completed in %.2fs", time.monotonic() - step_start)
        step_results[3] = "pass"

    # --- Step 5: Reviewer (if not yet done) ---
    if last_completed < 5:
        logger.info("--- Step 5: Reviewer ---")
        step_start = time.monotonic()
        render_step_flow(4, step_results)
        console.print("\n[bold blue]Step 5: Reviewer[/bold blue]")

        # --- Pre-Reviewer Guards (P1: precondition + git consistency) ---
        try:
            _run_pipeline_guards("reviewer", implementation, workspace)
        except PipelineGateError as e:
            console.print(
                "\n  [red bold]✗ Pipeline blocked before Reviewer step:[/red bold]"
            )
            for err in e.errors:
                console.print(f"    [red]• {err}[/red]")
            resume_cmd = (
                "uv run python scripts/orchestrator.py"
                f" resume {task_number} --from-step 5"
            )
            console.print(f"\n  [dim]Fix the issues and resume: {resume_cmd}[/dim]")
            raise typer.Exit(code=1) from None

        all_gates_passed = (
            all(r["passed"] for r in tracker.quality_gate_results)
            if tracker.quality_gate_results
            else True
        )
        logger.info("All quality gates passed: %s", all_gates_passed)

        reviewer_context = (
            f"Task: {objective}\nScope: {scope}\n"
            f"Files created: {json.dumps(files_created)}\n"
            f"Files modified: {json.dumps(files_modified)}\n"
            f"Quality gates passed: {all_gates_passed}\n"
            f"Test coverage: {implementation['test_coverage']:.1f}%\n\n"
            f"## Source Code\n"
            f"{_build_file_contents_block(files_created + files_modified, workspace)}"
            f"\n\n"
            "Review this implementation. You MUST base your findings on the actual "
            "source code provided above. Do NOT hallucinate missing features that "
            "are present in the code.\n\n"
            "Respond with a JSON object containing:\n"
            '  - "decision": one of "approved", "request_changes", "rejected"\n'
            '  - "findings": array of issues or observations (cite specific lines)\n'
            '  - "suggested_improvements": array of recommendations\n'
        )
        reviewer_response = _invoke_agent(llm, "reviewer", reviewer_context, workspace)

        if reviewer_response:
            try:
                review_data = parse_json_response(reviewer_response)
                review_status = review_data.get(
                    "decision", "approved" if all_gates_passed else "request_changes"
                )
            except ValueError:
                review_status = "approved" if all_gates_passed else "request_changes"
        else:
            review_status = "approved" if all_gates_passed else "request_changes"

        review_content = (
            f"# Review Report - Task {task_number}\n\n"
            f"## Status\n{review_status}\n\n"
            f"## Coverage\n{implementation['test_coverage']}%\n\n"
            f"## Created\n{datetime.now().isoformat()}\n"
        )
        if reviewer_response:
            review_content += f"\n## LLM Review\n\n{reviewer_response}\n"
        _save_markdown(
            task_path / "review.md",
            review_content,
        )
        logger.info(
            "Step 5 completed in %.2fs: review_status=%s",
            time.monotonic() - step_start,
            review_status,
        )
        color = "green" if review_status == "approved" else "red"
        console.print(f"  Status: [{color}]{review_status}[/]")
    else:
        # Review was already done — read the status
        review_file = task_path / "review.md"
        review_content = review_file.read_text() if review_file.exists() else ""
        review_status = (
            "approved" if "approved" in review_content.lower() else "request_changes"
        )
        console.print("\n[bold blue]Step 5: Reviewer[/bold blue]")
        console.print(f"  [dim]Already completed — status: {review_status}[/dim]")

    # Pipeline complete
    total_elapsed = time.monotonic() - pipeline_start
    if review_status != "approved":
        logger.warning("Pipeline ended: review_status=%s", review_status)
        console.print(
            f"\n  [red]✗ Review returned '{review_status}' — "
            "run resume --from-step 3 to fix[/red]"
        )
        resume_cmd = (
            f"uv run python scripts/orchestrator.py resume {task_number} --from-step 3"
        )
        console.print(f"  [dim]{resume_cmd}[/dim]")
        raise typer.Exit(code=1) from None

    logger.info(
        "=== Pipeline resumed and completed in %.2fs (task=%d) ===",
        total_elapsed,
        task_number,
    )
    console.print(
        Panel(
            "[green bold]Pipeline completed successfully"
            f"[/green bold] ({total_elapsed:.1f}s)",
            title="Done",
        )
    )


@app.command()
def status(  # noqa: C901
    workspace: Annotated[
        Path, typer.Option(help="Workspace root path")
    ] = _DEFAULT_WORKSPACE,
) -> None:
    """Show current pipeline progress and task history."""
    _configure_logging()
    logger.debug("Status command invoked for workspace: %s", workspace)
    tasks_dir = workspace / "docs" / "tasks"

    table = Table(title="Task Status")
    table.add_column("Task", style="cyan")
    table.add_column("Review", style="yellow")
    table.add_column("Status", style="green")

    if not tasks_dir.exists():
        console.print("[dim]No tasks found.[/dim]")
        raise typer.Exit()

    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir() or not re.match(r"\d{4}$", task_dir.name):
            continue
        num = int(task_dir.name)
        review_file = task_dir / "review.md"
        review_status = "pending"
        if review_file.exists():
            content = review_file.read_text()
            if "approved" in content:
                review_status = "✓ approved"
            elif "request_changes" in content:
                review_status = "✗ changes requested"
        impl_file = task_dir / "implementation.md"
        impl_status = "✓ implemented" if impl_file.exists() else "pending"
        table.add_row(f"task-{num:04d}", review_status, impl_status)

    console.print(table)


@app.command()
def validate(
    workspace: Annotated[
        Path, typer.Option(help="Workspace root path")
    ] = _DEFAULT_WORKSPACE,
) -> None:
    """Run quality gates against the workspace."""
    _configure_logging()
    logger.info("Validate command invoked for workspace: %s", workspace)
    console.print("[bold]Running quality gates...[/bold]\n")

    checks = [
        ("docs/tasks/ exists", (workspace / "docs" / "tasks").exists()),
        ("src/ exists", (workspace / "src").exists()),
        ("tests/ exists", (workspace / "tests").exists()),
        ("pyproject.toml exists", (workspace / "pyproject.toml").exists()),
    ]

    all_ok = True
    for name, passed in checks:
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {icon} {name}")
        if not passed:
            all_ok = False

    if all_ok:
        logger.info("All workspace validation checks passed")
        console.print("\n[green bold]All checks passed.[/green bold]")
    else:
        failed = [name for name, passed in checks if not passed]
        logger.warning("Workspace validation failed checks: %s", failed)
        console.print("\n[red bold]Some checks failed.[/red bold]")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
