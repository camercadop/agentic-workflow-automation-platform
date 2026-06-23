# C4 Level 2 – Context Manager Component Diagram

This diagram shows the internal building blocks of the **Context Manager** container and their relationships.

**Referenced ADRs:** ADR-004 (Plugin Isolation Model), ADR-006 (Execution Context), ADR-007 (Workflow Context).

```mermaid
%% C4 Level-2: C2-CM – Context Manager
flowchart TD

    subgraph CM["Context Manager"]

        ECF["Execution Context Factory
        (Creates isolated context
        per plugin instance)"]

        WCS["Workflow Context Store
        (Holds current version of
        workflow data, provides
        read/write API)"]

        CIE["Context Isolation Enforcer
        (Ensures plugins only access
        their own Execution Context)"]

        CP["Context Persister
        (Optional snapshotting for
        long-running workflows)"]

    end

    EC["Execution Context"]
    WC["Workflow Context"]

    IS["Isolation Service
    (Permission Evaluation,
    Resource Mediation – ADR-004)"]

    %% Relationships
    ECF -->|"delegates authorization to"| IS
    IS -->|"approves provisioning"| ECF
    ECF -->|"creates"| EC
    WCS <-->|"reads/writes"| WC
    CIE -->|"wraps"| EC
    CP <-->|"snapshots"| WC
```
