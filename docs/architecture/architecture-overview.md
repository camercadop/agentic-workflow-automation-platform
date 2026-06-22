# System Architecture Overview

A concise overview of the system's architecture, including core components, execution flow, and governance models for an extensible, agent-driven workflow platform.

## Core Engine Components

The Core Engine Components are the foundational building blocks of the system architecture.
```
Core Engine
├── Plugin Contracts (BaseTrigger, BaseCondition, BaseTransformer, BaseAction)
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
   - Trigger fires -> Context created
   - Conditions evaluated -> Branching decisions
   - Transformers process -> Context updated
   - Actions executed -> Side effects
5. Governance Checkpoints (ADR-defined validation points)
```

## Governance Boundaries

This section defines the separation of responsibilities between architects and agents, outlining validation gates between workflow stages.
- **Architect-Led**: Contracts, Execution Context definitions
- **Agent-Executed**: Plugin implementations, workflow orchestration
- **Validation Gates**: Defined per ADR (not yet specified)

## Plugin Isolation Model

This section explains how plugins are encapsulated and communicate only through the Execution Context for isolation, while data propagation between plugin instances is mediated by the Workflow Context.
- Plugins inherit from Base classes
- Plugins communicate only via Execution Context
- Core Engine enforces boundaries (mechanism TBD in ADR)

## Non-Linear Flow Support

This section describes support for branching and merging workflows without requiring core modifications.
- Workflow Definition allows branching/merging
- Executor handles multiple paths without Core modification
- Context carries state between branches

## Extensibility Points

This section highlights the extension points available for adding new functionality without modifying core code.
- New plugin types can be added via ADR
- Custom workflow graphs supported
- No Core modification required for business logic
