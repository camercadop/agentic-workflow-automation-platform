"""Integration tests for executor policy enforcement."""

import time
from typing import Any

import pytest

from src.core.context import ContextManager
from src.core.contracts import ActionPlugin, TriggerPlugin
from src.core.executor import WorkflowExecutor
from src.core.manifest import PluginManifest, PluginType
from src.core.policies import NodeExecutionError
from src.core.registration import register_plugin
from src.core.registry import PluginRegistry
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode


class _Trigger(TriggerPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="policy-trigger",
            version="1.0.0",
            plugin_type=PluginType.TRIGGER,
        )

    def check(self) -> dict[str, Any]:
        return {"event": "fired", "payload": {"key": "value"}}


class _FailingAction(ActionPlugin):
    """Always raises an error."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="failing-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("plugin crashed")


class _SlowAction(ActionPlugin):
    """Takes too long to execute."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="slow-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        time.sleep(0.2)  # Just enough to exceed the 0.05s timeout
        return {"done": True}


_call_count = 0


class _FlakyAction(ActionPlugin):
    """Fails the first N-1 times, succeeds on attempt N."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="flaky-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        global _call_count
        _call_count += 1
        if _call_count < 3:
            raise RuntimeError("transient error")
        return {"recovered": True}


class _SuccessAction(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="success-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "received": data}


def _make_registry(*plugins: Any) -> PluginRegistry:
    registry = PluginRegistry()
    for p in plugins:
        registry.register(p)
        registry.activate(p.manifest.name)
        registry.mark_active(p.manifest.name)
    return registry


class TestFailFastStrategy:
    def test_failing_node_aborts_workflow(self) -> None:
        registry = _make_registry(_Trigger(), _FailingAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="fail-fast-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="a",
                    plugin_name="failing-action",
                    config={"policy": {"error_strategy": "fail_fast"}},
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="data",
                ),
            ],
        )
        with pytest.raises(NodeExecutionError, match="Node 'a' failed"):
            executor.execute(wf)

    def test_default_strategy_is_fail_fast(self) -> None:
        registry = _make_registry(_Trigger(), _FailingAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="default-fail-fast",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(node_id="a", plugin_name="failing-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="data",
                ),
            ],
        )
        with pytest.raises(NodeExecutionError):
            executor.execute(wf)


class TestSkipNodeStrategy:
    def test_failed_node_is_skipped(self) -> None:
        registry = _make_registry(_Trigger(), _FailingAction(), _SuccessAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="skip-node-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="fail",
                    plugin_name="failing-action",
                    config={"policy": {"error_strategy": "skip_node"}},
                ),
                WorkflowNode(node_id="ok", plugin_name="success-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="fail",
                    target_port="data",
                ),
                WorkflowEdge(
                    source_node="fail",
                    source_port="result",
                    target_node="ok",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        # Trigger succeeds
        assert "t" in results
        # Failing node is skipped (not in results)
        assert "fail" not in results
        # Downstream node still executes (with no upstream data)
        assert "ok" in results


class TestContinueStrategy:
    def test_failed_node_continues_workflow(self) -> None:
        registry = _make_registry(_Trigger(), _FailingAction(), _SuccessAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="continue-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="fail",
                    plugin_name="failing-action",
                    config={"policy": {"error_strategy": "continue"}},
                ),
                WorkflowNode(node_id="ok", plugin_name="success-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="fail",
                    target_port="data",
                ),
                WorkflowEdge(
                    source_node="fail",
                    source_port="result",
                    target_node="ok",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert "t" in results
        assert "fail" not in results
        assert "ok" in results


class TestTimeoutPolicy:
    def test_slow_node_times_out(self) -> None:
        registry = _make_registry(_Trigger(), _SlowAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="timeout-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="slow",
                    plugin_name="slow-action",
                    config={
                        "policy": {
                            "timeout": {"timeout_seconds": 0.05},
                            "error_strategy": "skip_node",
                        }
                    },
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="slow",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert "t" in results
        assert "slow" not in results

    def test_slow_node_fail_fast_raises(self) -> None:
        registry = _make_registry(_Trigger(), _SlowAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="timeout-failfast",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="slow",
                    plugin_name="slow-action",
                    config={
                        "policy": {
                            "timeout": {"timeout_seconds": 0.05},
                            "error_strategy": "fail_fast",
                        }
                    },
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="slow",
                    target_port="data",
                ),
            ],
        )
        with pytest.raises(NodeExecutionError, match="Timed out"):
            executor.execute(wf)


class TestRetryPolicy:
    def test_retry_recovers_from_transient_failure(self) -> None:
        global _call_count
        _call_count = 0

        registry = _make_registry(_Trigger(), _FlakyAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="retry-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="flaky",
                    plugin_name="flaky-action",
                    config={
                        "policy": {
                            "retry": {"max_attempts": 3, "delay_seconds": 0.01},
                        }
                    },
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="flaky",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert results["flaky"] == {"recovered": True}

    def test_retry_exhaustion_with_skip(self) -> None:
        registry = _make_registry(_Trigger(), _FailingAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="retry-exhaust",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(
                    node_id="a",
                    plugin_name="failing-action",
                    config={
                        "policy": {
                            "retry": {"max_attempts": 2, "delay_seconds": 0.01},
                            "error_strategy": "skip_node",
                        }
                    },
                ),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert "t" in results
        assert "a" not in results


class TestNoPolicy:
    def test_nodes_without_policy_use_defaults(self) -> None:
        registry = _make_registry(_Trigger(), _SuccessAction())
        executor = WorkflowExecutor(registry, ContextManager())
        wf = WorkflowDefinition(
            name="no-policy",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="policy-trigger"),
                WorkflowNode(node_id="a", plugin_name="success-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="data",
                ),
            ],
        )
        results = executor.execute(wf)
        assert results["t"]["event"] == "fired"
        assert results["a"]["status"] == "ok"
