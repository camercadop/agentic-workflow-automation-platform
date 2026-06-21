# 001-Plugin-First Architecture

**Status:** Accepted
**Date:** 2026-06-18
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>

## Context
The platform must support complex, non-linear workflows while keeping the Core Engine minimal and decoupled from business logic. Without a defined extension model, business logic could leak into the core, violating the Core Minimalism principle and complicating governance. To achieve Plugin Isolation and Non-Linear Compliance, all functional logic must be encapsulated in independent plugins that execute in isolated Execution Contexts and interact only via mediated data flow (Workflow Context). This decision establishes the architectural boundary between platform contracts and plugin implementations.

## Decision
Adopt a Plugin First Architecture where all extensibility points (Triggers, Conditions, Transformers, Actions) are implemented as independent plugins that conform to well‑defined contracts. The Core Engine will only provide **registry loading (lookup)**, lifecycle management, and execution orchestration.

The platform distinguishes between: (a) Execution Context: the boundary of isolation per plugin instance; (b) Workflow Context: the mediated container for data flow and state propagation across nodes.

## Validation Criteria
- Verify that all workflow extensibility points are implemented as plugins
- Verify that the Core Engine contains no business logic
- Verify that the Core Engine only provides **registry loading**, lifecycle management, orchestration, and ensures Plugin Instances execute in isolated Execution Contexts
- Verify that plugins are independent components
- Verify that the architecture supports non-linear workflow execution

## Alternatives Considered
- **Monolithic Core**: Implementing workflow logic directly in the core. Rejected because it violates the Core Minimalism principle and creates a bottleneck for plugin‑driven development.
- **Service‑based Plugins**: Implementing plugins as external microservices. Rejected as it introduces excessive infrastructure complexity and latency for a prototype phase.
- **Static Registration**: Hard‑coding plugin references in the core. **Accepted for core-native plugins, but managed via a generated Static Registry for all other extensions to maintain extensibility without requiring core changes.**

## Mandatory Rules
- All workflow extensibility points must be implemented as plugins
- The Core Engine must not contain business logic
- The Core Engine must only provide **registry loading**, lifecycle management, and execution orchestration
- Plugins must be independent components
- The architecture must support non-linear workflow execution

## Allowed Changes
- Implementation details of the plugin mechanism
- **Registry loading mechanisms**
- Lifecycle management details
- Execution context details
- Contract definitions
- Governance mechanisms
- Audit mechanisms

## Forbidden Changes
- Do not add business logic to the Core Engine
- Do not bypass the plugin mechanism for workflow extensibility
- Do not make the Core Engine aware of specific plugin implementations
- Do not violate the separation between platform contracts and plugin implementations

## Risks
- **Plugin Quality**: Poorly designed plugins could break core workflows.