"""Core Engine: plugin contracts, registry, lifecycle, orchestration."""

from src.core.context import ContextManager, ExecutionContext, IsolationService
from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    PluginBase,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.manifest import PluginManifest, PluginType, PortSchema
from src.core.registry import LifecycleError, LifecycleState, PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode

__all__ = [
    "ActionPlugin",
    "ConditionPlugin",
    "ContextManager",
    "ExecutionContext",
    "IsolationService",
    "LifecycleError",
    "LifecycleState",
    "PluginBase",
    "PluginManifest",
    "PluginType",
    "PluginRegistry",
    "PortSchema",
    "TransformerPlugin",
    "TriggerPlugin",
    "WorkflowDefinition",
    "WorkflowEdge",
    "WorkflowNode",
]
