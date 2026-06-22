# 009-Governance & Validation Framework

**Status:** Accepted
**Date:** 2026-06-19
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001, 002, 003, 004, 005, 006, 007

## Context
- Since all plugins are built-time artifacts produced by development agents, validation must occur during the CI/CD pipeline before bundling into the application. No runtime artifact admission process is required. The Governance Framework provides pre-deployment validation gates that enforce architectural compliance across all ADRs before artifacts become part of the deployed platform.

## Terminology
- **Governance Framework**: Collection of validation gates that enforce the runtime architecture defined by ADR-001 through ADR-007.
- **Validation Engine**: Build‑time component that executes validation gates and produces validation reports. It is the implementation artifact of the Governance Framework and runs as part of the CI/CD pipeline.
- **Artifact**: Any component (Plugin, Manifest, Workflow Graph, Execution Context) subject to validation.
- **Deployment**: The process where validated artifacts are packaged into the application deployment.
- **Pre-Deployment**: Phase of CI/CD pipeline where validation gates are enforced.

## Decision
Adopt a Build-Time Validation Framework composed of non‑bypassable validation gates. During the CI/CD pipeline, plugins, manifests, contracts, permissions, execution contexts, and workflow graphs must strictly adhere to the architectural specifications defined in ADR-001 through ADR-007 before they may be bundled into the application. No human approvals or runtime admission gates are part of this architectural model.

## Relationship with Existing ADRs
- ADR-002 governs registration requirements validated by the Manifest Validation Gate.
- ADR-003 governs lifecycle requirements validated by the Contract Validation Gate.
- ADR-004 governs permission and isolation requirements validated by the Security Validation Gate.
- ADR-005 defines the Plugin Contract Model validated by the Contract Validation Gate.
- ADR-006 defines execution-context requirements validated by the Execution Context Validation Gate.
- ADR-007 defines workflow requirements validated by the Workflow Validation Gate.

### Validation Gates
1. **Manifest Validation Gate**
   - Manifest schema validation
   - Metadata completeness (ID, version, type)
   - Capability declaration validation

2. **Contract Validation Gate**
   - Compliance with Plugin Contract Model (ADR-005)
   - Contract version compatibility
   - Lifecycle state transition validation (ADR-003)
   - Plugin Runtime API signature compliance

3. **Security Validation Gate**
   - Declaration validation: Manifest capability-permission alignment
   - Initial permission set validation: Ensuring well-formedness and non-conflicting rights
   - Plugin package validation: Ensuring compliance with the Plugin Isolation Model (ADR-004) enforcement requirements

4. **Execution Context Validation Gate**
   - Validates declared context requirements and policies (not runtime Execution Context instances)
   - Context requirement satisfaction: Ensures declared requirements are well-formed and compatible
   - Declared resource requirements validation (CPU/memory/thread limits declared in manifest)
   - Compatibility with execution model (ADR-006): Validates declared execution context policies against the execution model specification
   - Note: Runtime Execution Context instances are provisioned and managed by the Context Manager at runtime per ADR-006

5. **Workflow Validation Gate**
   - Workflow schema validation
   - DAG validation
   - Type compatibility
   - Contract compatibility across connected nodes
   - Plugin existence and readiness checks
   - Permission satisfiability across the workflow

## Consequences
**Positive**
- Guarantees system stability by rejecting malformed artifacts early.
- Enforces architectural compliance across all ADR definitions.
- Reduces runtime errors through early detection.
- Maintains Core Engine minimalism (ADR-001).

**Negative**
- Adds computational overhead during CI/CD validation and registry generation
- Increases framework complexity to implement and maintain gate logic
- A single gate failure blocks the entire deployment

## Rationale
To prevent architectural drift in a decentralized plugin model, we need a centralized enforcement mechanism. This framework ensures the "Plugin-First" principle (ADR-001) does not compromise "Core Minimalism" (ADR-001) or security isolation (ADR-004). By centralizing validation in the Governance Framework rather than the Core Engine, architectural compliance is enforced without violating Core Minimalism.

## Validation Criteria
- Plugins with invalid manifests are rejected during build-time registration.
- Plugins failing contract checks cannot be included in the generated registry.
- Workflows with invalid DAGs or type mismatches are rejected during build-time validation.
- All validation is performed by the Governance Framework during CI/CD pipeline.
- Validation failures prevent artifact inclusion in the generated registry.
- No component can bypass a validation gate via configuration or direct injection.

## Alternatives Considered
- **Manual Governance/CABs** – Rejected for being slow and non-scalable.
- **Runtime-Only Validation** – Rejected as it allows invalid states in the registry.
- **Loose Governance** – Rejected as it undermines stability.

## Mandatory Rules
- All plugins must pass the Manifest Validation Gate before inclusion in the generated registry.
- All plugins must pass the Contract Validation Gate before inclusion in the generated registry.
- All workflow graphs must pass the Workflow Validation Gate before deployment.
- Contract compatibility must be verified before inclusion in the generated registry.
- Validation failures must strictly prevent artifact packaging.
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
