# C4 Level 2 – Isolation Service Component Diagram

This diagram shows the internal building blocks of the **Isolation Service** container and their relationships.

**Referenced ADRs:** ADR-004 (Plugin Isolation Model), ADR-009 (Build-time Validation – declares permissions enforced at runtime by this service).

```mermaid
%% C4 Level-2: C2-IS – Isolation Service
flowchart TD

    subgraph IS["Isolation Service"]

        PE["Permission Evaluator
        (Checks plugin manifest
        against granted capabilities)"]

        RM["Resource Mediator
        (Enforces CPU, memory,
        I/O, network quotas)"]

        SE["Sandbox Enforcer
        (Launches plugin in
        container/process with
        seccomp, namespaces)"]

        AL["Audit Logger
        (Records security-relevant
        events)"]

    end

    CM["Context Manager"]
    ES["External Systems"]
    GF["Governance Framework"]

    %% Relationships
    CM -->|"Delegates authorization to"| PE
    CM -->|"Delegates sandbox setup to"| SE
    RM -->|"Mediates resource requests to"| ES
    AL -->|"Emits audit events to"| GF
    PE -->|"Informs"| SE
    RM -->|"Provides resource limits to"| SE
    RM -->|"Logs violations via"| AL
```
