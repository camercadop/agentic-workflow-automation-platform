# Agent Definitions

Role definitions describing each agent's responsibilities, inputs, outputs, and constraints. These files serve as the authoritative specification for agent behavior within the agentic development pipeline (see [ADR-008](../../../docs/adr/adr-008-agentic-development.md)).

## Pipeline Flow

Agents execute in a defined sequence. Each agent acts as a quality gate before handing off to the next:

```
Requirement → Planner → Architect (conditional) → Developer → Tester → Reviewer → Merge
                                                       ↑                       |
                                                       └── request_changes ────┘
```

If the Reviewer requests changes, the Developer receives the feedback and iterates until approval.

## Agent Summary

| Agent | File | Role | Quality Gate |
|-------|------|------|--------------|
| Orchestrator | `orchestrator.md` | Coordinates the pipeline, invokes agents in sequence, handles escalation | Pipeline integrity |
| Architect | `architect.md` | Validates requirements against ADRs, produces design guidance | Architectural compliance |
| Planner | `planner.md` | Breaks requirements into task files with acceptance criteria | Work decomposition |
| Developer | `developer.md` | Implements code using tool-calling (read/write/run) | Implementation correctness |
| Tester | `tester.md` | Writes and runs tests, measures coverage | Test coverage (≥80%) |
| Reviewer | `reviewer.md` | Reviews implementation against requirements and standards | Overall quality |

## Agent Details

### Orchestrator (`orchestrator.md`)
Defines the end-to-end pipeline sequence, decision points (e.g., when Architect review is required), escalation paths, and artifact naming conventions. This is the "control plane" for the agentic process.

- Determines if a task is architecturally significant
- Manages the feedback loop between Reviewer and Developer
- Defines escalation rules for unresolved conflicts

### Architect (`architect.md`)
Invoked conditionally when a task touches core interfaces, plugin contracts, execution context, or governance mechanisms.

- **Inputs:** Task documents, ADRs, C4 diagrams, proposed designs
- **Outputs:** Approval/rejection, new or updated ADRs, design recommendations
- **Key constraint:** Prioritizes architectural integrity over expedience

### Planner (`planner.md`)
First agent in the pipeline. Decomposes raw requirements into focused, testable task documents.

- **Inputs:** Raw requirements, project documentation, constraints
- **Outputs:** Task Document (`docs/tasks/NNNN/task.md`) with objectives, steps, risks, and acceptance criteria
- **Key constraint:** Tasks must be small, independent, and agent-implementable

### Developer (`developer.md`)
Implements features using an agentic tool-calling loop (read files, write files, run commands).

- **Inputs:** Approved task documents, architectural feedback, reviewer findings (on resume)
- **Outputs:** Source code in `src/`, tests in `tests/`, Implementation Report (`docs/tasks/NNNN/implementation.md`)
- **Key constraint:** Business logic only in plugins; must pass ruff, mypy, and pytest before completion

### Tester (`tester.md`)
Validates implementation through additional test creation and coverage measurement.

- **Inputs:** Implementation Report, code changes, existing test suite
- **Outputs:** Test files, coverage reports
- **Key constraint:** Must not decrease coverage; tests must be meaningful and deterministic

### Reviewer (`reviewer.md`)
Final quality gate. Reviews code with full source context to produce grounded findings.

- **Inputs:** Implementation Report, test results, changed source code
- **Outputs:** Review Report (`docs/tasks/NNNN/review.md`) with decision (Approve / Request Changes / Reject)
- **Key constraint:** Must reference specific ADRs or standards when citing issues

## Artifacts Produced

| Step | Artifact | Location |
|------|----------|----------|
| Planner | Task Document | `docs/tasks/NNNN/task.md` |
| Developer | Implementation Report | `docs/tasks/NNNN/implementation.md` |
| Reviewer | Review Report | `docs/tasks/NNNN/review.md` |

## How Definitions Are Used

1. **System prompts** — The orchestrator loads these definitions to construct per-agent system prompts (see `src/agents/prompts/`).
2. **Behavioral constraints** — Each definition's "Behavioral Rules" section is injected into the LLM context to enforce guardrails.
3. **Documentation** — These files serve as human-readable documentation of agent capabilities and boundaries.

## Editing Guidelines

When modifying agent definitions:
- Keep responsibilities focused and non-overlapping between agents
- Ensure inputs/outputs form a coherent chain across the pipeline
- Update this README if adding or removing agents
- Behavioral rules should be specific and enforceable, not aspirational
