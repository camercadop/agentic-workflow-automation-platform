# C4 Model Level 1 - Container Diagram (Flowchart)

```mermaid
flowchart TD

    Dev([Developer])
    Arch([Architect])

    subgraph PFA["Plugin-First Workflow Automation Platform"]

        CE["Core Engine
        (Registry Loader,
        Lifecycle Manager)"]

        WR["Workflow Runtime
        (Node Executor,
        Routing Engine)"]

        PP["Plugin Packages
        (Validated Plugin Artifacts)"]

        CM["Context Manager
        (Context Lifecycle,
        Plugin Runtime API)"]

        PS["Platform API
        (External Workflow
        Submission, Control)"]

        IS["Isolation Service
        (Permission Evaluation,
        Resource Mediation)"]

    end

    EXT["External Systems
    (APIs, Databases, Queues, etc.)"]

    Dev -->|Develops plugins & workflows| PFA
    Arch -->|Defines contracts & governance| PFA

    CE -->|Loads registry from| PP
    CE -->|Orchestrates workflows via| WR

    WR -->|Requests Execution Context from| CM
    CM -->|Delegates authorization to| IS
    IS -->|Mediates access to| EXT
```
