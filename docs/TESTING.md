# Testing Guide

> **Audience:** Human developers and AI agents writing or maintaining tests.
> This document defines testing conventions and structure for the project.

---

## Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run a specific test file
uv run pytest tests/unit/test_registry.py


# Run with verbose output
uv run pytest -v
```

---

## Directory Structure

Tests mirror the source layout:

```
src/core/<module>.py                        → tests/unit/core/test_<module>.py
src/plugins/<type>/<plugin>.py              → tests/unit/plugins/<type>/test_<plugin>.py
src/api/<module>.py                         → tests/integration/test_<module>.py
```

Plugin tests preserve the plugin type subdirectory (e.g., `actions/`, `triggers/`).
Integration tests go in `tests/integration/`.

---

## Test Organization

Group tests in classes by behavior or component aspect:

```python
class TestPluginRegistration:
    """Tests for registering plugins in the registry."""

    def test_register_and_get(self) -> None: ...
    def test_duplicate_registration_raises(self) -> None: ...


class TestLifecycleTransitions:
    """Tests for lifecycle state machine transitions."""

    def test_full_lifecycle(self) -> None: ...
    def test_invalid_transition_raises(self) -> None: ...
```

---

## Naming Conventions

Use descriptive names following the pattern: `test_<action>_<condition_or_scenario>`:

```python
def test_register_and_get(self) -> None: ...
def test_duplicate_registration_raises(self) -> None: ...
def test_cycle_detected(self) -> None: ...
def test_provision_creates_active_context(self) -> None: ...
def test_denied_isolation_raises(self) -> None: ...
```

The name should make the expected behavior clear without reading the test body.

---

## Type Annotations

All test functions must have a return type annotation of `-> None`:

```python
def test_example(self) -> None:
    assert 1 + 1 == 2
```

---

## Test Helpers and Fixtures

- Define test-only stubs (e.g., `_StubAction`, `_Trigger`) at the top of the test file, prefixed with underscore.
- Use factory functions (e.g., `_setup_registry()`, `_make_manifest()`) to reduce repetition.
- Prefer explicit setup over implicit fixtures when the test is simple.

```python
class _StubAction(ActionPlugin):
    """Minimal action plugin for testing."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="stub-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            contract_version="1.0.0",
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"done": True}


def _setup_registry() -> PluginRegistry:
    registry = PluginRegistry()
    registry.register(_StubAction())
    registry.activate("stub-action")
    registry.mark_active("stub-action")
    return registry
```

---

## Assertions

- Use plain `assert` statements (pytest rewrites them for clear failure messages).
- Test one logical behavior per test method.
- Use `pytest.raises` for expected exceptions, with `match` to verify the message:

```python
def test_invalid_transition_raises(self) -> None:
    registry = PluginRegistry()
    registry.register(_StubAction())

    with pytest.raises(LifecycleError):
        registry.mark_active("stub-action")
```

---

## Plugin Test Conventions

Every plugin test file must cover at minimum:

1. **Manifest metadata** — verify `name`, `version`, and `plugin_type`.
2. **Core behavior** — call the plugin's primary method (`execute`, `check`, `evaluate`, etc.) and assert expected output.
3. **Side effects** — if the plugin produces side effects (logging, I/O), assert them using pytest fixtures like `caplog`.

Plugin tests instantiate the plugin directly without the registry:

```python
"""Unit tests for LogAction plugin."""

import logging
from typing import Any

from src.core.manifest import PluginType
from src.plugins.actions.log_action import LogAction


class TestLogAction:
    """Tests for LogAction plugin behavior."""

    def test_execute_returns_data_unchanged(self) -> None:
        action = LogAction()
        data: dict[str, Any] = {"key": "value", "count": 42}
        result = action.execute(data)
        assert result == data

    def test_execute_logs_data(self, caplog: logging.LogCaptureFixture) -> None:
        action = LogAction()
        data: dict[str, Any] = {"msg": "hello"}
        with caplog.at_level(logging.INFO):
            action.execute(data)
        assert "LogAction received" in caplog.text

    def test_manifest_metadata(self) -> None:
        action = LogAction()
        manifest = action.manifest
        assert manifest.name == "log-action"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.ACTION
```

---

## Integration Test Conventions

Integration tests exercise the full runtime pipeline: registry → lifecycle → workflow → executor.

Structure each integration test as:
1. **Setup** — create a `PluginRegistry`, register and activate plugins.
2. **Define** — build a `WorkflowDefinition` with `WorkflowNode` entries.
3. **Execute** — run via `WorkflowExecutor`.
4. **Assert** — verify output results keyed by node ID.

```python
def test_trigger_plugin_execution() -> None:
    registry = PluginRegistry()
    trigger = ManualTrigger(config={"data": {"event_type": "test"}})
    registry.register(trigger)
    registry.activate("manual-trigger")
    registry.mark_active("manual-trigger")

    wf = WorkflowDefinition(
        name="integration-test",
        nodes=[WorkflowNode(node_id="start", plugin_name="manual-trigger")],
    )

    executor = WorkflowExecutor(registry, ContextManager())
    results = executor.execute(wf)

    assert "start" in results
    assert results["start"]["event"] == "manual"
```

---

## Coverage

- Coverage is reported automatically via `pytest-cov` (configured in `pyproject.toml`).
- All new modules must have corresponding unit tests.
- Prioritize meaningful assertions over line-coverage targets. Unreachable defensive branches (e.g., unknown plugin type fallback) do not require forced coverage.
