# Agent System Prompts

Per-agent system prompts injected as the first message in each LLM conversation. These define each agent's identity, responsibilities, constraints, and expected output format.

## Prompt Index

| Prompt | Agent | Role |
|--------|-------|------|
| `architect_system_prompt.md` | Architect | Design validation, ADR compliance, structural approval |
| `planner_system_prompt.md` | Planner | Task decomposition, dependency analysis, acceptance criteria |
| `developer_system_prompt.md` | Developer | Code generation with tool use (read/write/run) |
| `tester_system_prompt.md` | Tester | Test creation, edge-case detection, coverage validation |
| `reviewer_system_prompt.md` | Reviewer | Code review, standards enforcement, approve/reject decisions |

## How Prompts Are Used

The LLM client (`src/agents/llm/client.py`) injects the appropriate system prompt as the first message in the conversation based on the agent role being invoked. The prompt establishes:

1. **Identity** — Who the agent is and its position in the pipeline
2. **Responsibilities** — What the agent must accomplish
3. **Constraints** — Rules the agent must follow (e.g., tool usage, coding standards)
4. **Output format** — The expected structure of the agent's final response

## Prompt Structure Conventions

Each prompt follows a consistent structure:

```
# {Agent} System Prompt

Role introduction paragraph.

## Core Responsibilities:
Numbered list of duties.

## Operating Principles:
Behavioral guidelines and collaboration rules.

## Output Format:
Expected response structure.
```

The Developer and Reviewer prompts additionally include:
- **Available Tools** — Tool schemas the agent can invoke (`read_file`, `write_file`, `list_directory`, `run_command`)
- **Coding Conventions** — Reference to `docs/CODE_STANDARDS.md` as the single source of truth
- **Workflow** — Step-by-step execution order (explore → implement → test → validate)

## Agent Pipeline Order

Prompts are designed to work in sequence, with each agent's output feeding the next:

```
Planner → Architect → Developer → Tester → Reviewer
                                      ↑          |
                                      └──────────┘ (request_changes loop)
```

## Modifying Prompts

When updating a prompt:
- Maintain the existing section structure
- Keep instructions specific and actionable — avoid vague guidance
- Reference ADRs and `docs/CODE_STANDARDS.md` rather than duplicating rules inline
- Test changes by running the orchestrator on a sample task (`scripts/orchestrator.py`)
