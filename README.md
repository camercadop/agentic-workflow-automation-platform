# agentic-workflow-automation-platform

> **Status:** Phases 1–6 complete (Core Engine, Persistence, API Layer, Execution Policies, Agent Infrastructure, Condition Plugins Library).
>
> The architecture documentation (ADRs and C4 diagrams) remains the authoritative source of truth.

## Project Goals
### Product Goal
- Build a plugin‑based workflow automation platform (DAG-based, non-linear pipelines) that can be extended by third‑party developers.

### Engineering Goal
- Showcase a fully‑autonomous, agent‑driven software development lifecycle: requirements → design → implementation → testing → review → documentation → merge.
- Prove that complex engineering processes can be orchestrated by specialized AI agents without human‑written boilerplate code.
- Establish reusable patterns (agents, skills, ADRs) for future projects.

This project is a demonstration of an **Agentic Software Development Process**. While the target product is a plugin-based workflow automation platform, the primary goal is to showcase how specialized AI agents collaborate to design, implement, test, review, and document software autonomously.

> **New here?** Start with the [Agentic Development Pipeline](docs/AGENTIC_DEVELOPMENT_PIPELINE.md) to understand how the entire agent-driven process works end-to-end.

## Why This Project Exists
This platform exists to demonstrate two core innovations:

1. **Autonomous Engineering**: It proves that specialized AI agents can orchestrate the entire software development lifecycle—from requirements to merge—without human-written boilerplate. This eliminates repetitive tasks and accelerates development while maintaining architectural rigor.

2. **Plugin‑First Extensibility**: By standardizing plugin contracts and build-time registration, the system provides a foundation for third‑party developers to create reusable workflow components while adhering to strict governance and isolation rules.

Together, these innovations showcase a practical blueprint for scalable, secure, and agent‑driven software systems that can be adapted for future projects.

## Architecture

This platform implements an **agentic software development lifecycle** (ASDL) and **plugin-based workflow automation**, designed to demonstrate autonomy, composability, and governance.

### Core Architectural Principles
1. **Plugin Isolation (ADR-004)**: Plugins execute in sandboxed environments with enforced contract boundaries.
2. **Core Minimalism (ADR-001)**: Core Engine handles only registry loading, lifecycle, and workflow orchestration.
3. **Agentic Development (ADR-008)**: Agent-driven design, code generation, and validation remain separate from runtime.
4. **Build-Time Governance (ADR-009)**: Compliance enforced via static validation gates during CI/CD.
5. **Composable Workflows (ADR-007)**: Workflows are DAGs enabling branching, parallelism, and merge points.

## Core Components
These components embody the architectural principles defined in the ADRs and form the foundation of the platform's runtime behavior.

- **Workflow Runtime (ADR-007)**: Executes the workflow DAG, respecting defined dependencies, non-linear paths, and pruning invalid branches. Validated during build time.
- **Plugin Contract Model (ADR-005)**: Defines standardized interfaces and contracts for plugins without exposing concrete implementation classes or validation mechanisms.
- **Execution Context (ADR-006)**: Per‑execution context instance isolation boundary that encapsulates memory, threads, and sandbox scopes. Ensures complete isolation even within the same workflow.
- **Build‑Time Validation Framework (ADR‑009)**: Enforces architectural compliance through gates (Manifest, Contract, Security, Context, Workflow) before deployment.
- **Execution Policies**: Per-node retry, timeout, and error handling strategies that provide resilience during workflow execution.
- **Pipeline Guards**: Post-step validation functions that verify artifact existence, syntax correctness, test execution, and report-to-git consistency before allowing the pipeline to advance.

### System Structure
| Layer | Responsibility | ADR Reference |
|-------|-----------------|---------------|
| **Development** | Agent-driven code, tests, and docs generation | ADR-008 |
| **Runtime** | Core Engine (plugin registry, execution) and plugin isolation | ADR-001, ADR-002, ADR-004 |
| **Governance** | Build-time validation gates and lead architect oversight | ADR-009 |
| **Workspace** | Structured by purpose: plugins, ADRs, agent logic | See `/docs/architecture/c4/` |

## The Domain
The platform implements a **non‑linear workflow pipeline** defined as a **directed acyclic graph (DAG)** of plugin instances. Nodes represent plugin executions (Trigger, Condition, Transformer, Action) and typed edges define data flow between them, enabling branching, parallelism, and merging (see ADR-007).

### Domain Example
Consider a simple **Email Alert** workflow:
1. **Trigger** – A timer checks a message queue every 5 min.
2. **Condition** – Only proceed if the message payload `priority` is `high`.
3. **Transformer** – Add a `timestamp` field and redact any `PII` data.
4. **Action** – Send an email via an SMTP plugin.

All four steps are implemented as separate plugins, enabling independent development and reuse across workflows.

- **Plugin Registry Loading**: Plugins are statically registered via a build‑time configuration file and loaded from the generated registry at startup. No runtime discovery is performed (see ADR‑002).
- **Lifecycle Management**: Manages plugin lifecycle states (Registered, Activated, Active, Deactivated, Cleaned Up) as defined in ADR‑003.
- **Workflow Orchestration**: Executes the workflow DAG, respecting defined dependencies, non‑linear paths, and per‑instance execution contexts (ADR‑006).

### Governance Principles
Two layers of governance ensure both development quality and runtime compliance.

**Agentic Development Governance (ADR-008)**
- **Agentic Decision Support**: Autonomous agents handle design, implementation, and validation under the guidance and final approval of the Lead Architect.
- **Agent-Written Core**: Agents implement Core Engine infrastructure (loading, orchestration, state) but **must not** embed business logic.

**Runtime Governance (ADR-009)**
- **Plugin Isolation**: Each plugin operates independently with clear contracts (ADR-004).
- **Build-Time Validation Enforcement**: Automated enforcement via five build-time validation gates prevents invalid artifacts from entering the registry.

### Execution Context & Governance Boundaries
Clear architectural boundaries separate plugin execution from core governance.

- **Execution Context (ADR-006)**: Per-execution context instance isolation boundary that encapsulates memory, threads, and sandbox scopes for execution. Each execution context instance receives its own execution context, ensuring complete isolation even within the same workflow.
- **Plugin Boundaries**: Plugins execute in isolation with explicit contract validation; no direct access to Core internals
- **Governance Gates (ADR-009)**: Automated validation checkpoints at plugin registration, workflow definition (pre-deployment)

## Plugin Architecture
- **Contract-First**: Plugins are developed to conform to the standardized contracts defined by the Plugin Contract Model (ADR-005), without reference to specific implementation classes.
- **Metadata-Driven**: Plugins declare metadata through standardized manifests or inline `@register_plugin` annotations (see ADR-002).
- **Build-Time Registration**: Plugins are validated during CI/CD, generating a static registry. No runtime discovery is performed.
- **Isolation & Validation**: Plugins execute in isolated contexts with contract validation; failures are reported during validation (ADR-004).

## MVP Scope
- **Core Components**: Plugin Contracts, Plugin Registry, Execution Context, Workflow Definition, Workflow Executor, Execution Policies
- **Governance**: Agent collaboration under architect oversight
- **Process**: Full pipeline from requirement to merge


## Tech Stack
- **Language**: Python 3.12+
- **Web Framework**: FastAPI + Uvicorn
- **Data Validation**: Pydantic v2
- **Database**: PostgreSQL 16
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Migrations**: Alembic
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter/Formatter**: Ruff
- **Type Checking**: MyPy (strict mode)
- **Testing**: Pytest + pytest-cov
- **CLI Framework**: Typer + Rich
- **LLM Client**: OpenAI SDK (compatible with OpenRouter)
- **Containerization**: Docker + Docker Compose

## Project Structure
```
├── agents/            # Development-time agent definitions (ADR-008)
├── skills/            # Reusable agent capabilities
├── prompts/           # LLM prompt templates per agent role
├── src/
│   ├── core/          # Core Engine (registry, lifecycle, orchestration, bootstrap)
│   ├── plugins/       # Plugin implementations (triggers, conditions, transformers, actions)
│   ├── governance/    # Validation gates (ADR-009) and pipeline guards
│   ├── agents/        # Agent infrastructure (LLM client, tools, prompts)
│   │   ├── llm/      # LLM client (single-shot + tool-calling loop)
│   │   ├── prompts/  # Per-agent system prompts
│   │   ├── skills/   # Skill documentation (referenced by prompts)
│   │   └── definitions/ # Agent role definitions
│   ├── models/        # SQLModel persistence models
│   ├── repositories/  # Repository pattern for data access
│   ├── api/           # FastAPI application (routes, schemas, errors)
│   └── database.py    # Engine and session management
├── migrations/        # Alembic database migrations
├── tests/
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── docs/
│   ├── adr/           # Architectural Decision Records
│   ├── architecture/  # C4 diagrams, domain model, vision
│   └── tasks/         # Per-task directories (agentic process)
│       ├── 0001/      # Task 1 artifacts
│       │   ├── task.md
│       │   ├── implementation.md
│       │   └── review.md
│       ├── 0002/      # Task 2 artifacts (etc.)
│       ├── TASK_TEMPLATE.md
│       ├── IMPLEMENTATION_REPORT_TEMPLATE.md
│       └── REVIEW_REPORT_TEMPLATE.md
├── pyproject.toml     # Project config, dependencies, tool settings
└── uv.lock            # Lockfile
```

## Scripts

### Orchestrator CLI

The `scripts/orchestrator.py` CLI provides semi-automatic orchestration of AI agents for development tasks. It automates routine steps (planning, implementation, testing, review) while maintaining human oversight at key checkpoints.

```bash
# Run the full agentic pipeline for a requirement
uv run python scripts/orchestrator.py run "Create a RegexCondition plugin"

# Dry run (no file writes, enables DEBUG logging)
uv run python scripts/orchestrator.py run --dry-run "Add a TimerTrigger plugin"

# Skip manual confirmations (for CI)
uv run python scripts/orchestrator.py run --auto-approve "Add logging transformer"

# Skip architect review step
uv run python scripts/orchestrator.py run --skip-architect "Fix typo in README"

# Resume a failed/incomplete task (auto-detects last completed step)
uv run python scripts/orchestrator.py resume 1

# Resume from a specific step (e.g. retry from Developer step)
uv run python scripts/orchestrator.py resume 1 --from-step 3

# Resume without manual confirmations
uv run python scripts/orchestrator.py resume 1 --auto-approve

# Check status of all tasks
uv run python scripts/orchestrator.py status

# Validate workspace structure
uv run python scripts/orchestrator.py validate
```

| Command    | Description                                          |
|------------|------------------------------------------------------|
| `run`      | Execute the full pipeline (plan → architect → dev → test → review) |
| `resume`   | Resume a failed/incomplete task from where it left off |
| `status`   | Show task history and review states                  |
| `validate` | Run structural quality gates against the workspace   |

#### Resume Behavior

The `resume` command auto-detects the last completed step by checking for existing artifacts in the per-task directory (`docs/tasks/NNNN/`):

| Artifact exists | Inferred last completed step |
|-----------------|------------------------------|
| `task.md` only | Step 1 (Planner) |
| + `implementation.md` | Step 3 (Developer) |
| + `review.md` (not approved) | Step 4 (Tester) |
| + `review.md` (approved) | Step 5 (Reviewer) |

Use `--from-step N` to override auto-detection and force re-execution from a specific step.

When resuming from Step 3 (Developer), if a previous `review.md` exists with findings, those findings are automatically included in the developer's context. This creates a feedback loop where the developer addresses reviewer concerns directly.

#### Pipeline Guards

The orchestrator enforces **pipeline guards** between steps to prevent phantom implementations from advancing. If the Developer agent claims to create files that don't exist on disk, or if tests fail, the pipeline is blocked with actionable error messages and a resume command.

Guards run automatically at these boundaries:
- **Post-Developer**: Artifact existence, path validation, syntax validation
- **Post-Tester**: Actual test execution (runs `pytest`), real coverage measurement via `pytest-cov`
- **Pre-Reviewer**: Reviewer precondition, report-to-git consistency

After tests pass, the orchestrator measures actual test coverage by running pytest with `--cov-report=json` and extracting the total percentage. This real value is passed to quality gates and the reviewer.

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md#pipeline-guards) for full details.

#### Logging

The orchestrator uses Python's `logging` module for structured operational output (separate from the Rich console UI). Logs include timing per step, agent invocation details, quality gate results, and decision audit trails. Dry-run mode (`--dry-run`) enables DEBUG-level logging for deeper visibility.

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/workflow_db` |
| `POSTGRES_USER` | PostgreSQL user (Docker Compose) | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password (Docker Compose) | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name (Docker Compose) | `workflow_db` |
| `LLM_API_KEY` | API key for LLM provider | — |
| `LLM_BASE_URL` | LLM API base URL | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | Model identifier | `openrouter/free` |
| `LLM_MAX_TOKENS` | Max tokens per LLM response | `4096` |
| `LLM_TEMPERATURE` | LLM sampling temperature | `0.3` |

## Development Setup

```bash
# Install dependencies (including dev tools)
uv sync --extra dev

# Copy environment file
cp .env.example .env

# Start PostgreSQL (via Docker)
docker compose up db -d

# Run database migrations
uv run alembic upgrade head

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/

# Run tests
uv run pytest

# Run tests with verbose coverage
uv run pytest --cov=src --cov-report=html

# Start the API server
uv run uvicorn src.api.main:app --reload
```

## API Reference

Once running, the API is available at `http://localhost:8000`. Interactive docs at `/docs` (Swagger UI) and `/redoc`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/workflows/` | List all workflows |
| `POST` | `/workflows/` | Create a workflow (validates DAG) |
| `GET` | `/workflows/{id}` | Get workflow by ID |
| `PATCH` | `/workflows/{id}` | Update workflow (re-validates DAG) |
| `DELETE` | `/workflows/{id}` | Delete workflow |
| `POST` | `/workflows/{id}/execute` | Execute a workflow |
| `GET` | `/executions/` | List all executions |
| `GET` | `/executions/{id}` | Get execution by ID |
| `POST` | `/executions/` | Create execution record |
| `PATCH` | `/executions/{id}` | Update execution status |
| `DELETE` | `/executions/{id}` | Delete execution |
| `GET` | `/plugins/` | List registered plugins |
| `POST` | `/plugins/` | Register a plugin |
| `GET` | `/plugins/{id}` | Get plugin by ID |
| `PATCH` | `/plugins/{id}` | Update plugin lifecycle state |
| `DELETE` | `/plugins/{id}` | Delete plugin |

### Quickstart Examples

```bash
# Create a workflow
curl -X POST http://localhost:8000/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "nodes": [
      {"node_id": "trigger", "plugin_name": "manual-trigger"},
      {"node_id": "action", "plugin_name": "log-action"}
    ],
    "edges": [
      {"source_node": "trigger", "source_port": "payload", "target_node": "action", "target_port": "data"}
    ]
  }'

# Execute the workflow (replace <workflow-id> with the returned UUID)
curl -X POST http://localhost:8000/workflows/<workflow-id>/execute \
  -H "Content-Type: application/json" \
  -d '{"initial_data": {"msg": "hello"}}'

# Create a workflow with execution policies (retry + timeout)
curl -X POST http://localhost:8000/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resilient-workflow",
    "nodes": [
      {"node_id": "trigger", "plugin_name": "manual-trigger"},
      {"node_id": "action", "plugin_name": "log-action", "config": {
        "policy": {
          "retry": {"max_attempts": 3, "delay_seconds": 1.0, "backoff_factor": 2.0},
          "timeout": {"timeout_seconds": 10.0},
          "error_strategy": "skip_node"
        }
      }}
    ],
    "edges": [
      {"source_node": "trigger", "source_port": "payload", "target_node": "action", "target_port": "data"}
    ]
  }'

# Check health
curl http://localhost:8000/health
```

## Execution Policies

Each workflow node can be configured with resilience policies:

| Policy | Options | Default |
|--------|---------|---------|
| **Retry** | `max_attempts`, `delay_seconds`, `backoff_factor` | 1 attempt, 0s delay, 2.0x backoff |
| **Timeout** | `timeout_seconds` | 30s |
| **Error Strategy** | `fail_fast`, `skip_node`, `continue` | `fail_fast` |

Error strategies determine workflow behavior on node failure:
- `fail_fast` — Abort the entire workflow immediately
- `skip_node` — Mark node as skipped, continue downstream
- `continue` — Record failure, continue execution

## Docker

```bash
# Start all services (API + PostgreSQL)
docker compose up --build

# Run in detached mode
docker compose up --build -d

# Start only the database
docker compose up db -d

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

The API is available at `http://localhost:8000` and PostgreSQL at `localhost:5432`.

## Agentic Workflow
Every feature follows this automated lifecycle:

```mermaid
flowchart TD
    A[Requirement] --> B[ArchitectAgent]
    B --> C[PlannerAgent]
    C --> D[DeveloperAgent]
    D --> E[TesterAgent]
    E --> F[ReviewerAgent]
    F -->|approved| G[Done]
    F -->|request_changes| D
```

> For a complete, step-by-step explanation of this flow (with diagrams, tool-calling details, guards, and feedback loops), see **[Agentic Development Pipeline](docs/AGENTIC_DEVELOPMENT_PIPELINE.md)**.

### Agent Tool-Calling

The Developer, Tester, and Reviewer agents use an agentic tool-calling loop to interact with the codebase. Instead of producing text-only responses, they can:

- **Read files** to understand existing patterns
- **Write files** to create source code and tests
- **List directories** to explore the project structure
- **Run commands** to validate with ruff, mypy, and pytest

The LLM client (`src/agents/llm/client.py`) implements the loop: send message with tool schemas → execute tool calls → feed results back → repeat until the agent produces a final text response.

Tools are sandboxed: writes are restricted to `src/`, `tests/`, `docs/`; commands are allowlisted; path traversal is blocked.

The Reviewer agent receives the full source code of created/modified files in its prompt context, ensuring findings are grounded in actual code rather than hallucinated.

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md#agent-infrastructure) for full details.

## Architecture Documentation

- **⭐ Agentic Development Pipeline**: [`docs/AGENTIC_DEVELOPMENT_PIPELINE.md`](docs/AGENTIC_DEVELOPMENT_PIPELINE.md) – how agents drive the full development lifecycle (start here)
- **ADR Index**: [`/docs/adr/`](docs/adr/) – all Architectural Decision Records
- **C4 Level 0 – System Context**: [`level-0-system-context.md`](docs/architecture/c4/level-0-system-context.md)
- **C4 Level 1 – Container Diagram**: [`level-1-container.md`](docs/architecture/c4/level-1-container.md)
- **C4 Level 2 – Component Diagrams**: Core Engine, Workflow Runtime, Plugin Packages, Governance, Context Manager, Isolation Service, Platform API, Development Agents
- **Architecture Overview**: [`docs/architecture/architecture-overview.md`](docs/architecture/architecture-overview.md)
- **Domain Model**: [`docs/architecture/domain-model.md`](docs/architecture/domain-model.md)
- **Vision**: [`docs/architecture/vision.md`](docs/architecture/vision.md)
- **Code Standards**: [`docs/CODE_STANDARDS.md`](docs/CODE_STANDARDS.md) – linting, formatting, and style rules
- **Developer Guide**: [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) – module usage and architecture constraints
- **Testing Guide**: [`docs/TESTING.md`](docs/TESTING.md) – testing conventions, structure, and examples
- **Glossary**: [`GLOSSARY.md`](GLOSSARY.md) – key terminology and definitions
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md) – coding standards and contribution rules

## ADR Summary

| ADR | Title | Scope |
|-----|-------|-------|
| 001 | Plugin-First Architecture | Runtime |
| 002 | Plugin Registration Model | Runtime |
| 003 | Plugin Lifecycle Model | Runtime |
| 004 | Plugin Isolation Model | Runtime |
| 005 | Plugin Contract Definitions | Runtime |
| 006 | Execution Context Strategy | Runtime |
| 007 | Workflow Graph Specification | Runtime |
| 008 | Agentic Development Model | Development |
| 009 | Governance and Validation Framework | Runtime |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `psycopg2` install fails | Install `libpq-dev` (Linux) or `brew install postgresql` (macOS) |
| Database connection refused | Ensure PostgreSQL is running: `docker compose up db -d` |
| Alembic migration errors | Verify `DATABASE_URL` is set and database exists |
| Tests use wrong DB | Tests default to SQLite in-memory via `conftest.py`; no PostgreSQL needed |
| LLM agent errors | Verify `LLM_API_KEY` and `LLM_BASE_URL` in `.env` |
| Import errors in tests | Run `uv sync --extra dev` to install all dev dependencies |

## License
This project is released under the [Apache License, Version 2.0](LICENSE).
See the [LICENSE](LICENSE) file for full license text.
