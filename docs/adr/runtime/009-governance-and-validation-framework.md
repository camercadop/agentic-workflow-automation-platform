# 009-Governance & Validation Framework

**Status:** Proposed
**Date:** 2026-06-19
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001, 002, 003, 004, 005, 006, 007

## Context
The platform's extensibility model, driven by a Plugin‑First Architecture (ADR-001), introduces various moving parts: plugin manifests, lifecycle states, capability declarations, contract implementations, execution contexts, and workflow graphs. According to ADR-004, the Core Engine must remain isolated from security-sensitive logic through the Isolation Service. A centralized technical governance layer is required to enforce architectural compliance across all extensible components through automated validation gates, preventing incompatible, insecure, or malformed artifacts from entering the system.

## Terminology
- **Governance Framework**: Collection of all validation gates that enforce ADR-001 through ADR-008.
- **Validation Service**: Platform component responsible for executing validation gates and producing admission decisions. This component is part of the Governance Framework but operates as a dedicated boundaryless execution unit. The Governance Framework defines the validation rules, while the Validation Service is responsible for automatically verifying artifacts against those rules.
- **Artifact**: Any component (Plugin, Manifest, Workflow Graph, Execution Context) subject to validation.
- **Admission**: Successful passage of an artifact through required validation gates.
- **Core Engine**: The platform's core component responsible for discovery, lifecycle management, and orchestration (ADR-001).
- **Validation Service**: Platform component responsible for executing validation gates until admission decisions.

## Decision
Adopt an automated **Governance & Validation Framework** composed of non‑bypassable validation gates. The platform (not the Core Engine) remains the sole authority on what constitutes a valid component through this framework, which enforces that plugins, manifests, contracts, permissions, execution contexts, and workflow graphs strictly adhere to the architectural specifications defined in ADR-001 through ADR-008 before they may be registered, activated, or executed. No human approvals are part of this architectural model.

## Relationship with Existing ADRs
- ADR-002 governs discovery requirements validated by the Discovery Validation Gate.
- ADR-003 governs lifecycle requirements validated by the Contract Validation Gate.
- ADR-004 governs permission and isolation requirements validated by the Security Validation Gate.
- ADR-005 defines the Plugin Contract Model validated by the Contract Validation Gate.
- ADR-006 defines execution-context requirements validated by the Execution Context Validation Gate.
- ADR-007 defines workflow requirements validated by the Workflow Validation Gate.

### Validation Gates
1. **Discovery Validation Gate**
   - Manifest schema validation
   - Metadata completeness (ID, version, type)
   - Capability declaration validation

2. **Contract Validation Gate**
   - Compliance with Plugin Contract Model (ADR-005)
   - Contract version compatibility
   - Lifecycle state transition validation (ADR-003)
   - Runtime API signature compliance

3. **Security Validation Gate**
   - Declaration validation: Manifest capability-permisson alignment
   - Initial permission set validation: Ensuring well-formedness and non-conflicting rights
   - Archive validation: Ensuring compliance with the Plugin Isolation Model (ADR-004) enforcement requirements

4. **Execution Context Validation Gate**
   - Context requirement satisfaction
   - Resource constraints verification
   - Compatibility with execution model (ADR-006)

  5. **Workflow Validation Gate**
     - DAG validation
     - Type compatibility
     - Contract compatibility across connected nodes
     - Plugin existence and readiness checks
     - Permission satisfiability across the workflow

6. **Execution Admission Gate**
    - Revalidation of execution prerequisites
    - Context availability verification
    - Permission availability verification
    - Plugin activation status verification

## Consequences
**Positive**
- Guarantees system stability by rejecting malformed artifacts early.
- Enforces architectural compliance across all ADR definitions.
- Reduces runtime errors through early detection.
- Maintains Core Engine minimalism (ADR-001).

**Negative**
- Adds computational overhead during registration and workflow initialization.
- Increases framework complexity to implement and maintain gate logic.
- A single gate failure blocks the entire artifact.

## Rationale
To prevent architectural drift in a decentralized plugin model, we need a centralized enforcement mechanism. This framework ensures the "Plugin-First" principle (ADR-001) does not compromise "Core Minimalism" (ADR-001) or security isolation (ADR-004). By centralizing validation in the Governance Framework rather than the Core Engine, we complete the isolation chain initiated in ADR-004.

## Validation Criteria
- Plugins with invalid manifests are rejected during Discovery.
- Plugins failing contract checks cannot be activated.
- Workflows with invalid DAGs or type mismatches are rejected before execution.
- All validation is performed by the Governance Framework, not the Core Engine.
- Validation failures are logged and prevent subsequent lifecycle stages.
- No component can bypass a validation gate via configuration or direct injection.

## Alternatives Considered
- **Manual Governance/CABs** – Rejected for being slow and non-scalable.
- **Runtime-Only Validation** – Rejected as it allows invalid states in the registry.
- **Loose Governance** – Rejected as it undermines stability.

## Mandatory Rules
- All plugins must pass the Discovery Validation Gate before registration.
- All plugins must pass the Contract Validation Gate before activation.
- All workflow graphs must pass the Workflow Validation Gate before execution.
- Contract compatibility must be verified before any plugin activation.
- Validation failures must strictly prevent the associated lifecycle stage.
- Validation gates cannot be bypassed under any circumstances.

## Allowed Changes
- Updates to validation logic to support new plugin types or capabilities.
- Refinement of validation schemas (e.g., manifest version updates).
- Performance optimizations of gate implementations.

## Forbidden Changes
- Registering plugins that fail any validation gate.
- Executing workflows that fail graph or type validation.
- Activating plugins with unsatisfied or unauthorized permissions.
- Bypassing validation gates.
- Moving validation logic from the Governance Framework to the Core Engine.
- Disabling mandatory validation gates without an approved revision of this ADR.
