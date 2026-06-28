"""Workflow API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowNodeSchema(BaseModel):
    node_id: str = Field(min_length=1)
    plugin_name: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdgeSchema(BaseModel):
    source_node: str = Field(min_length=1)
    source_port: str = Field(min_length=1)
    target_node: str = Field(min_length=1)
    target_port: str = Field(min_length=1)
    data_type: str = Field(default="any")


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(default="1.0.0", min_length=1)
    nodes: list[WorkflowNodeSchema] = Field(min_length=1)
    edges: list[WorkflowEdgeSchema] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1)
    nodes: list[WorkflowNodeSchema] | None = None
    edges: list[WorkflowEdgeSchema] | None = None
    metadata: dict[str, Any] | None = None


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: str
    nodes: list[WorkflowNodeSchema]
    edges: list[WorkflowEdgeSchema]
    metadata_: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecuteRequest(BaseModel):
    initial_data: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecuteResponse(BaseModel):
    execution_id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    results: dict[str, dict[str, Any]]
