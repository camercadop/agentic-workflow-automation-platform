"""Execution API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.models.execution import ExecutionStatus


class ExecutionCreate(BaseModel):
    workflow_id: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: str
    status: ExecutionStatus
    context: dict[str, Any]
    context_version: int
    started_at: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}
