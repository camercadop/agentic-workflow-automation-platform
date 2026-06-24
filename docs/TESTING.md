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
src/core/<module>.py      → tests/unit/test_<module>.py
src/api/<module>.py       → tests/integration/test_<module>.py
```

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

## Coverage

- Coverage is reported automatically via `pytest-cov` (configured in `pyproject.toml`).
- All new modules must have corresponding unit tests.
- Prioritize meaningful assertions over line-coverage targets. Unreachable defensive branches (e.g., unknown plugin type fallback) do not require forced coverage.
