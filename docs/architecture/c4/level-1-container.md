# C4 Model Level 1 - Container Diagram (Flowchart)

```mermaid
flowchart TD
    %% Containers
    core["Core Engine"]
    pkgs["Plugin Packages"]
    wfRuntime["Workflow Runtime\n(Node Executor, Routing Engine, Context Manager)"]
    runtimeApi["Runtime API\n(Context, Logging, Metrics, Secrets)"]
    isoService["Isolation Service\n(Permission Evaluation, Resource Mediation)"]
    ext["Third-party APIs, databases"]

    %% Relationships with labels
    core -->|loads registry| pkgs
    pkgs -->|provides registered plugin types to| wfRuntime
    wfRuntime -->|provides services to| runtimeApi
    runtimeApi -->|validates via| isoService
    isoService -->|mediates| ext
```
