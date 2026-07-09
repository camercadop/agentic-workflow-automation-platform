# API Routes

FastAPI route handlers organized by domain resource. Each module defines an `APIRouter` instance mounted by the main application.

## Modules

| Module | Prefix | Tag | Description |
|--------|--------|-----|-------------|
| `workflows.py` | `/workflows` | workflows | CRUD and execution of workflow definitions |
| `plugins.py` | `/plugins` | plugins | Plugin registry management and lifecycle |
| `executions.py` | `/executions` | executions | Execution record CRUD and status tracking |

## Endpoint Reference

### Workflows (`workflows.py`)

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `GET` | `/workflows/` | 200 | List all workflow definitions |
| `GET` | `/workflows/{workflow_id}` | 200 | Get workflow by UUID |
| `POST` | `/workflows/` | 201 | Create workflow (validates DAG acyclicity and edge integrity) |
| `PATCH` | `/workflows/{workflow_id}` | 200 | Update workflow (re-validates DAG on node/edge changes) |
| `DELETE` | `/workflows/{workflow_id}` | 204 | Delete workflow |
| `POST` | `/workflows/{workflow_id}/execute` | 201 | Execute workflow and record result |

### Plugins (`plugins.py`)

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `GET` | `/plugins/` | 200 | List all registered plugins |
| `GET` | `/plugins/{plugin_id}` | 200 | Get plugin by UUID |
| `POST` | `/plugins/` | 201 | Register a new plugin |
| `PATCH` | `/plugins/{plugin_id}` | 200 | Update plugin lifecycle state |
| `DELETE` | `/plugins/{plugin_id}` | 204 | Delete plugin |

### Executions (`executions.py`)

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `GET` | `/executions/` | 200 | List all executions |
| `GET` | `/executions/{execution_id}` | 200 | Get execution by UUID |
| `POST` | `/executions/` | 201 | Create execution record |
| `PATCH` | `/executions/{execution_id}` | 200 | Update execution status |
| `DELETE` | `/executions/{execution_id}` | 204 | Delete execution |

## Architecture

### Dependency Injection

All routes use FastAPI's `Depends()` system for:
- **Database sessions** — Injected via `get_session` from `src.database`
- **Repositories** — Each module defines a `_get_repo()` factory that wraps the session in the appropriate repository class
- **App-level singletons** — `workflows.py` accesses `PluginRegistry` and `ContextManager` from `request.app.state`

Type aliases (e.g., `RepoDep`, `ExecRepoDep`, `RegistryDep`) keep handler signatures concise.

### Error Handling

All routes delegate to `src.api.errors.raise_not_found()` for 404 responses. Validation errors (invalid DAG structure, schema violations) are raised as `422 Unprocessable Entity` by Pydantic/FastAPI automatically.

### DAG Validation

The `POST` and `PATCH` workflow endpoints construct a `WorkflowDefinition` from the request body before persisting. This validates:
- Node ID uniqueness
- Edge source/target reference existing nodes
- Graph acyclicity (no cycles in the DAG)

### Workflow Execution Flow

`POST /workflows/{id}/execute`:
1. Loads the persisted workflow and builds a `WorkflowDefinition`
2. Creates a `WorkflowExecution` record with status `RUNNING`
3. Runs the DAG via `WorkflowExecutor` (with retry, timeout, and error strategy policies)
4. Updates execution status to `COMPLETED` or `FAILED`
5. Returns execution ID, status, and node results

## Schemas

Request/response schemas are defined in `src/api/schemas/` using Pydantic v2 models. See that package for field-level documentation.
