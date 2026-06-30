# Coding Conventions

> **Audience:** AI agents (Developer, Tester, Reviewer) and human contributors.
> This document is the authoritative reference for coding patterns, naming, structure, and style.

---

## Language & Runtime

- **Python 3.12+** — use modern syntax (`type` aliases, `X | Y` unions, `StrEnum`)
- **No deprecated `typing` generics** — do NOT use `typing.List`, `typing.Dict`, `typing.Tuple`, `typing.Set`, `typing.Optional`, or `typing.Union`. Use built-in generics (`list[X]`, `dict[K, V]`, `tuple[X, ...]`, `set[X]`) and `X | None` / `X | Y` union syntax instead
- **Strict type hints everywhere** — all function signatures, return types, and class attributes must be annotated
- **No `Any` unless unavoidable** — prefer specific types; use `dict[str, Any]` only for plugin data payloads

---

## Formatting & Linting

| Tool | Config |
|------|--------|
| **Ruff** | `pyproject.toml` → `[tool.ruff]` (rules: E, F, I, N, UP, B, A, SIM, D) |
| **MyPy** | Strict mode, `packages = ["src"]` |
| **Pydocstyle** | Google convention |

Run before committing:
```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

---

## Project Structure

```
src/
├── core/           # Engine internals (registry, lifecycle, executor, context, policies)
├── plugins/        # Plugin implementations grouped by type
│   ├── triggers/
│   ├── conditions/
│   ├── transformers/
│   └── actions/
├── governance/     # Validation gates and pipeline guards
├── agents/         # Agent infrastructure (LLM client, tools, prompts)
├── models/         # SQLModel persistence models
├── repositories/   # Repository pattern (CRUD)
├── api/            # FastAPI app (routes, schemas, errors)
└── database.py     # Engine and session management

tests/
├── unit/           # Mirrors src/ structure
│   ├── core/
│   └── plugins/
│       ├── triggers/
│       ├── conditions/
│       ├── transformers/
│       └── actions/
└── integration/    # End-to-end API and execution tests
```

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Module files | `snake_case.py` | `string_condition.py` |
| Classes | `PascalCase` | `StringContains`, `LogAction` |
| Functions/methods | `snake_case` | `evaluate`, `on_activate` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_TOOL_ITERATIONS` |
| Plugin names (manifest) | `kebab-case` | `"string-contains-condition"` |
| Test files | `test_<module>.py` | `test_string_condition.py` |
| Test functions | `test_<behavior>` | `test_contains`, `test_invalid_regex` |

---

## Module File Template

Every Python module starts with a module-level docstring:

```python
"""Brief description of the module's purpose."""
```

Import order (enforced by ruff `I` rule):
1. Standard library
2. Third-party
3. Local (`src.*`)

---

## Plugin Implementation Pattern

Every plugin follows this exact structure:

```python
"""Brief description of the plugin."""

from typing import Any

from src.core.contracts import ActionPlugin  # or TriggerPlugin, ConditionPlugin, TransformerPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin


@register_plugin
class MyPlugin(ActionPlugin):
    """One-line description of what this plugin does."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="my-plugin",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            permissions=[],
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Describe what execute does."""
        return data
```

### Required elements:
1. **`@register_plugin` decorator** — mandatory for build-time registry collection
2. **`manifest` property** — returns `PluginManifest` with unique `name` (kebab-case), `version` (semver), `plugin_type`, and `permissions`
3. **Contract method** — depends on plugin type:

| Base Class | Method | Signature |
|---|---|---|
| `TriggerPlugin` | `check()` | `() -> dict[str, Any]` |
| `ConditionPlugin` | `evaluate(data)` | `(dict[str, Any]) -> bool` |
| `TransformerPlugin` | `transform(data)` | `(dict[str, Any]) -> dict[str, Any]` |
| `ActionPlugin` | `execute(data)` | `(dict[str, Any]) -> dict[str, Any]` |

### Optional elements:
- Constructor `__init__` for configuration parameters
- Lifecycle hooks: `on_activate()`, `on_deactivate()`, `on_cleanup()`
- Logger: `logger = logging.getLogger(__name__)`

### Grouping related plugins:
When multiple plugins share logic (e.g. string conditions), create an abstract base class in the same file:

```python
class StringCondition(ConditionPlugin):
    """Base for string-based conditions."""

    def __init__(self, key: str = "", value: str = "") -> None:
        self._key = key
        self._value = value

    @abstractmethod
    def compare(self, actual: str, expected: str) -> bool: ...

    def evaluate(self, data: dict[str, Any]) -> bool:
        actual_value = data.get(self._key)
        if not isinstance(actual_value, str):
            return False
        return self.compare(actual_value, self._value)


@register_plugin
class StringContains(StringCondition):
    ...
```

---

## Test Conventions

See [`docs/TESTING.md`](TESTING.md) for the full testing guide (structure, naming, fixtures, assertions, plugin test patterns, integration tests, and coverage rules).

---

## Docstrings

Use **Google style** (enforced by ruff `D` rule + pydocstyle convention):

```python
def execute(self, data: dict[str, Any]) -> dict[str, Any]:
    """Execute action with input data.

    Args:
        data: The input payload from upstream nodes.

    Returns:
        The execution result passed to downstream nodes.

    Raises:
        ValueError: If required fields are missing.
    """
```

For simple methods, a one-liner is sufficient:

```python
def compare(self, actual: str, expected: str) -> bool:
    """Return True if expected is in actual."""
    return expected in actual
```

---

## Data Models

### Pydantic models (API schemas, manifests):
```python
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Standardized plugin manifest."""

    name: str = Field(min_length=1, description="Unique plugin identifier.")
    version: str = Field(min_length=1, description="Semantic version.")
```

### Dataclasses (internal value objects):
```python
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Per-node retry configuration."""

    max_attempts: int = 1
    delay_seconds: float = 0.0
    backoff_factor: float = 2.0
```

### Enums:
```python
from enum import StrEnum


class PluginType(StrEnum):
    """Plugin type classification."""

    TRIGGER = "trigger"
    CONDITION = "condition"
    TRANSFORMER = "transformer"
    ACTION = "action"
```

Use `StrEnum` for serializable enums, `@dataclass(frozen=True, slots=True)` for immutable value objects.

---

## Error Handling

- Define custom exceptions per domain:
  ```python
  class NodeExecutionError(Exception):
      """Raised when a node fails and error strategy is FAIL_FAST."""

      def __init__(self, node_id: str, message: str) -> None:
          self.node_id = node_id
          super().__init__(f"Node '{node_id}' failed: {message}")
  ```
- Never use bare `except:` — at minimum use `except Exception`
- Use `# noqa: BLE001` only when broad exception catching is intentional (e.g. in policy executors)
- Prefer early returns over deeply nested conditionals

---

## Imports

- Absolute imports only: `from src.core.contracts import PluginBase`
- No relative imports (`from .contracts import ...` is not used)
- Group: stdlib → third-party → local (ruff `I` rule enforces this)
- Use `from __future__ import annotations` only when needed for forward references
- Never import deprecated generics from `typing` (`List`, `Dict`, `Tuple`, `Set`, `Optional`, `Union`) — use built-in equivalents

---

## Architecture Rules (Non-Negotiable)

1. **Core Engine has no business logic** — only registry, lifecycle, context, orchestration
2. **Plugins never import from other plugins** — they are fully independent
3. **Plugins never access Core internals** — only use contracts and registration
4. **Execution contexts are always destroyed** — use `finally` blocks
5. **No runtime plugin discovery** — everything is build-time via `@register_plugin`
6. **ADRs are authoritative** — if code conflicts with an ADR, update the code

---

## Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use structured messages with %s formatting (not f-strings)
logger.info("LogAction received: %s", data)
logger.error("Node '%s' failed: %s", node_id, error)
```

- Use `logging.getLogger(__name__)` at module level
- Prefer `%s` substitution over f-strings in log calls (avoids formatting cost when level is disabled)

---

## Dependencies

- Managed via `uv` (lockfile: `uv.lock`)
- Declared in `pyproject.toml` under `[project.dependencies]` and `[project.optional-dependencies.dev]`
- Always run `uv sync --extra dev` to install all development tools
