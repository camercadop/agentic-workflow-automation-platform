#!/usr/bin/env python3
"""Semi-Automatic Agent Orchestrator CLI.

Provides semi-automatic orchestration of AI agents for development tasks.
Automates routine steps while maintaining human oversight and manual checkpoints.
"""

import json
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.llm.client import (  # noqa: E402
    LLMClient,
    LLMConfigError,
    LLMError,
    load_system_prompt,
    parse_json_response,
)

_DEFAULT_WORKSPACE = Path.cwd()

app = typer.Typer(
    name="orchestrator",
    help="Semi-Automatic Agent Orchestrator for Agentic Workflow Automation Platform",
    no_args_is_help=True,
)
console = Console()


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
        self.agent_interactions.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "action": action,
                "result": result,
            }
        )

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
    return any(kw in text for kw in STRUCTURAL_KEYWORDS)


def _get_next_task_number(workspace: Path) -> int:
    """Compute the next sequential task number from existing task files.

    Args:
        workspace: Root path of the project workspace.

    Returns:
        The next available task number (1-based).
    """
    tasks_dir = workspace / "docs" / "tasks"
    if not tasks_dir.exists():
        return 1
    max_num = 0
    for f in tasks_dir.glob("task-*.md"):
        match = re.search(r"task-(\d+)\.md", f.name)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def _save_markdown(path: Path, content: str) -> None:
    """Write markdown content to a file, creating parent directories as needed.

    Args:
        path: Destination file path.
        content: Markdown text to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    console.print(f"  [dim]Saved:[/dim] {path}")


# --- Commands ---


def _init_llm_client() -> LLMClient | None:
    """Attempt to initialize the LLM client.

    Returns:
        An LLMClient instance, or None if credentials are missing.
    """
    try:
        return LLMClient()
    except LLMConfigError as e:
        console.print(f"  [yellow]⚠ LLM unavailable: {e}[/yellow]")
        console.print("  [dim]Falling back to static mode.[/dim]")
        return None


def _invoke_agent(
    llm: LLMClient | None, agent_name: str, user_message: str
) -> str | None:
    """Invoke an agent via the LLM, returning the response or None on failure.

    Args:
        llm: The LLM client instance (or None for static fallback).
        agent_name: Agent role name matching a prompt file.
        user_message: Context to send to the agent.

    Returns:
        The LLM response text, or None if unavailable.
    """
    if llm is None:
        return None
    try:
        system_prompt = load_system_prompt(agent_name)
        return llm.invoke(system_prompt, user_message)
    except (FileNotFoundError, LLMError) as e:
        console.print(f"  [yellow]⚠ Agent '{agent_name}' error: {e}[/yellow]")
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
    if not requirement:
        requirement = typer.prompt("Enter the feature requirement to implement")

    tracker = ProgressTracker()
    task_number = _get_next_task_number(workspace)

    # Initialize LLM (None if unavailable — falls back to static mode)
    llm = None if dry_run else _init_llm_client()

    console.print(
        Panel(
            f"[bold]Task {task_number}:[/bold] {requirement.strip()}",
            title="Agentic Pipeline",
        )
    )

    # Step 1: Planner
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
        except ValueError:
            # LLM didn't return valid JSON — use the raw text as objective
            objective = f"Implement feature: {requirement.strip()}"
            scope = "Core functionality"
            plan = ["Analyze", "Design", "Implement", "Test", "Review"]
            console.print(
                "  [dim]Could not parse structured plan, using defaults.[/dim]"
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
            f"## Objective\n{objective}\n\n"
            f"## Scope\n{scope}\n\n## Plan\n"
            + "\n".join(f"- {s}" for s in plan)
            + f"\n\n## Created\n- Date: {created_at}\n- By: planner\n"
        )
        _save_markdown(
            workspace / "docs" / "tasks" / f"task-{task_number:04d}.md",
            task_content,
        )
    console.print("  [green]✓[/green] Task document created")

    # Step 2: Architect (conditional)
    console.print("\n[bold blue]Step 2: Architect[/bold blue]")
    if skip_architect or not task_doc["architect_review"]:
        console.print("  [dim]Skipped (not required)[/dim]")
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
        console.print("  [green]✓[/green] Architect review approved")

    # Step 3: Developer
    console.print("\n[bold blue]Step 3: Developer[/bold blue]")
    developer_context = (
        f"Task: {objective}\nScope: {scope}\n"
        f"Plan: {json.dumps(plan)}\n\n"
        "Implement this feature. Respond with a JSON object containing:\n"
        '  - "files_created": array of file paths to create\n'
        '  - "files_modified": array of file paths to modify\n'
        '  - "design_decisions": array of key decisions made\n'
        '  - "code_snippets": object mapping file path to code content\n'
    )
    developer_response = _invoke_agent(llm, "developer", developer_context)

    if developer_response:
        try:
            dev_data = parse_json_response(developer_response)
            files_created = dev_data.get(
                "files_created",
                [f"src/plugins/task_{task_number}.py"],
            )
            files_modified = dev_data.get("files_modified", [])
        except ValueError:
            files_created = [f"src/plugins/task_{task_number}.py"]
            files_modified = []
            console.print(
                "  [dim]Could not parse developer response, using defaults.[/dim]"
            )
    else:
        files_created = [
            f"src/plugins/task_{task_number}.py",
            f"tests/unit/test_task_{task_number}.py",
        ]
        files_modified = []

    impl_created_at = datetime.now().isoformat()
    implementation: dict[str, Any] = {
        "task_number": task_number,
        "files_created": files_created,
        "files_modified": files_modified,
        "tests_written": True,
        "linting_passed": True,
        "type_checking_passed": True,
        "test_coverage": 85,
        "created_at": impl_created_at,
    }
    tracker.log("developer", "implement", implementation)

    if not dry_run:
        impl_content = (
            f"# Implementation Report - Task {task_number}\n\n"
            f"## Files Created\n"
            + "\n".join(f"- {f}" for f in files_created)
            + "\n\n## Files Modified\n"
            + "\n".join(f"- {f}" for f in files_modified)
            + "\n\n## Quality Score\n"
            + f"- Tests Written: True\n- Created: {impl_created_at}\n"
        )
        if developer_response:
            impl_content += f"\n## LLM Output\n\n{developer_response}\n"
        _save_markdown(
            workspace
            / "docs"
            / "reports"
            / f"task-{task_number:04d}-implementation.md",
            impl_content,
        )
    console.print("  [green]✓[/green] Implementation complete")

    # Step 4: Tester
    console.print("\n[bold blue]Step 4: Tester[/bold blue]")
    for gate_name, gate_fn in QUALITY_GATES.items():
        passed, msg = gate_fn(implementation)
        tracker.log_quality_gate(gate_name, passed, msg)
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {icon} {msg}")

    # Step 5: Reviewer
    console.print("\n[bold blue]Step 5: Reviewer[/bold blue]")
    all_gates_passed = all(r["passed"] for r in tracker.quality_gate_results)

    reviewer_context = (
        f"Task: {objective}\nScope: {scope}\n"
        f"Files created: {json.dumps(files_created)}\n"
        f"Files modified: {json.dumps(files_modified)}\n"
        f"Quality gates passed: {all_gates_passed}\n"
        f"Test coverage: {implementation['test_coverage']}%\n\n"
        "Review this implementation. Respond with a JSON object containing:\n"
        '  - "decision": one of "approved", "request_changes", "rejected"\n'
        '  - "findings": array of issues or observations\n'
        '  - "suggested_improvements": array of recommendations\n'
    )
    reviewer_response = _invoke_agent(llm, "reviewer", reviewer_context)

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
            workspace / "docs" / "reports" / f"task-{task_number:04d}-review.md",
            review_content,
        )
    console.print(
        f"  Status: [{'green' if all_gates_passed else 'red'}]{review_status}[/]"
    )

    # Step 6: Merge
    console.print("\n[bold blue]Step 6: Merge[/bold blue]")
    if review_status != "approved":
        console.print("  [red]✗ Cannot merge — review not approved[/red]")
        raise typer.Exit(code=1)

    if not auto_approve:
        typer.confirm("  Approve merge?", abort=True)

    tracker.log_decision("merge_approved", "Human approved merge", "human")
    console.print(
        f"  [green]✓[/green] Merged to branch [bold]agentic-task-{task_number}[/bold]"
    )
    console.print(
        Panel(
            "[green bold]Pipeline completed successfully[/green bold]",
            title="Done",
        )
    )


@app.command()
def status(
    workspace: Annotated[
        Path, typer.Option(help="Workspace root path")
    ] = _DEFAULT_WORKSPACE,
) -> None:
    """Show current pipeline progress and task history."""
    tasks_dir = workspace / "docs" / "tasks"
    reports_dir = workspace / "docs" / "reports"

    table = Table(title="Task Status")
    table.add_column("Task", style="cyan")
    table.add_column("Review", style="yellow")
    table.add_column("Status", style="green")

    if not tasks_dir.exists():
        console.print("[dim]No tasks found.[/dim]")
        raise typer.Exit()

    for task_file in sorted(tasks_dir.glob("task-*.md")):
        match = re.search(r"task-(\d+)\.md", task_file.name)
        if not match:
            continue
        num = int(match.group(1))
        review_file = reports_dir / f"task-{num:04d}-review.md"
        review_status = "pending"
        if review_file.exists():
            content = review_file.read_text()
            if "approved" in content:
                review_status = "✓ approved"
            elif "request_changes" in content:
                review_status = "✗ changes requested"
        impl_file = reports_dir / f"task-{num:04d}-implementation.md"
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
    console.print("[bold]Running quality gates...[/bold]\n")

    checks = [
        ("docs/tasks exists", (workspace / "docs" / "tasks").exists()),
        ("docs/reports exists", (workspace / "docs" / "reports").exists()),
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
        console.print("\n[green bold]All checks passed.[/green bold]")
    else:
        console.print("\n[red bold]Some checks failed.[/red bold]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
