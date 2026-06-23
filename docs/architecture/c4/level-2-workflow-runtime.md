# C4 Level 2 – Workflow Runtime Component Diagram

This diagram shows the internal building blocks of the **Workflow Runtime** container and their dependencies.

**Referenced ADRs:** ADR-006 (Execution Context), ADR-007 (Workflow Graph Specification).

```mermaid
%% C4 Level-2: C2-WR – Workflow Runtime
flowchart TD

    subgraph WR["Workflow Runtime"]

        NE["Node Executor
        (Executes plugin instances
        within an Execution Context)"]

        RE["Routing Engine
        (Evaluates edges,
        handles branching/merging,
        respects DAG)"]

        SD["Scheduler / Dispatcher
        (Queues ready nodes,
        manages concurrency)"]

        EH["Error Handler
        (Captures failures,
        triggers compensation
        or escalation)"]

    end

    CM["Context Manager
    (Context Lifecycle,
    Plugin Runtime API)"]

    WD["Workflow Definition
    (Graph)"]

    %% Relationships
    NE <-->|"Requests Execution Context from"| CM
    RE <-->|"Interprets graph from"| WD
    SD <-->|"Dispatches ready nodes to"| NE
    EH <-->|"Captures failures from"| NE
    EH <-->|"Reroutes or halts via"| RE
```
