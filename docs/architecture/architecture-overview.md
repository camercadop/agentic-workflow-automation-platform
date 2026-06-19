# System Architecture Overview

## Core Engine Components
```
Core Engine
├── Plugin Contracts (BaseTrigger, BaseCondition, BaseTransformer, BaseAction)
├── Plugin Registry (Discovery, Loading, Lifecycle)
├── Execution Context: Workflow state container
├── Workflow Definition (Graph-based flow)
└── Workflow Executor (Non-linear orchestrator)
```

## Execution Flow
```
1. Plugin Discovery (via entry-points)
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
- **Architect-Led**: Contracts, Execution Context definitions
- **Agent-Executed**: Plugin implementations, workflow orchestration
- **Validation Gates**: Defined per ADR (not yet specified)

## Plugin Isolation Model
- Plugins inherit from Base classes
- Plugins communicate only via Execution Context
- Core Engine enforces boundaries (mechanism TBD in ADR)

## Non-Linear Flow Support
- Workflow Definition allows branching/merging
- Executor handles multiple paths without Core modification
- Context carries state between branches

## Extensibility Points
- New plugin types can be added via ADR
- Custom workflow graphs supported
- No Core modification required for business logic