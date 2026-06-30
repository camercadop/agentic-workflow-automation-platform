# Contributing

> **Audience:** Human developers and AI agents contributing to this project.
> Read this document before writing or modifying any code.

---

## Prerequisites

- Python 3.12+
- Package manager: [uv](https://docs.astral.sh/uv/)
- Install dependencies:

```bash
uv sync --extra dev
```

---

## Tooling & Validation

| Tool | Purpose | Command |
|------|---------|---------|
| Ruff | Lint + format | `uv run ruff check src/ tests/` |
| MyPy | Type checking (strict mode) | `uv run mypy src/` |
| Pytest | Tests + coverage | `uv run pytest` |

All three must pass with zero errors before any code is merged.

Run all checks at once:

```bash
uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest
```

---

## Code Style & Formatting

- Line length ≤ 88 characters (enforced by Ruff).
- Break long lines with parentheses, never backslashes.
- Trailing commas on multi-line structures (function args, lists, dicts).
- Imports sorted by Ruff (isort-compatible). Group order: stdlib → third-party → local.
- Ruff lint rules enabled: `E`, `F`, `I`, `N`, `UP`, `B`, `A`, `SIM`.


---

## Type Safety & Annotations

- MyPy runs in strict mode. All functions must have full type annotations (parameters and return type).
- Use `from __future__ import annotations` for forward references.
- Use `typing.Protocol` for extension points where external code implements the interface (duck-typing contracts, e.g., `IsolationService`).
- Use ABC for plugin base classes where subclassing is the expected pattern.
- Avoid `Any` unless interfacing with truly dynamic data. Prefer specific types or generics.

---

## Documentation

- Every module must have a module-level docstring referencing relevant ADRs:

  ```python
  """Plugin Registry and Lifecycle Management (ADR-002, ADR-003)."""
  ```

- Docstrings on all public classes and methods. Use imperative mood ("Return the plugin manifest", not "Returns the plugin manifest").
- Minimal inline comments. Code should be self-explanatory. Use comments only for non-obvious design decisions or ADR references.
- Update `docs/DEVELOPER_GUIDE.md` when adding new public APIs or patterns.

---

## Data Modeling Conventions

- Use Pydantic `BaseModel` for validated domain models.
- Every `Field()` must include a `description` parameter. No exceptions.

  ```python
  name: str = Field(
      min_length=1,
      description="Unique plugin identifier.",
  )
  ```


---

## Error Handling

- Define domain-specific exceptions per module (`LifecycleError`, `WorkflowExecutionError`). Never raise bare `Exception`.
- Validate at construction time. Invalid objects must never exist. Reject bad state in `__init__` or `model_validator`.
- Exception messages must be descriptive, including the entity name and current state:

  ```python
  raise LifecycleError(
      f"Cannot transition '{entry.name}' from {entry.state} to {target}."
  )
  ```

---

## Architecture Rules

- **ADRs are the source of truth.** If code conflicts with an ADR, the ADR wins. Update the code.
- **No runtime plugin discovery** (ADR-002). Plugins are registered programmatically at startup from static configuration.
- **No business logic in the Core Engine** (ADR-001). Core handles only registry, lifecycle, context, and orchestration.
- **Plugin isolation is mandatory** (ADR-004, ADR-006). Plugins never share execution contexts, access each other's state, or reference Core internals.
- **Execution contexts are ephemeral** (ADR-006). Always provision before execution and destroy in a `finally` block.
- **Lifecycle transitions are strictly sequential** (ADR-003). No skipping states. The registry enforces this.
- **Pipeline guards are mandatory.** The orchestrator enforces artifact existence, syntax validity, and test execution between pipeline steps. Any new pipeline step must have corresponding guards in `src/governance/pipeline_guards.py`.

---

## Adding a New Core Module

1. Create `src/core/<module>.py` with a module-level docstring referencing relevant ADRs.
2. Export public symbols from `src/core/__init__.py` in alphabetical order.
3. Create `tests/unit/test_<module>.py` with class-grouped tests (see [`docs/TESTING.md`](docs/TESTING.md)).
4. Run all checks: `uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest`.
5. Update `docs/DEVELOPER_GUIDE.md` if the module introduces new patterns or public APIs.
