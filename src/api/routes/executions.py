"""Workflow execution API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas import ExecutionCreate, ExecutionResponse
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
    return repo.list()


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: uuid.UUID, repo: RepoDep) -> WorkflowExecution:
    execution = repo.get(str(execution_id))
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/", response_model=ExecutionResponse, status_code=201)
def create_execution(body: ExecutionCreate, repo: RepoDep) -> WorkflowExecution:
    execution = WorkflowExecution(
        workflow_id=body.workflow_id,
        context=body.context,
    )
    return repo.create(execution)
