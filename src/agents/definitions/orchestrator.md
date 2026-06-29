# Agent Orchestration Flow

This document defines the orchestration flow for the agentic development process in this project.

## Workflow Pipeline

The agentic development process follows this sequence:

```
Requirement → Planner → Architect (if structural) → Developer → Tester → Reviewer → Merge
```

### Step-by-Step Process:

1. **Requirement Input**
   - A requirement, feature request, or issue is submitted to the system
   - This could come from a human user, another system, or an automated trigger

2. **Planner Agent**
   - The Planner analyzes the requirement and creates a Task Document
   - The Task Document is stored in `/docs/tasks/task-XXXX.md`
   - The Planner identifies if the change is structural (requires architectural review)

3. **Architect Agent (Conditional)**
   - If the Planner marks the task as structural, the Architect reviews the plan
   - The Architect validates alignment with ADRs and architectural principles
   - The Architect may approve, request changes, or create/update ADRs
   - If not structural, this step is skipped

4. **Developer Agent**
   - The Developer implements the feature based on the (potentially architect-reviewed) Task Document
   - The Developer writes code and tests following project conventions
   - The Developer produces an Implementation Report stored in `/docs/reports/task-XXXX-implementation.md`

5. **Tester Agent**
   - The Tester creates additional tests as needed and validates test coverage
   - The Tester ensures tests are meaningful and cover edge cases
   - The Tester verifies that new and existing tests pass

6. **Reviewer Agent**
   - The Reviewer examines the Implementation Report and code changes
   - The Reviewer checks for adherence to standards, principles, and test coverage
   The Reviewer produces no errors, type checking passes
   - The Reviewer verifies architectural compliance and adequate test coverage
   - The Reviewer produces a Review Report stored in `/docs/reports/task-XXXX-review.md`
   - The Reviewer decides to Approve, Request Changes, or Reject

7. **Merge / Feedback Loop**
   - If Approved: The changes are merged into the main codebase
   - If Request Changes: Feedback is sent back to the Developer (and potentially Architect/Planner) for revision
   - If Rejected: The task is returned to the Planner for re-evaluation

## Decision Points:

- **Architectural Significance**: The Planner determines if a task requires Architect review based on whether it touches:
  - Core Engine interfaces or contracts
  - Plugin registration or lifecycle mechanisms
  - Workflow execution or DAG validation
  - Execution Context or Isolation mechanisms
  - Governance validation engine
  - Fundamental architectural patterns

- **Quality Gates**: Each agent acts as a quality gate:
  - Planner: Ensures work is well-defined and actionable
  - Architect: Ensures architectural integrity (when applicable)
  - Developer: Ensures implementable solution
  - Tester: Ensures testability and coverage
  - Reviewer: Ensures overall quality and compliance

## Artifacts:

Each completed task produces three main artifacts:
1. **Task Document** (`/docs/tasks/task-XXXX.md`) - Created by Planner
2. **Implementation Report** (`/docs/reports/task-XXXX-implementation.md`) - Created by Developer
3. **Review Report** (`/docs/reports/task-XXXX-review.md`) - Created by Reviewer

## Naming Convention:

Task and report files use sequential numbering: `task-0001.md`, `task-0002.md`, etc.
The corresponding reports use the same number: `task-0001-implementation.md`, `task-0001-review.md`.

## Escalation:

If there are disagreements between agents that cannot be resolved through the normal flow:
- Developer ↔ Tester: Escalate to Reviewer for tie-breaking
- Developer/Reviewer ↔ Architect: Escalate to Planner for re-scoping
- Persistent conflicts: Require human intervention

This orchestration flow ensures that all development follows the project's architectural principles while maintaining quality standards through automated agent collaboration.
