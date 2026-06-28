"""Plugin API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.manifest import PluginType
from src.core.registry import LifecycleState


class PluginCreate(BaseModel):
    """Request schema for registering a plugin."""

    name: str = Field(
        min_length=1,
        description="Plugin name.",
    )
    version: str = Field(
        min_length=1,
        description="Plugin semantic version.",
    )
    plugin_type: PluginType = Field(
        description="Plugin type (trigger, condition, transformer, action).",
    )
    manifest: dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin manifest metadata.",
    )


class PluginUpdate(BaseModel):
    """Request schema for updating plugin lifecycle state."""

    lifecycle_state: LifecycleState = Field(description="Target lifecycle state.")


class PluginResponse(BaseModel):
    """Response schema for plugin records."""

    id: uuid.UUID = Field(description="Plugin unique identifier.")
    name: str = Field(description="Plugin name.")
    version: str = Field(description="Plugin semantic version.")
    plugin_type: PluginType = Field(description="Plugin type.")
    lifecycle_state: LifecycleState = Field(description="Current lifecycle state.")
    manifest: dict[str, Any] = Field(description="Plugin manifest metadata.")
    registered_at: datetime = Field(description="Registration timestamp.")
    last_verified: datetime | None = Field(description="Last verification timestamp.")

    model_config = {"from_attributes": True}
