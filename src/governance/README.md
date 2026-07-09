# Governance

Build-time validation framework (ADR-009) and pipeline guards for the agentic development process.

## Modules

| Module | Purpose |
|--------|---------|
| `gates.py` | Five validation gates: Manifest, Contract, Security, Context, Workflow |
| `engine.py` | `ValidationEngine` — runs gates and produces `ValidationReport` |
| `pipeline_guards.py` | Post-step guards that prevent hallucinated implementations from advancing |
| `pipeline_errors.py` | `PipelineGateError` raised when a guard fails |

## Validation Gates

1. **ManifestValidationGate** — Validates plugin manifest completeness
2. **ContractValidationGate** — Ensures plugins conform to their declared contracts
3. **SecurityValidationGate** — Checks for security policy violations
4. **ExecutionContextValidationGate** — Verifies isolation boundaries
5. **WorkflowValidationGate** — Validates DAG structure and edge compatibility

## Pipeline Guards

```mermaid
flowchart LR
    Dev[Developer] -->|artifacts| G1{Post-Developer Guards}
    G1 -->|pass| Test[Tester]
    Test -->|results| G2{Post-Tester Guards}
    G2 -->|pass| G3{Pre-Reviewer Guards}
    G3 -->|pass| Rev[Reviewer]
    G1 -->|fail| X1[❌ Block + Resume]
    G2 -->|fail| X2[❌ Block + Resume]
    G3 -->|fail| X3[❌ Block + Resume]
```

- **Post-Developer**: artifact existence, path validation, syntax check
- **Post-Tester**: runs `pytest`, measures coverage
- **Pre-Reviewer**: report-to-git consistency

## Key ADR

- **ADR-009** — Build-Time Governance
