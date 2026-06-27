"""API request/response schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.manifest import PluginType
from src.core.registry import LifecycleState
from src.models.execution import ExecutionStatus

# --- Plugin schemas ---


class PluginCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    plugin_type: PluginType
    manifest: dict[str, Any] = Field(default_factory=dict)


class PluginResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: str
    plugin_type: PluginType
    lifecycle_state: LifecycleState
    manifest: dict[str, Any]
    registered_at: datetime
    last_verified: datetime | None

    model_config = {"from_attributes": True}


# --- Execution schemas ---


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
