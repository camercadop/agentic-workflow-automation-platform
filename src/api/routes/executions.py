"""Workflow execution API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from src.api.errors import raise_not_found
from src.api.schemas import ExecutionCreate, ExecutionResponse, ExecutionUpdate
from src.database import get_session
from src.models.execution import WorkflowExecution
from src.repositories.executions import WorkflowExecutionRepository

router = APIRouter(prefix="/executions", tags=["executions"])


def _get_repo(
    session: Annotated[Session, Depends(get_session)],
) -> WorkflowExecutionRepository:
    return WorkflowExecutionRepository(session)


RepoDep = Annotated[WorkflowExecutionRepository, Depends(_get_repo)]


@router.get("/", response_model=list[ExecutionResponse])
def list_executions(repo: RepoDep) -> list[WorkflowExecution]:
    """List all workflow executions."""
    return repo.list()


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: uuid.UUID, repo: RepoDep) -> WorkflowExecution:
    """Get a workflow execution by ID."""
    execution = repo.get(execution_id)
    if execution is None:
        raise_not_found("Execution not found")
    return execution


@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(body: ExecutionCreate, repo: RepoDep) -> WorkflowExecution:
    """Create a new workflow execution."""
    execution = WorkflowExecution(
        workflow_id=body.workflow_id,
        context=body.context,
    )
    return repo.create(execution)


@router.patch("/{execution_id}", response_model=ExecutionResponse)
def update_execution(
    execution_id: uuid.UUID, body: ExecutionUpdate, repo: RepoDep
) -> WorkflowExecution:
    """Update a workflow execution's status."""
    execution = repo.get(execution_id)
    if execution is None:
        raise_not_found("Execution not found")
    execution.status = body.status
    return repo.update(execution)


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(execution_id: uuid.UUID, repo: RepoDep) -> None:
    """Delete a workflow execution by ID."""
    execution = repo.get(execution_id)
    if execution is None:
        raise_not_found("Execution not found")
    repo.delete(execution_id)
