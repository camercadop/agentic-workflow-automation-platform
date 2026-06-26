"""Plugin persistence model."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from src.core.manifest import PluginType
from src.core.registry import LifecycleState


class Plugin(SQLModel, table=True):
    __tablename__ = "plugins"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique identifier for the plugin (UUID)",
    )
    name: str = Field(
        index=True,
        nullable=False,
        unique=True,
        description="Name of the plugin (unique)",
    )
    version: str = Field(
        nullable=False,
        description="Semantic version of the plugin",
    )
    plugin_type: PluginType = Field(
        index=True,
        nullable=False,
        description="Plugin role classification",
    )
    lifecycle_state: LifecycleState = Field(
        default=LifecycleState.REGISTERED,
        index=True,
        nullable=False,
        description="Current lifecycle state of the plugin",
    )
    manifest: dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=dict,
        description="Plugin manifest metadata in JSON format",
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the plugin was registered in the database",
    )
    last_verified: datetime | None = Field(
        default=None,
        description="Timestamp of last successful verification",
    )
