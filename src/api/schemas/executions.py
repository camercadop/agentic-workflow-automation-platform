"""Execution API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.models.execution import ExecutionStatus


class ExecutionCreate(BaseModel):
    """Request schema for creating workflow executions."""

    workflow_id: str = Field(
        min_length=1,
        description="ID of the workflow to execute.",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial execution context data.",
    )


class ExecutionUpdate(BaseModel):
    """Request schema for updating execution status."""

    status: ExecutionStatus = Field(description="New execution status.")


class ExecutionResponse(BaseModel):
    """Response schema for workflow executions."""

    id: uuid.UUID = Field(
        description="Execution unique identifier.",
    )
    workflow_id: str = Field(
        description="ID of the executed workflow.",
    )
    status: ExecutionStatus = Field(
        description="Current execution status.",
    )
    context: dict[str, Any] = Field(
        description="Execution context data.",
    )
    context_version: int = Field(
        description="Optimistic concurrency version for the context."
    )
    started_at: datetime | None = Field(
        description="Timestamp when execution started.",
    )
    created_at: datetime = Field(
        description="Creation timestamp.",
    )
    updated_at: datetime = Field(
        description="Last update timestamp.",
    )
    completed_at: datetime | None = Field(
        description="Timestamp when execution completed.",
    )
    error: str | None = Field(
        description="Error message if execution failed.",
    )

    model_config = {"from_attributes": True}
