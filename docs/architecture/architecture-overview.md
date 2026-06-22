# System Architecture Overview

A concise overview of the system's architecture, including core components, execution flow, and governance models for an extensible, agent-driven workflow platform.

## Core Engine Components

The Core Engine Components are the foundational building blocks of the system architecture.
```
Core Engine
├── Plugin Contracts (Trigger, Condition, Transformer, Action interfaces)
├── Plugin Registry (Static Generation, Runtime Loading, Lifecycle)
├── Execution Context: Per-plugin-instance isolation boundary
├── Workflow Context: Mediated data‑propagation container for the workflow runtime
├── Workflow Definition (Graph-based flow)
└── Workflow Executor (Non-linear orchestrator)
```

## Execution Flow

This section outlines the execution flow from build-time registration to governance checkpoints.

```
1. Build-time Registration & Static Registry Generation
2. Plugin Registration (Registry)
3. Workflow Definition (Graph definition)
4. Workflow Execution:
   - Trigger fires -> Plugin Instance executes within Execution Context (isolation) and accesses Workflow Context
   - Conditions evaluated -> Plugin Instance executes within Execution Context (isolation) and accesses Workflow Context (branching decisions)
   - Transformers process -> Plugin Instance executes within Execution Context (isolation) and accesses Workflow Context (data updates)
   - Actions executed -> Plugin Instance executes within Execution Context (isolation) and accesses Workflow Context (side effects)
   - Execution Context destroyed after each plugin instance execution
5. Governance Checkpoints (ADR-defined validation points)
```

## Governance Boundaries (Design-time)

This section defines the separation of responsibilities between architects and development agents during the design phase.
- **Architect-Led**: Contracts, Execution Context definitions
- **Development Agent-Assisted**: plugin implementation generation and workflow design artifacts
- **Validation Gates**: Defined in ADR-009 (Governance and Validation Framework)

## Plugin Isolation Model

Plugins execute within isolated Execution Contexts; data propagation between plugin instances is mediated only by the Workflow Context.
- Plugins inherit from Base classes
- Plugins use Execution Contexts for isolation and Workflow Context for mediated data propagation.
- Core Engine coordinates orchestration; Context Manager routes access requests; Isolation Service is sole authorization authority.

## Non-Linear Flow Support

This section describes support for branching and merging workflows without requiring core modifications.
- Workflow Definition allows branching/merging
- Executor handles multiple paths without Core modification
- Workflow Context carries state between branches

## Extensibility Points

This section highlights the extension points available for adding new functionality without modifying core code.
- New plugin types can be added via ADR
- Custom workflow graphs supported
- No Core modification required for business logic
