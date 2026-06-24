"""Core Engine: plugin contracts, registry, lifecycle, orchestration."""

from src.core.context import ContextManager, ExecutionContext, IsolationService
from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    PluginBase,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.executor import WorkflowExecutionError, WorkflowExecutor
from src.core.manifest import PluginManifest, PluginType, PortSchema
from src.core.registration import get_collected_plugins, register_plugin
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
    "get_collected_plugins",
    "register_plugin",
    "PortSchema",
    "TransformerPlugin",
    "TriggerPlugin",
    "WorkflowDefinition",
    "WorkflowEdge",
    "WorkflowExecutionError",
    "WorkflowExecutor",
    "WorkflowNode",
]
