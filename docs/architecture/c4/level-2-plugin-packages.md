# C4 Level 2 – Plugin Packages Component Diagram

This diagram shows the internal structure of a validated **Plugin Package** artifact stored in the Plugin Registry.

**Referenced ADRs:** ADR-002 (Plugin Registration Model), ADR-005 (Plugin Contract Model).

```mermaid
%% C4 Level-2: C2-PP – Plugin Packages
flowchart TD

    subgraph PP["Plugin Package"]

        PM["Plugin Manifest
        (Metadata, contract version,
        dependencies)"]

        PCI["Plugin Contract Implementation
        (Class implementing one of
        Trigger, Condition,
        Transformer, Action)"]

        PR["Plugin Resources
        (Config files,
        static assets)"]

        TA["Test Artifacts
        (Unit/contract tests generated
        by Test Generator Agent)"]

    end

    PC["Plugin Contract
    (Core Engine)"]

    %% Dependencies
    PCI -->|"Implements"| PC
    PM -->|"Declares contract version for"| PCI
    PCI -->|"Optionally loads"| PR
    TA -->|"Validates"| PCI
```
