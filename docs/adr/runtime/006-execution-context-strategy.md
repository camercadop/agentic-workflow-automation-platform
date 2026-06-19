# ADR 006: Execution Context Strategy

**Status:** Proposed
**Date:** 2026-07-01
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 002, 003, 004, 005

## Context
The platform must manage how plugins execute tasks within a standardized, secure, and scalable environment. Without a defined strategy, plugins could share or misuse execution contexts (e.g., memory, threading, or isolation), leading to:

- Resource contention (e.g., memory leaks, thread starvation)
- Security vulnerabilities (e.g., unchecked access to shared resources)
- Inconsistent behavior (e.g., plugins interfering with each other’s state)
- Debugging difficulties (e.g., opaque execution flows)

**Constraints:**
- Mandatory adherence to the Plugin Contract Model (ADR 005), which defines security boundaries (ADR 004) and lifecycle rules (ADR 003). The strategy must align with these while enabling flexibility for diverse plugin workloads.

## Terminology
| Term | Definition |
|------|------------|
| **Execution Context** | The isolated runtime environment in which a plugin invocation executes, providing memory, threading, and sandboxed boundaries for a single plugin instance’s active execution. |
| **Context Service** | The platform component responsible for creating, provisioning, and destroying execution contexts, operating under the Isolation Service’s policies (ADR-004). |
| **Plugin Instance** | A single occurrence of a plugin executing within a workflow, uniquely identified and isolated for its execution duration. |

**Execution Context is a logical isolation boundary. The underlying implementation may evolve (e.g., process, thread, container, sandbox) without affecting the contract model.**

## Decision
Adopt a **per-plugin instance execution context strategy** where:
- Each plugin instance (e.g., individual Trigger, Condition, Transformer, Action in a workflow) receives its own isolated execution context.
- Contexts are provisioned immediately before plugin instance execution and destroyed immediately after execution completes.
- A **platform metadata service** (not a shared layer) exposes controlled, read-only access to approved platform metadata through the Runtime API.
- Plugins can request additional context resources (threads, IPC channels) via the Runtime API, which the Core Engine forwards to the Isolation Service for evaluation and allocation.

This ensures that even within a single workflow, plugins like Trigger, Condition, and Action run in entirely separate contexts, preventing interference.

## Consequences
**Positive**
- Reduced interference: Plugins cannot corrupt each other’s state or consume excessive shared resources.
- Security-enforced boundaries: Resource access is validated against the Security Contract.
- Predictable performance: Context isolation simplifies scaling and debugging.
- Simplified recovery: Execution contexts can be cleaned up deterministically by the Context Service.

**Negative**
- Increased overhead: Per-context setup/teardown may impact startup time or memory usage.
- Complexity in resource management: Requires careful policy evaluation by the Isolation Service.
- Protocol negotiation overhead: Requesting additional resources adds latency.

**Risks**
- Context drift: If the Isolation Service mismanages context provisioning, plugins might violate isolation.
- Overhead for lightweight plugins: Heavy setup costs for minimal plugins.
- Dependency on Isolation Service: Failure in isolation logic could lead to unisolated execution.

## Rationale
The per-plugin instance context strategy balances isolation and interoperability, aligning with ADR 005’s architectural boundaries. It enforces security (via ADR 004’s sandboxing) while respecting plugin-specific needs. By tying context management to execution phases (Active), we ensure deterministic cleanup without polluting the plugin lifecycle (ADR 003) with execution-specific state. The Context Service owns context lifecycle; lifecycle hooks (optional per ADR 003) may observe but not control it.

This design explicitly addresses workflow execution: each plugin instance in a workflow (Trigger, Condition, Transformer, Action) receives its own execution context immediately before execution begins. Contexts are not shared between plugins, nor are they reused across workflow executions. This avoids the ambiguity of "per-plugin" referring to type, instance, or workflow-level scope.

## Validation Criteria
- Each plugin instance in a workflow runs in an isolated context with no shared state.
- Memory/thread usage per context is bounded and traceable.
- Security audits confirm adherence to the Security Contract during execution.
- Contexts are correctly provisioned and destroyed for each plugin instance during execution.
- Stress tests validate performance under high plugin concurrency within workflows.

## Alternatives Considered
- **Shared Global Context** – Fails to isolate plugins, violating ADR 004 security boundaries – Rejected.
- **Per-Task Contexts** – Overcomplicates lifecycle management (ADR 003) and blurs plugin boundaries – Rejected.
- **Plugin-Defined Context** – Risk of inconsistent security practices; violates Contract Model compliance – Rejected.

## Mandatory Rules
- Execution contexts must be provisioned immediately before plugin instance execution and destroyed immediately after execution completes.
- Plugins may only access platform metadata via negotiated protocols defined in the Runtime API Contract (ADR 004).
- Changes that affect plugin-visible execution context behavior must follow the Plugin Contract Model versioning rules (ADR 005).

## Allowed Changes
- Add lightweight context features (e.g., read-only caches) with minor version bumps.
- Refine context isolation mechanisms (e.g., adjusting sandbox granularity) without altering core guarantees.

## Forbidden Changes
- Allow plugins to share execution memory spaces or threads outside the isolation model.
- Bypass Core Engine context validation logic.
- Remove lifecycle cleanup requirements.