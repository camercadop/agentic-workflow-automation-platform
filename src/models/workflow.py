"""Workflow definition persistence model."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Workflow(SQLModel, table=True):
    """Persistence model for workflow definitions."""

    __tablename__ = "workflows"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique identifier for the workflow (UUID)",
    )
    name: str = Field(
        index=True,
        nullable=False,
        unique=True,
        description="Unique workflow name",
    )
    version: str = Field(
        default="1.0.0",
        nullable=False,
        description="Semantic version of the workflow definition",
    )
    nodes: list[dict[str, Any]] = Field(
        sa_column=Column(JSON),
        default_factory=list,
        description="List of workflow nodes (plugin references with config)",
    )
    edges: list[dict[str, Any]] = Field(
        sa_column=Column(JSON),
        default_factory=list,
        description="List of directed edges defining data flow",
    )
    metadata_: dict[str, Any] = Field(
        sa_column=Column("metadata", JSON),
        default_factory=dict,
        description="Additional workflow-level metadata",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the workflow was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the workflow was last updated",
    )
