# Base Repository

Abstract base classes providing the repository pattern foundation.

| Module | Purpose |
|--------|---------|
| `repository.py` | Abstract `BaseRepository` interface defining the contract |
| `crud.py` | Generic CRUD mixin (create, read, update, delete, list) |

All concrete repositories (`workflows.py`, `plugins.py`, `executions.py`) extend these bases.
