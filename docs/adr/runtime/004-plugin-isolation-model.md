# ADR 004 - Plugin Isolation Model

**Status:** Accepted
**Date:** 2026-06-22
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001, 002, 003

## Context
Plugins in our system must not interfere with each other or the Core Engine. Without explicit isolation, plugins could:
1. Access shared resources (e.g., files, memory) directly, leading to race conditions or resource exhaustion.
2. Expose internal APIs to other plugins, violating the Plugin First principle of indirect interaction.
3. Corrupt Core Engine state by overriding global configuration or internal logic.
4. Contain malicious code that exploits interactions with other plugins.

Constraints:
- Maintain backward compatibility with existing plugins.
- Ensure the Core Engine remains agnostic to plugin implementations.
- Avoid introducing excessive runtime overhead.

Affected Architectural Goals:
- Plugin Isolation (ADR 001 requirement for independent components).
- Core Minimalism (preventing plugins from bloating the Core Engine).

## Terminology
| Term | Definition |
|------|------------|
| **Capability** | A functional feature a plugin *provides* (e.g., "transform-data", "send-email"). Declared in the manifest during build-time registration (ADR 002). |
| **Permission** | A right to access a specific **resource** (e.g., file `/tmp/data`, env `API_KEY`, network `api.example.com`). Granted at runtime by the Isolation Service. |

### Plugin Runtime API Ownership (Plugin-Facing Interface)
The Context Manager is the authorization and resource-access gateway of the Plugin Runtime API. All resource requests are channeled through it to ensure isolation compliance; the Context Manager delegates authorization decisions to the Isolation Service. Plugins interact only with the Platform through the Plugin Runtime API.

## Decision
Adopt a sandboxed architecture where plugins:
1. Run in isolated execution contexts (e.g., separate processes or isolated VMs).
2. Interact with the system through two distinct interfaces:
   - **Lifecycle Interface**: Used for plugin registration outcomes and lifecycle state transitions (ADRs 002/003).
   - **Plugin Runtime API Interface**: Used to access platform services (execution context, metadata, logging, metrics, configuration, event bus) and to submit resource access requests. The Context Manager routes resource access requests to the Isolation Service for policy evaluation.
3. Resource access requests submitted through the Plugin Runtime API Interface are validated by the Isolation Service against the active policy model.
4. Cannot reference or modify other plugins’ code/data directly.

### Permission Validation Boundaries
Permission validation occurs at both build-time and runtime with distinct responsibilities:
- **Build-time Validation** (Governance Framework - ADR-009):
  - Security Validation Gate validates manifest capability-permission alignment and initial permission set well-formedness
  - Workflow Validation Gate verifies permission satisfiability across the workflow graph
  - These gates ensure structural correctness and static policy compliance
- **Runtime Validation** (Isolation Service - this ADR):
  - Binds context tokens and verifies dynamic runtime parameters (e.g., specific file paths, API tokens, session lifetimes)
  - Evaluates resource access requests against the active policy model in the current execution context
  - Enforces dynamic, context-aware access decisions that cannot be determined statically

## Consequences
**Positive**
- Prevents plugins from crashing each other or the Core Engine.
- Enhances security by limiting plugin-to-plugin/data access.
- Simplifies debugging by isolating plugin failure modes.

**Negative**
- Potential performance overhead from running plugins in isolated contexts.
- Increased complexity in managing inter-plugin communication (requires Core-mediated APIs).

**Risks**
- Plugins may attempt to bypass isolation via API misuse or exploit sandbox gaps.
- Incompatibility with legacy plugins expecting unrestricted resource access.

## Validation Criteria
- Test 1: A plugin with capability `read-files` cannot read `/etc/passwd` unless explicitly granted `file:/etc/passwd` permission.
- Test 2: Plugins cannot modify Core Engine’s internal state (e.g., configuration, hooks).
- Test 3: Core Engine rejects any plugin attempt to reference another plugin’s class/data.
- Test 4: Plugins interact only with the Platform public API contract, comprising the Lifecycle Interface (registration and lifecycle transitions) and the Plugin Runtime API Interface (platform services and resource access through the Context Manager and Isolation Service).

## Clarification
Plugins do not directly call the Isolation Service.
Resource access requests are submitted through the Plugin Runtime API and routed by the Context Manager to the Isolation Service for policy evaluation.
The Core Engine remains responsible for orchestration and lifecycle coordination.

## Alternatives Considered
- Peer-to-peer plugin communication: Rejected because it violates isolation and introduces shared state risks.
- Shared process with strict APIs: Rejected due to potential security gaps in shared memory.
- Single shared library: Rejected because it violates Plugin First and Core Minimalism.

## Mandatory Rules
- **Lifecycle Interface**: Plugins may implement lifecycle hooks for state transitions (Registered, Activated, Active, Deactivated, Cleaned Up).
- **Plugin Runtime API Interface**: Plugins call platform services and request resource access through this interface; **resource access calls are evaluated for permissions** by the Isolation Service.
- **Permissions**: The Isolation Service validates resource access requests through the Plugin Runtime API against policy.
- **Isolation**: The Core Engine never directly evaluates permissions—only the Isolation Service does.
- **Authorization Authority**: The Isolation Service is the sole component allowed to grant or deny permissions.

## Allowed Changes
- Adjust sandboxing implementation (e.g., process vs. VM isolation).
- Refine Isolation Service APIs to better enforce permissions.
- Extend Plugin Runtime API with new platform services (e.g., caching, pub/sub).

## Forbidden Changes
- Allow plugins to bypass the Plugin Runtime API for resource access.
- Allow the Core Engine to perform permission evaluation (violates ADR-001 Minimalism).
- Allow plugins to directly reference other plugins’ memory or classes.

## Rationale
The sandboxed model ensures plugins are fully decoupled from each other and the Core Engine, aligning with the Plugin First Architecture. By restricting interaction to well-defined APIs and enforcing permissions via the Isolation Service, we mitigate security and stability risks while maintaining Core Minimalism.
