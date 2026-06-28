"""Workflow execution persistence model."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ExecutionStatus(StrEnum):
    """Possible states of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowExecution(SQLModel, table=True):
    """Persistence model for workflow execution records."""

    __tablename__ = "workflow_executions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique identifier for the workflow execution (UUID)",
    )
    workflow_id: str = Field(
        index=True,
        nullable=False,
        description="Reference to the workflow definition ID",
    )
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Current execution status",
    )
    context: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=dict,
        description="Workflow context data at this execution point",
    )
    context_version: int = Field(
        default=1,
        description="Version number of the context for optimistic locking",
    )
    started_at: datetime | None = Field(
        default=None,
        description="When the execution transitioned to RUNNING",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the execution was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the execution record was last updated",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When the execution completed (success or failure)",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed",
    )
