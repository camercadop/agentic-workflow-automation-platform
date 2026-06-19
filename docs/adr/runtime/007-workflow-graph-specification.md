# ADR 007: Workflow Graph Specification

**Status:** Proposed
**Date:** 2026-07-01
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 002, 003, 004, 005, 006

## Context
Workflows are the primary mechanism for composing plugins into cohesive automation pipelines. Without a standardized graph specification, workflows become difficult to design, validate, and execute reliably. Current challenges include:

- Inconsistent workflow definitions across plugin implementations
- Lack of type-safe data flow between plugins
- No formal mechanism for conditional branching or parallel execution
- Difficulty in static analysis for security and compatibility validation
- Absence of versioning for workflow schemas

Constraints include maintaining compatibility with the Plugin Contract Model (ADR 005), supporting the execution context strategy (ADR 006), and preserving plugin isolation (ADR 004).

## Terminology
| Term | Definition |
|------|------------|
| **Workflow Graph** | A directed acyclic graph (DAG) defining the structure and dependency relationships between plugin instances within a workflow. |
| **Node** | A single execution point in the workflow, representing a plugin instance with configured inputs/outputs. |
| **Edge** | A directed connection between nodes defining data or event flow. |
| **Workflow Context** | A workflow-scoped data container managed by the workflow runtime; it carries state through the graph by mapping node outputs to subsequent node inputs, ensuring no direct state sharing between plugin instances. **Workflow data propagation is mediated exclusively by the Workflow Runtime. Plugins never exchange data directly.** |

## Decision
Workflow graphs are **directed acyclic graphs** where:
- **Node** instances explicitly declare their plugin type, configuration, and input/output contracts derived from the Plugin Contract Model.
- **Edge** connections enforce type‑safe data flow from a node’s output to another node’s input, validated against both the originating plugin's output contract and the destination plugin's input contract.
- The graph is validated for acyclicity, contract compatibility, and plugin presence.

Following validation, workflow execution is guided by the graph’s dependency structure. Runtime routing decisions (such as conditional branches or parallel paths) determine the exact execution flow, while topological ordering defines node eligibility.

This clear structural model provides static analysis guarantees and aligns with the isolation and permission rules of the platform.

This approach enables static validation, secure execution, and clear composition of plugin instances.

## Consequences
**Positive**
- Static validation of workflow graphs before execution
- Type-safe data flow between plugins with explicit contracts
- Clear separation of concerns between workflow definition and plugin implementation
- Support for conditional branching and parallel execution patterns
- Improved debugging through graph visualization and tracing

**Negative**
- Increased complexity in workflow definition syntax
- Need for graph validation tooling
- Potential performance overhead from context propagation

**Risks**
- Complex graphs may become difficult to maintain
- Type mismatches could cause runtime failures if validation is incomplete
- Versioning workflow graphs alongside plugin contracts introduces complexity

## Rationale
A DAG-based approach provides the right balance of expressiveness and analyzability for workflow composition. By defining workflows as graphs, we enable:

1. **Static Analysis**: Validate plugin compatibility, data types, and security boundaries before execution.
2. **Dependency Correctness**: Topological ordering ensures consistent dependency resolution and execution eligibility, while runtime conditions determine the actual execution path.
3. **Clear Isolation**: Each node's execution context (ADR 006) remains isolated even within a shared workflow.
4. **Extensibility**: Support for advanced patterns (parallel execution, conditionals) without breaking core semantics.

This aligns with ADR 005's emphasis on architectural boundaries and ADR 006's per-instance execution contexts.

## Validation Criteria
- All workflow graphs must be valid DAGs with no cycles.
- Node input/output types must match connected edge types.
- All referenced plugins must exist in the discovery registry (ADR 002).
- Workflows must validate that required plugin permissions can be satisfied by the execution environment.
- Workflow execution must respect the per-instance context isolation model.

## Alternatives Considered
- **Imperative Workflow Definition** – Define workflows as code sequences – Rejected for lack of static analyzability and validation.
- **Linear Pipeline Model** – Restrict workflows to sequential steps – Rejected for insufficient expressiveness.
- **Event-Driven Flows** – Define workflows as event subscriptions – Rejected for complexity in tracking execution state.

## Mandatory Rules
- Workflows must be defined as valid directed acyclic graphs.
- Each node must declare explicit input and output type contracts derived from the plugin's declared contract (ADR 005) and validated during workflow validation.
- Edges must declare compatible type mappings between node ports validated against the originating plugin's output contract.
- Workflow Context must propagate through the graph without cross-node state leakage.
- Each node executes within its own isolated execution context (ADR 006).
- Workflow graph schemas are independently versioned from plugin contracts to allow evolution without coupling.

## Allowed Changes
- Add new node types with compatible input/output contracts.
- Extend edge types for additional data flow patterns.
- Add workflow-level metadata fields.

## Forbidden Changes
- Allow cycles in workflow graphs.
- Permit implicit type conversions between incompatible node ports.
- Allow nodes to access execution contexts of other nodes in the same workflow.
