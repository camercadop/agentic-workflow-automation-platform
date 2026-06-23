# C4 Level 2 – Governance Layer Component Diagram

This diagram shows the internal building blocks of the **Governance Layer** (build‑time validation gates) and their relationships to plugin artifacts.

**Referenced ADRs:** ADR-009 (Governance & Validation Framework).

```mermaid
%% C4 Level-2: C2-GV – Governance Layer
flowchart TD

    subgraph GV["Governance Layer (Build-Time)"]

        VE["Validation Engine
        (Orchestrates gates,
        aggregates reports)"]

        MG["Manifest Gate
        (Validates plugin manifest schema,
        metadata completeness,
        capability declarations)"]

        CG["Contract Gate
        (Verifies plugin implements
        correct contract, lifecycle
        transitions, API signatures)"]

        SG["Security Gate
        (Runs static analysis,
        permission validation,
        dependency checks)"]

        XG["Context Gate
        (Ensures proper declared
        context requirements,
        resource policies)"]

        WG["Workflow Gate
        (Validates DAG structure,
        type compatibility,
        contract compatibility)"]

    end

    PA["Plugin Artifacts
    (Manifests, Source,
    Packages)"]

    WA["Workflow Definitions
    (DAG Graphs)"]

    PF["Pass/Fail Reports"]

    RB["Registry Builder"]

    %% Artifacts consumed by Validation Engine
    PA -->|"consumed by"| VE
    WA -->|"consumed by"| VE

    %% Validation Engine invokes gates
    VE -->|"invokes"| MG
    VE -->|"invokes"| CG
    VE -->|"invokes"| SG
    VE -->|"invokes"| XG
    VE -->|"invokes"| WG

    %% Gates emit results
    MG -->|"emits"| PF
    CG -->|"emits"| PF
    SG -->|"emits"| PF
    XG -->|"emits"| PF
    WG -->|"emits"| PF

    %% Registry Builder uses reports and artifacts
    PF -->|"informs"| RB
    PA -->|"packaged by"| RB
```

## Component Summary

| Component | Responsibility | ADR Reference |
|-----------|---------------|---------------|
| Validation Engine | Orchestrates all gates, distributes artifacts, aggregates pass/fail reports | ADR-009 |
| Manifest Gate | Schema validation, metadata completeness, capability declaration validation | ADR-002, ADR-009 |
| Contract Gate | Plugin Contract Model compliance, lifecycle state transitions, API signature verification | ADR-003, ADR-005, ADR-009 |
| Security Gate | Permission-capability alignment, package isolation compliance, static analysis | ADR-004, ADR-009 |
| Context Gate | Declared context requirement validation, resource policy well-formedness, execution model compatibility | ADR-006, ADR-009 |
| Workflow Gate | DAG validation, type/contract compatibility across nodes, plugin existence checks | ADR-007, ADR-009 |

## Notes

- The Governance Layer operates **exclusively at build time** (CI/CD pipeline) and is **not** deployed as a runtime service (per ADR-009).
- A failure in any gate blocks artifact inclusion in the generated Static Registry.
- No gate can be bypassed via configuration or direct injection.
