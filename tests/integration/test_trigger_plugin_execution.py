"""Integration test for TriggerPlugin contract execution pipeline."""

from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowNode
from src.plugins.triggers.manual_trigger import ManualTrigger


def test_trigger_plugin_execution() -> None:
    # 1. Setup Registry and Plugin
    registry = PluginRegistry()
    trigger = ManualTrigger(config={"data": {"event_type": "test_manual"}})
    registry.register(trigger)
    registry.activate("manual-trigger")
    registry.mark_active("manual-trigger")

    # 2. Define a simple workflow with only the trigger
    wf = WorkflowDefinition(
        name="manual-integration-test",
        nodes=[WorkflowNode(node_id="start", plugin_name="manual-trigger")],
    )

    # 3. Execute
    executor = WorkflowExecutor(registry, ContextManager())
    results = executor.execute(wf)

    # 4. Assertions
    assert "start" in results
    assert results["start"]["event"] == "manual"
    assert results["start"]["payload"]["event_type"] == "test_manual"
