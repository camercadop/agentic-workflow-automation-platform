"""Workflow API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowNodeSchema(BaseModel):
    """Schema for a workflow node definition."""

    node_id: str = Field(
        min_length=1,
        description="Unique identifier for this node within the workflow.",
    )
    plugin_name: str = Field(
        min_length=1,
        description="Name of the plugin to execute at this node.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin configuration including execution policies.",
    )


class WorkflowEdgeSchema(BaseModel):
    """Schema for a workflow edge (data flow between nodes)."""

    source_node: str = Field(
        min_length=1,
        description="Node ID of the edge source.",
    )
    source_port: str = Field(
        min_length=1,
        description="Output port name on the source node.",
    )
    target_node: str = Field(
        min_length=1,
        description="Node ID of the edge target.",
    )
    target_port: str = Field(
        min_length=1,
        description="Input port name on the target node.",
    )
    data_type: str = Field(
        default="any",
        description="Expected data type flowing through this edge.",
    )
    condition: str | None = Field(
        default=None,
        description="Optional condition expression for conditional edges.",
    )


class WorkflowCreate(BaseModel):
    """Request schema for creating a workflow."""

    name: str = Field(
        min_length=1,
        description="Workflow name.",
    )
    version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Semantic version of the workflow definition.",
    )
    nodes: list[WorkflowNodeSchema] = Field(
        min_length=1,
        description="List of nodes in the workflow DAG.",
    )
    edges: list[WorkflowEdgeSchema] = Field(
        default_factory=list,
        description="List of edges defining data flow between nodes.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for the workflow.",
    )


class WorkflowUpdate(BaseModel):
    """Request schema for updating a workflow."""

    version: str | None = Field(
        default=None,
        min_length=1,
        description="New semantic version.",
    )
    nodes: list[WorkflowNodeSchema] | None = Field(
        default=None,
        description="Replacement node list.",
    )
    edges: list[WorkflowEdgeSchema] | None = Field(
        default=None,
        description="Replacement edge list.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Replacement metadata.",
    )


class WorkflowResponse(BaseModel):
    """Response schema for workflow records."""

    id: uuid.UUID = Field(description="Workflow unique identifier.")
    name: str = Field(description="Workflow name.")
    version: str = Field(description="Semantic version.")
    nodes: list[WorkflowNodeSchema] = Field(description="Workflow nodes.")
    edges: list[WorkflowEdgeSchema] = Field(description="Workflow edges.")
    metadata_: dict[str, Any] = Field(description="Workflow metadata.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last update timestamp.")

    model_config = {"from_attributes": True}


class WorkflowExecuteRequest(BaseModel):
    """Request schema for executing a workflow."""

    initial_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial data passed to the workflow trigger node.",
    )


class WorkflowExecuteResponse(BaseModel):
    """Response schema for workflow execution results."""

    execution_id: uuid.UUID = Field(description="Unique execution identifier.")
    workflow_id: uuid.UUID = Field(description="ID of the executed workflow.")
    status: str = Field(description="Execution status (e.g. completed, failed).")
    results: dict[str, dict[str, Any]] = Field(
        description="Per-node execution results keyed by node ID."
    )
