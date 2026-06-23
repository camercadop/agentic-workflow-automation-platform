# C4 Level 2 – Development Agents Component Diagram

This diagram shows the internal structure of the **Development Agents** layer and how agents collaborate via a shared artifact repository.

**Referenced ADRs:** ADR-008 (Agent-Assisted Development Model).

```mermaid
%% C4 Level-2: C2-DA – Development Agents
flowchart TD

    subgraph DA["Development Agents"]

        AA["Architect Agent
        (Generates ADRs,
        validates contracts)"]

        PGA["Plugin Generator Agent
        (Creates plugin skeletons
        adhering to contracts)"]

        TGA["Test Generator Agent
        (Creates unit/contract tests)"]

        DOC["Documentation Agent
        (Updates ADRs, API docs)"]

        RA["Review Agent
        (Optional gatekeeper,
        validates artifacts
        against standards)"]

    end

    SAR["Shared Artifact Repository
    (ADRs, plugin source,
    tests, docs)"]

    %% Relationships
    AA -->|"publishes ADRs & design decisions to"| SAR
    PGA -->|"publishes plugin source to"| SAR
    TGA -->|"publishes tests to"| SAR
    DOC -->|"publishes documentation to"| SAR
    RA -->|"reads artifacts from"| SAR

    AA -->|"provides design guidance to"| PGA
    PGA -->|"triggers test creation in"| TGA
    AA -->|"triggers documentation updates in"| DOC
    RA -->|"validates artifacts produced by"| PGA
    RA -->|"validates artifacts produced by"| TGA
    RA -->|"validates artifacts produced by"| DOC
```

## Verification

| Check | Result |
|-------|--------|
| All five agents from the description are present | ✅ |
| Shared Artifact Repository included | ✅ |
| Interactions via shared artifact repository shown | ✅ |
| Review Agent marked as optional | ✅ |
| Consistent with ADR-008 agent hierarchy and collaboration model | ✅ |
| No runtime components included (per ADR-008 separation principle) | ✅ |
| Mermaid syntax valid | ✅ |
