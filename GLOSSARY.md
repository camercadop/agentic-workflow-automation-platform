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
Architectural pattern where plugins implement standardized contracts defined by the Plugin Contract Model (ADR‑005) before any business logic is added.

## DAG (Directed Acyclic Graph)
The underlying structure of workflows; Workflow Nodes represent configured Plugin Types and their execution materializes Plugin Instances, while edges define data flow, allowing branching, parallelism, and merging.

## Documentation Agent
Agent that writes and maintains user guides, API references, and other documentation.

## Execution Context
Runtime Object provisioned by Context Manager before a Plugin Instance executes; it provides isolated memory, threading, and sandbox boundaries for that execution and is destroyed immediately afterwards. Execution contexts are never shared between Plugin Instances, ensuring strict isolation per ADR‑006.

## Execution Context Strategy (ADR‑006)
Per‑Plugin Instance isolation that encapsulates memory, threads, and sandbox scopes, ensuring complete isolation even within the same workflow.

## Isolation Service
Single authority for authorization decisions. All permission evaluations are performed here, and no other component is allowed to decide on access rights.

## Validation Gates
Validation steps that prevent non‑compliant artifacts from entering the registry.

## Governance and Validation Framework (ADR‑009)
Build‑time validation gates (manifest, contract, security, context, workflow) that enforce architectural compliance before deployment.

## Lifecycle Hook
Optional function a plugin may implement to react to lifecycle state transitions (e.g., `on_activated`).

## Metadata‑Driven
Plugins declare capabilities, version, and entry points via a standardized manifest processed at build time.

## Node Executor
Runtime Component within Workflow Runtime that requests an Execution Context from Context Manager, materializes a Plugin Instance from the referenced Plugin Type, and executes it within that Execution Context.

## Non‑Linear Pipelines
Workflows that are not strictly sequential; they may branch, run in parallel, and converge.

## Plugin
Independent component implementing one of the extensibility points (Trigger, Condition, Transformer, Action) and conforming to defined contracts.

## Plugin Instance
Runtime Object materialized by Node Executor from a Workflow Node's referenced Plugin Type. It executes within its own Execution Context and may interact with platform services via the Plugin Runtime API.

## Plugin Runtime API
The standardized interface through which plugins interact with platform services (execution context, metadata, logging, metrics, configuration, event bus) and request resource access. All interactions are mediated by the Context Manager and validated by the Isolation Service to ensure compliance with the Plugin Isolation Model (ADR‑004).

## Plugin Contract Definitions (ADR‑005)
Defines the standardized contracts that plugins must adhere to, described without reference to concrete classes, inheritance, or specific validation technologies.

## Plugin Contract Model
Set of interface definitions and schemas that define the required interface for each plugin type, expressed in an implementation-neutral manner.

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



## Plugin Package
Distributable artifact (e.g., wheel, zip) that contains a plugin's compiled code, its standardized metadata manifest, and any required resources for registration and execution.

## Static Registry
Generated artifact containing all validated plugin definitions; loaded by the Core Engine at startup.

## Platform API
Programmatic interface exposed by the platform for **external callers** to submit workflow definitions, query execution status, and control workflow execution. It is the public-facing endpoint of the system.

## Skill
Reusable capability or tool that an agent can invoke (e.g., linters, formatters, validators).

## Subagent
Temporary specialized agent spawned by another agent to complete a bounded task.

## Test Generator Agent
Agent that produces unit, integration, and contract tests for generated artifacts.

## Validation Engine
Build‑time component that executes validation gates and produces validation reports. It is the implementation artifact of the Governance Framework and runs as part of the CI/CD pipeline. The validation reports are used by the Registry Builder tool to compile the final Static Registry artifact.

## Workflow Runtime
Component that executes the workflow DAG, respecting dependencies and isolation rules. It is composed of:

* **Node Executor** – requests an Execution Context from Context Manager, materializes a Plugin Instance from the referenced Plugin Type, and executes it within that Execution Context.
* **Routing Engine** – determines the order of node execution based on DAG dependencies and handles branching/merging.
* **Context Manager** – Single authorization gateway for plugins. It forwards all resource requests to the Isolation Service and ensures that only approved permissions are granted.

## Workflow Context
Runtime‑owned, mediated data‑mapping container scoped to a workflow execution. The workflow runtime owns and controls this context, mapping node outputs to subsequent node inputs. Plugins interact with it only through the runtime’s mediation, ensuring isolation between plugin instances.

## Workflow Node
Static definition in a Workflow Graph that references a Plugin Type and its configuration. A Workflow Node does not create runtime objects; Node Executor materializes a Plugin Instance when the node is scheduled.
