"""Unit tests for workflow executor (ADR-006, ADR-007)."""

from typing import Any

import pytest
from src.core.context import ContextManager
from src.core.contracts import ActionPlugin, TransformerPlugin, TriggerPlugin
from src.core.executor import WorkflowExecutionError, WorkflowExecutor
from src.core.manifest import PluginManifest, PluginType
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode


class _Trigger(TriggerPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="test-trigger",
            version="1.0.0",
            plugin_type=PluginType.TRIGGER,
            contract_version="1.0.0",
        )

    def check(self) -> dict[str, Any]:
        return {"event": "timer", "payload": "hello"}


class _Transformer(TransformerPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="test-transformer",
            version="1.0.0",
            plugin_type=PluginType.TRANSFORMER,
            contract_version="1.0.0",
        )

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        return {**data, "transformed": True}


class _Action(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="test-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            contract_version="1.0.0",
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"status": "sent", "input": data}


def _setup_registry() -> PluginRegistry:
    registry = PluginRegistry()
    for plugin in (_Trigger(), _Transformer(), _Action()):
        registry.register(plugin)
        registry.activate(plugin.manifest.name)
        registry.mark_active(plugin.manifest.name)
    return registry


class TestWorkflowExecutor:
    def test_single_node_execution(self) -> None:
        registry = _setup_registry()
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="single",
            nodes=[
                WorkflowNode(
                    node_id="t", plugin_name="test-trigger"
                ),
            ],
        )
        results = executor.execute(wf)
        assert results["t"] == {"event": "timer", "payload": "hello"}

    def test_linear_pipeline(self) -> None:
        registry = _setup_registry()
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="pipeline",
            nodes=[
                WorkflowNode(
                    node_id="t", plugin_name="test-trigger"
                ),
                WorkflowNode(
                    node_id="x", plugin_name="test-transformer"
                ),
                WorkflowNode(
                    node_id="a", plugin_name="test-action"
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="x",
                    target_port="data",
                ),
                WorkflowEdge(
                    source_node="x",
                    source_port="output",
                    target_node="a",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert results["t"]["event"] == "timer"
        assert results["x"]["transformed"] is True
        assert results["a"]["status"] == "sent"

    def test_inactive_plugin_raises(self) -> None:
        registry = PluginRegistry()
        registry.register(_Trigger())
        # Not activated — still in REGISTERED state
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="fail",
            nodes=[
                WorkflowNode(
                    node_id="t", plugin_name="test-trigger"
                ),
            ],
        )
        with pytest.raises(WorkflowExecutionError, match="not active"):
            executor.execute(wf)

    def test_unknown_plugin_raises(self) -> None:
        registry = PluginRegistry()
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="missing",
            nodes=[
                WorkflowNode(
                    node_id="t", plugin_name="nonexistent"
                ),
            ],
        )
        with pytest.raises(KeyError, match="not found"):
            executor.execute(wf)

    def test_context_destroyed_after_execution(self) -> None:
        registry = _setup_registry()
        cm = ContextManager()
        executor = WorkflowExecutor(registry, cm)
        wf = WorkflowDefinition(
            name="ctx-test",
            nodes=[
                WorkflowNode(
                    node_id="t", plugin_name="test-trigger"
                ),
            ],
        )
        executor.execute(wf)
        assert len(cm.active_contexts) == 0
