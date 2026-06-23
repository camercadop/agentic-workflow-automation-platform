# C4 Level 2 – Core Engine Component Diagram

This diagram shows the internal building blocks of the **Core Engine** container and their dependencies.

**Referenced ADRs:** ADR-001 (Core Minimalism), ADR-002 (Plugin Registration), ADR-005 (Plugin Contract Model).

**External dependencies shown:** Context Manager (ADR-006), Workflow Runtime (ADR-007).

```mermaid
%% C4 Level-2: C2-CE – Core Engine
flowchart TD

    subgraph CE["Core Engine"]

        PC["Plugin Contracts
        (Trigger, Condition,
        Transformer, Action)"]

        PR["Plugin Registry
        (Static Generation,
        Runtime Loading,
        Lifecycle)"]

        WD["Workflow Definition
        (Graph-Based Flow Model)"]

        WE["Workflow Executor
        (Non-Linear Orchestrator)"]

    end

    CM["Context Manager
    (Owns Execution Context
    Lifecycle – ADR-006)"]

    WR["Workflow Runtime
    (Node Executor,
    Routing Engine,
    Owns Workflow Context – ADR-007)"]

    %% Dependencies
    PR -->|Validates against| PC
    WE -->|Resolves plugins from| PR
    WE -->|Interprets| WD
    WE -->|Delegates node execution to| WR
    WR -->|Requests Execution Context from| CM
```
