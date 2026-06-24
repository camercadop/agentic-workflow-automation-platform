"""Plugin manifest model for build-time registration (ADR-002, ADR-005)."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PluginType(StrEnum):
    """Plugin type classification per domain model."""

    TRIGGER = "trigger"
    CONDITION = "condition"
    TRANSFORMER = "transformer"
    ACTION = "action"


class PortSchema(BaseModel):
    """Typed port declaration for workflow graph edges (ADR-007)."""

    name: str
    data_type: str
    description: str = ""
    required: bool = True


class PluginManifest(BaseModel):
    """Standardized plugin manifest for build-time registration.

    Plugins declare this metadata for validation against the Plugin Contract Model
    and inclusion in the Static Registry.
    """

    name: str = Field(
        min_length=1,
        description="Unique plugin identifier.",
    )
    version: str = Field(
        min_length=1,
        description="Semantic version of the plugin.",
    )
    description: str = Field(
        default="",
        description="Human-readable plugin description.",
    )
    plugin_type: PluginType = Field(
        description="Classification of the plugin's role in a workflow.",
    )
    permissions: list[str] = Field(
        default_factory=list,
        description="Resource permissions the plugin requires.",
    )
    inputs: list[PortSchema] = Field(
        default_factory=list,
        description="Input port declarations for workflow graph edges.",
    )
    outputs: list[PortSchema] = Field(
        default_factory=list,
        description="Output port declarations for workflow graph edges.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional plugin metadata.",
    )
