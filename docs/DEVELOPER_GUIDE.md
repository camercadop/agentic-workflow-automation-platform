# Developer Guide — Core Engine

> **Audience:** Human developers and AI agents working with or extending the Core Engine.
> This document explains what the system does and how to integrate with it.

---

## Module Map

| Module | Responsibility | ADR |
|--------|----------------|-----|
| `manifest.py` | Plugin metadata model (name, type, ports, permissions) | ADR-002, ADR-005 |
| `contracts.py` | Abstract plugin interfaces (`TriggerPlugin`, `ConditionPlugin`, `TransformerPlugin`, `ActionPlugin`) | ADR-003, ADR-005 |
| `registration.py` | Decorator-based plugin collection for build-time registry generation | ADR-002 |
| `registry.py` | Static plugin registry and lifecycle state machine | ADR-002, ADR-003 |
| `context.py` | Per-execution isolation boundary and context provisioning | ADR-004, ADR-006 |
| `workflow.py` | DAG definition model with built-in validation | ADR-007 |
| `executor.py` | Workflow runtime: topological ordering, context provisioning, plugin dispatch | ADR-006, ADR-007 |

---

## How to Use the Core Classes

### 1. Defining a Plugin

Every plugin must subclass one of the four contract types and declare a manifest:

```python
from typing import Any
from src.core.contracts import ActionPlugin
from src.core.manifest import PluginManifest, PluginType, PortSchema


class EmailSender(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="email-sender",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            permissions=["network:smtp.example.com"],
            inputs=[PortSchema(name="payload", data_type="dict")],
            outputs=[PortSchema(name="result", data_type="dict")],
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"status": "sent"}
```

Plugin types and their required methods:

| Base Class | Method to Implement | Returns |
|---|---|---|
| `TriggerPlugin` | `check()` | `dict[str, Any]` |
| `ConditionPlugin` | `evaluate(data)` | `bool` |
| `TransformerPlugin` | `transform(data)` | `dict[str, Any]` |
| `ActionPlugin` | `execute(data)` | `dict[str, Any]` |

Lifecycle hooks are optional — override only when needed:
- `on_activate()` — called on Registered → Activated
- `on_deactivate()` — called on Active → Deactivated
- `on_cleanup()` — called on Deactivated → CleanedUp

### 2. Registering Plugins and Managing Lifecycle

Plugins are declared using the `@register_plugin` decorator and collected at build time (no runtime discovery):

```python
from src.core.registration import register_plugin
from src.core.contracts import ActionPlugin


@register_plugin
class EmailSender(ActionPlugin):
    ...
```

The Registry Builder imports plugin modules, calls `get_collected_plugins()`, validates each against the governance gates, and produces the static registry artifact.

At startup, the registry enforces a strict sequential lifecycle:

```
Registered → Activated → Active → Deactivated → CleanedUp
```

```python
from src.core.registry import PluginRegistry

registry = PluginRegistry()
registry.register(EmailSender())

# Transition through lifecycle before execution
registry.activate("email-sender")      # Registered → Activated
registry.mark_active("email-sender")   # Activated → Active

# After use
registry.deactivate("email-sender")    # Active → Deactivated
registry.cleanup("email-sender")       # Deactivated → CleanedUp
```

Invalid transitions raise `LifecycleError`. Duplicate registrations raise `ValueError`.

### 3. Execution Contexts

The `ContextManager` provisions isolated execution boundaries per plugin instance. Authorization is delegated to an `IsolationService`:

```python
from src.core.context import ContextManager

cm = ContextManager()  # Uses DefaultIsolationService (permits all)
ctx = cm.provision(plugin.manifest)

# ... execute the plugin ...

cm.destroy(ctx.context_id)  # Always destroy after execution
```

To enforce custom authorization policies, implement the `IsolationService` protocol:

```python
from src.core.context import IsolationService
from src.core.manifest import PluginManifest


class StrictIsolation:
    def authorize(self, manifest: PluginManifest, resources: list[str]) -> bool:
        return all(r in ALLOWED_RESOURCES for r in resources)

cm = ContextManager(isolation_service=StrictIsolation())
```

### 4. Defining Workflows

Workflows are DAGs validated at construction time (acyclicity + referential integrity):

```python
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode

wf = WorkflowDefinition(
    name="email-alert",
    nodes=[
        WorkflowNode(node_id="trigger", plugin_name="timer-check"),
        WorkflowNode(node_id="filter", plugin_name="priority-filter"),
        WorkflowNode(node_id="send", plugin_name="email-sender"),
    ],
    edges=[
        WorkflowEdge(
            source_node="trigger",
            source_port="payload",
            target_node="filter",
            target_port="data",
        ),
        WorkflowEdge(
            source_node="filter",
            source_port="output",
            target_node="send",
            target_port="payload",
        ),
    ],
)
```

Construction raises `ValidationError` if:
- Any edge references a non-existent node
- The graph contains a cycle
- Required fields are missing or empty

### 5. Executing Workflows

The `WorkflowExecutor` ties everything together — it resolves plugins from the registry, provisions contexts, and dispatches execution:

```python
from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry

registry = PluginRegistry()
# ... register and activate plugins ...

executor = WorkflowExecutor(registry, ContextManager())
results = executor.execute(wf, initial_data={"key": "value"})
# results: {"trigger": {...}, "filter": {...}, "send": {...}}
```

Plugins must be in `ACTIVE` state. The executor raises `WorkflowExecutionError` for inactive plugins and `KeyError` for unregistered ones.

---

## Architecture Constraints

- **ADRs are authoritative.** If code conflicts with an ADR, the ADR wins. Update the code.
- **Core Engine is minimal.** It handles registry, lifecycle, context, and orchestration only. No business logic.
- **Plugin isolation is mandatory.** Plugins never share execution contexts, access each other's state, or reference Core internals.
- **Contexts are ephemeral.** Always provision before execution and destroy in a `finally` block after execution.
- **Lifecycle transitions are sequential.** No skipping states. The registry enforces this.
