# Glossary

## ADR (Architectural Decision Record)
Formal record of architectural decisions; the authoritative source of truth for the platform.

## Agent
An autonomous software entity that performs a specific engineering task (e.g., architecture design, code generation, testing, documentation).

## Agent‑Assisted Development Model (ADR‑008)
Development‑time agents collaborate to generate platform artifacts (plugins, ADRs, tests, docs) while remaining separate from the runtime architecture.

## Agentic Workflow Automation Platform
Plugin‑first workflow automation platform whose runtime executes DAG‑based workflows. AI agents participate **only during development‑time activities** such as architecture design, code generation, testing, and documentation (see ADR‑008).

## Architect Agent
Agent responsible for architectural decisions, ADR generation, and design validation.

## Build‑Time Governance
Enforcement of architectural rules during CI/CD, not at runtime.

## Build‑Time Plugin Registration (ADR‑002)
Plugins are validated and registered during CI/CD, producing a static registry that the Core Engine loads at startup.

## C4 Diagrams
Architecture documentation (System Context, Container) stored under `docs/architecture/c4/`.

## Composable Workflows (ADR‑007)
Workflows are defined as DAGs, enabling branching, parallel execution, and merging of plugin instances.

## Core Engine
Minimal runtime component that provides lifecycle management and workflow orchestration. Plugins are loaded from a **static registry** generated at build time, so the Core Engine performs **no runtime discovery** of plugins.

## Contract‑First
Plugins must implement contracts defined by abstract base classes before any business logic is added.

## DAG (Directed Acyclic Graph)
The underlying structure of workflows; nodes represent plugin executions and edges define data flow, allowing branching, parallelism, and merging.

## Documentation Agent
Agent that writes and maintains user guides, API references, and other documentation.

## Execution Context
Ephemeral isolated environment created for a single plugin‑instance execution and destroyed immediately afterwards. Execution contexts are never shared between plugin instances, ensuring strict isolation per ADR‑006.

## Execution Context Strategy (ADR‑006)
Per‑plugin instance isolation that encapsulates memory, threads, and sandbox scopes, ensuring complete isolation even within the same workflow.

## Isolation Service
Runtime component that provisions and enforces sandboxed execution environments for each plugin instance, guaranteeing that plugins cannot interfere with each other's state or with the core engine.

## Governance Gates
Validation steps that prevent non‑compliant artifacts from entering the registry.

## Governance and Validation Framework (ADR‑009)
Build‑time validation gates (manifest, contract, security, context, workflow) that enforce architectural compliance before deployment.

## Lifecycle Hook
Optional function a plugin may implement to react to lifecycle state transitions (e.g., `on_activated`).

## Metadata‑Driven
Plugins declare capabilities, version, and entry points via a `plugin.yaml` manifest processed at build time.

## Non‑Linear Pipelines
Workflows that are not strictly sequential; they may branch, run in parallel, and converge.

## Plugin
Independent component implementing one of the extensibility points (Trigger, Condition, Transformer, Action) and conforming to defined contracts.

## Plugin Contract Definitions (ADR‑005)
Contract‑first approach where plugins inherit from abstract base classes (`BaseTrigger`, `BaseCondition`, `BaseTransformer`, `BaseAction`) and are validated against Pydantic schemas.

## Plugin Contract Model
Set of abstract base classes and schemas that define the required interface for each plugin type.

## Plugin First Architecture (ADR‑001)
Design principle where all extensibility points are implemented as independent plugins; the core contains no business logic.

## Plugin Generator Agent
Agent that creates plugins compliant with the platform’s contract model.

## Plugin Isolation Model (ADR‑004)
Plugins run in sandboxed execution contexts with strict contract boundaries, preventing direct access to core internals.

## Plugin Lifecycle Model (ADR‑003)
State machine for plugins: **Registered → Activated → Active → Deactivated → Cleaned Up**; optional hooks may be implemented for each transition.

## Plugin Registration
(Covered by Build‑Time Plugin Registration ADR‑002.)

## Plugin Instance
Concrete instantiation of a plugin type within a workflow, bound to a specific execution context and configuration parameters.

## Plugin Package
Distributable artifact (e.g., wheel, zip) that contains a plugin's compiled code, its `plugin.yaml` manifest, and any required resources for registration and execution.

## Static Registry
Generated artifact containing all validated plugin definitions; loaded by the Core Engine at startup.

## Runtime API
Programmatic interface exposed by the Core Engine (e.g., CLI, HTTP, gRPC) that allows external callers to submit workflow definitions, query execution status, and control workflow execution. It operates on the static registry and does not perform runtime plugin discovery.

## Skill
Reusable capability or tool that an agent can invoke (e.g., linters, formatters, validators).

## Subagent
Temporary specialized agent spawned by another agent to complete a bounded task.

## Test Generator Agent
Agent that produces unit, integration, and contract tests for generated artifacts.

## Workflow Runtime
Component that executes the workflow DAG, respecting dependencies and isolation rules. It is composed of:

* **Node Executor** – runs individual plugin instances within their own execution contexts.
* **Routing Engine** – determines the order of node execution based on DAG dependencies and handles branching/merging.
* **Context Manager** – creates and disposes the per‑node execution contexts and enforces isolation guarantees.

## Workflow Context
Shared, per‑workflow state (variables, metadata, intermediate results) that can be read by workflow nodes but is isolated from other concurrent workflow executions.

## Workflow Node
Individual step in the workflow DAG representing the execution of a Plugin Instance. Each node includes metadata such as node ID, dependencies, and the execution context used for that step.
