"""Integration test for a TransformerPlugin (using IdentityTransformer)."""

from src.core.context import ContextManager
from src.core.executor import WorkflowExecutor
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowNode
from src.plugins.transformers.identity_transformer import IdentityTransformer


def test_transformer_plugin_execution() -> None:
    """Transformer returns the input data unchanged."""
    registry = PluginRegistry()
    transformer = IdentityTransformer()
    registry.register(transformer)
    registry.activate("identity-transformer")
    registry.mark_active("identity-transformer")

    wf = WorkflowDefinition(
        name="transformer-integration-test",
        nodes=[WorkflowNode(node_id="tx", plugin_name="identity-transformer")],
    )

    executor = WorkflowExecutor(registry, ContextManager())
    result = executor.execute(wf, initial_data={"status": 404, "payload": "data"})

    assert result["tx"]["status"] == 404
    assert result["tx"]["payload"] == "data"


# (The test_transformer_plugin_uses_default function is no longer applicable for IdentityTransformer and has been removed)
