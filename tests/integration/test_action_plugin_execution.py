"""Integration test for an ActionPlugin (using LogAction)."""

import logging

from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowNode
from src.plugins.actions.log_action import LogAction


def test_action_plugin_execution(caplog) -> None:
    """Action returns the input data unchanged and logs the payload."""
    registry = PluginRegistry()
    action = LogAction()
    registry.register(action)
    registry.activate("log-action")
    registry.mark_active("log-action")

    wf = WorkflowDefinition(
        name="action-integration-test",
        nodes=[WorkflowNode(node_id="act", plugin_name="log-action")],
    )

    executor = WorkflowExecutor(registry, ContextManager())
    input_data = {"key": "value", "number": 42}
    with caplog.at_level(logging.INFO):
        result = executor.execute(wf, initial_data=input_data)

    # Action should return the same data
    assert result["act"] == input_data

    # Check that the log message was recorded
    assert any("LogAction received" in record.message for record in caplog.records)
    # Optionally, check that the logged data matches the input
    # The log record's args contain the data; we can verify if needed.
