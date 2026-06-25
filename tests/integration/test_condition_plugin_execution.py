"""Integration test for a ConditionPlugin (using TrueCondition)."""

from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowNode
from src.plugins.conditions.true_condition import TrueCondition


def test_condition_plugin_execution() -> None:
    """TrueCondition always returns True."""
    registry = PluginRegistry()
    condition = TrueCondition()
    registry.register(condition)
    registry.activate("true-condition")
    registry.mark_active("true-condition")

    wf = WorkflowDefinition(
        name="condition-integration-test",
        nodes=[WorkflowNode(node_id="cond", plugin_name="true-condition")],
    )

    executor = WorkflowExecutor(registry, ContextManager())
    result = executor.execute(wf, initial_data={})  # input doesn't matter

    assert result["cond"]["result"] is True
