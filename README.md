# agentic-workflow-automation-platform

> **Status:** Phases 1–3 complete (Core Engine, Persistence, API Layer). Phase 4 (Execution Policies) **next**.
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

-- **Workflow Runtime (ADR-007)**: Executes the workflow DAG, respecting defined dependencies, non-linear paths, and pruning invalid branches. Validated during build time.
-- **Plugin Contract Model (ADR-005)**: Defines standardized interfaces and contracts for plugins without exposing concrete implementation classes or validation mechanisms.
-- **Execution Context (ADR-006)**: Per‑execution context instance isolation boundary that encapsulates memory, threads, and sandbox scopes. Ensures complete isolation even within the same workflow.
-- **Build‑Time Validation Framework (ADR‑009)**: Enforces architectural compliance through gates (Manifest, Contract, Security, Context, Workflow) before deployment.

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
- **Core Components**: Plugin Contracts, Plugin Registry, Execution Context, Workflow Definition, Workflow Executor
- **Governance**: Agent collaboration under architect oversight
- **Process**: Full pipeline from requirement to merge


## Tech Stack
- **Language**: Python 3.12+
- **Web Framework**: FastAPI + Uvicorn
- **Data Validation**: Pydantic v2
- **Database**: PostgreSQL
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter/Formatter**: Ruff
- **Type Checking**: MyPy (strict mode)
- **Testing**: Pytest + pytest-cov

## Project Structure
```
├── src/
│   ├── core/          # Core Engine (registry, lifecycle, orchestration, bootstrap)
│   ├── plugins/       # Plugin implementations (triggers, conditions, transformers, actions)
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
│   └── architecture/  # C4 diagrams, domain model, vision
├── pyproject.toml     # Project config, dependencies, tool settings
└── uv.lock            # Lockfile
```

## Development Setup

```bash
# Install dependencies (including dev tools)
uv sync --extra dev

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Run tests
uv run pytest

# Run database migrations (requires DATABASE_URL env var)
uv run alembic upgrade head

# Start the API server
uv run uvicorn src.api.main:app --reload
```

## API Quickstart

Once running, the API is available at `http://localhost:8000` (docs at `/docs`).

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
```

## Docker

```bash
# Start all services (API + PostgreSQL)
docker compose up --build

# Run in detached mode
docker compose up --build -d

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
    F --> G[Merge]
```
## Architecture Documentation

- **ADR Index**: [`/docs/adr/`](docs/adr/) – all Architectural Decision Records
- **C4 Level 0 – System Context**: [`level-0-system-context.md`](docs/architecture/c4/level-0-system-context.md)
- **C4 Level 1 – Container Diagram**: [`level-1-container.md`](docs/architecture/c4/level-1-container.md)
- **Glossary**: [`GLOSSARY.md`](GLOSSARY.md) – key terminology and definitions
- **Developer Guide**: [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) – module usage and architecture constraints
- **Testing Guide**: [`docs/TESTING.md`](docs/TESTING.md) – testing conventions, structure, and examples
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md) – coding standards and contribution rules

## License
This project is released under the [Apache License, Version 2.0](LICENSE).
See the [LICENSE](LICENSE) file for full license text.
