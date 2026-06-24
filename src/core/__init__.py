"""Core Engine: plugin contracts, registry, lifecycle, orchestration."""

from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    PluginBase,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.manifest import PluginManifest, PluginType, PortSchema
from src.core.registry import LifecycleError, LifecycleState, PluginRegistry

__all__ = [
    "ActionPlugin",
    "ConditionPlugin",
    "LifecycleError",
    "LifecycleState",
    "PluginBase",
    "PluginManifest",
    "PluginType",
    "PluginRegistry",
    "PortSchema",
    "TransformerPlugin",
    "TriggerPlugin",
]
