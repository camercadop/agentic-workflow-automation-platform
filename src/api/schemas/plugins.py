"""Plugin API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.manifest import PluginType
from src.core.registry import LifecycleState


class PluginCreate(BaseModel):
    """Request schema for registering a plugin."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    plugin_type: PluginType
    manifest: dict[str, Any] = Field(default_factory=dict)


class PluginUpdate(BaseModel):
    """Request schema for updating plugin lifecycle state."""

    lifecycle_state: LifecycleState


class PluginResponse(BaseModel):
    """Response schema for plugin records."""

    id: uuid.UUID
    name: str
    version: str
    plugin_type: PluginType
    lifecycle_state: LifecycleState
    manifest: dict[str, Any]
    registered_at: datetime
    last_verified: datetime | None

    model_config = {"from_attributes": True}
