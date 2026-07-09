"""Workflow API routes."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette import status

from src.api.errors import raise_not_found, raise_validation_error
from src.api.schemas.workflows import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode
from src.database import get_session
from src.governance import ValidationEngine
from src.models.execution import ExecutionStatus, WorkflowExecution
from src.models.workflow import Workflow
from src.repositories.executions import WorkflowExecutionRepository
from src.repositories.workflows import WorkflowRepository

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _get_registry(request: Request) -> PluginRegistry:
    return request.app.state.registry  # type: ignore[no-any-return]


def _get_context_manager(request: Request) -> ContextManager:
    return request.app.state.context_manager  # type: ignore[no-any-return]


def _get_repo(session: Annotated[Session, Depends(get_session)]) -> WorkflowRepository:
    return WorkflowRepository(session)


def _get_execution_repo(
    session: Annotated[Session, Depends(get_session)],
) -> WorkflowExecutionRepository:
    return WorkflowExecutionRepository(session)


RepoDep = Annotated[WorkflowRepository, Depends(_get_repo)]
ExecRepoDep = Annotated[WorkflowExecutionRepository, Depends(_get_execution_repo)]
RegistryDep = Annotated[PluginRegistry, Depends(_get_registry)]
CtxMgrDep = Annotated[ContextManager, Depends(_get_context_manager)]


@router.get("/", response_model=list[WorkflowResponse])
def list_workflows(repo: RepoDep) -> list[Workflow]:
    """List all workflow definitions."""
    return repo.list()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: uuid.UUID, repo: RepoDep) -> Workflow:
    """Get a workflow definition by ID."""
    workflow = repo.get(workflow_id)
    if workflow is None:
        raise_not_found("Workflow not found")
    return workflow


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    body: WorkflowCreate, repo: RepoDep, registry: RegistryDep
) -> Workflow:
    """Create a new workflow definition.

    Validates DAG structure (acyclicity, edge integrity) and runs
    governance gates (ADR-009) against registered plugins.
    """
    definition = WorkflowDefinition(
        name=body.name,
        version=body.version,
        nodes=[WorkflowNode(**n.model_dump()) for n in body.nodes],
        edges=[WorkflowEdge(**e.model_dump()) for e in body.edges],
        metadata=body.metadata,
    )

    # Run workflow governance gate against live registry
    registered = {name: registry.get(name).plugin for name in registry.plugins}
    report = ValidationEngine().validate_workflow(definition, registered)
    if not report.passed:
        raise_validation_error(report.errors)

    workflow = Workflow(
        name=body.name,
        version=body.version,
        nodes=[n.model_dump() for n in body.nodes],
        edges=[e.model_dump() for e in body.edges],
        metadata_=body.metadata,
    )
    return repo.create(workflow)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: uuid.UUID, body: WorkflowUpdate, repo: RepoDep
) -> Workflow:
    """Update a workflow definition."""
    workflow = repo.get(workflow_id)
    if workflow is None:
        raise_not_found("Workflow not found")

    update_data = body.model_dump(exclude_none=True)

    # If nodes or edges change, re-validate the DAG
    nodes = update_data.get("nodes", workflow.nodes)
    edges = update_data.get("edges", workflow.edges)
    if isinstance(nodes, list) and nodes and hasattr(nodes[0], "model_dump"):
        nodes = [n.model_dump() for n in nodes]
    if isinstance(edges, list) and edges and hasattr(edges[0], "model_dump"):
        edges = [e.model_dump() for e in edges]

    WorkflowDefinition(
        name=workflow.name,
        version=update_data.get("version", workflow.version),
        nodes=[WorkflowNode(**n) for n in nodes],
        edges=[WorkflowEdge(**e) for e in edges],
    )

    if "version" in update_data:
        workflow.version = update_data["version"]
    if "nodes" in update_data:
        workflow.nodes = nodes
    if "edges" in update_data:
        workflow.edges = edges
    if "metadata" in update_data:
        workflow.metadata_ = update_data["metadata"]
    workflow.updated_at = datetime.now(UTC)

    return repo.update(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: uuid.UUID, repo: RepoDep) -> None:
    """Delete a workflow definition by ID."""
    workflow = repo.get(workflow_id)
    if workflow is None:
        raise_not_found("Workflow not found")
    repo.delete(workflow_id)


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecuteResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_workflow(
    workflow_id: uuid.UUID,
    body: WorkflowExecuteRequest,
    repo: RepoDep,
    exec_repo: ExecRepoDep,
    registry: RegistryDep,
    ctx_mgr: CtxMgrDep,
) -> dict[str, Any]:
    """Trigger execution of a workflow definition.

    Loads the persisted DAG, runs it through the WorkflowExecutor,
    and records the execution result.
    """
    workflow = repo.get(workflow_id)
    if workflow is None:
        raise_not_found("Workflow not found")

    # Build the core WorkflowDefinition from persisted data
    definition = WorkflowDefinition(
        name=workflow.name,
        version=workflow.version,
        nodes=[WorkflowNode(**n) for n in workflow.nodes],
        edges=[WorkflowEdge(**e) for e in workflow.edges],
    )

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=str(workflow_id),
        context=body.initial_data,
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    execution = exec_repo.create(execution)

    # Run the workflow
    executor = WorkflowExecutor(registry, ctx_mgr)
    try:
        results = executor.execute(definition, body.initial_data)
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = datetime.now(UTC)
        execution.context = results
    except Exception as exc:
        results = {}
        execution.status = ExecutionStatus.FAILED
        execution.completed_at = datetime.now(UTC)
        execution.error = str(exc)

    exec_repo.update(execution)

    return {
        "execution_id": execution.id,
        "workflow_id": workflow.id,
        "status": execution.status,
        "results": results,
    }
