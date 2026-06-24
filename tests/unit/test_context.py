"""Unit tests for execution context strategy (ADR-006)."""

import pytest
from src.core.context import (
    ContextManager,
    DefaultIsolationService,
    ExecutionContext,
    IsolationService,
)
from src.core.manifest import PluginManifest, PluginType


def _make_manifest(name: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        name=name,
        version="1.0.0",
        plugin_type=PluginType.ACTION,
        contract_version="1.0.0",
        permissions=["file:/tmp/data"],
    )


class TestExecutionContext:
    def test_initial_state_inactive(self) -> None:
        ctx = ExecutionContext(plugin_name="p")
        assert ctx.is_active is False

    def test_activate(self) -> None:
        ctx = ExecutionContext(plugin_name="p")
        ctx.activate()
        assert ctx.is_active is True

    def test_destroy_clears_state(self) -> None:
        ctx = ExecutionContext(plugin_name="p", metadata={"k": "v"})
        ctx.activate()
        ctx.destroy()
        assert ctx.is_active is False
        assert ctx.metadata == {}

    def test_unique_context_ids(self) -> None:
        a = ExecutionContext(plugin_name="a")
        b = ExecutionContext(plugin_name="b")
        assert a.context_id != b.context_id


class TestContextManager:
    def test_provision_creates_active_context(self) -> None:
        cm = ContextManager()
        manifest = _make_manifest()
        ctx = cm.provision(manifest)
        assert ctx.is_active is True
        assert ctx.plugin_name == "test-plugin"
        assert ctx.context_id in cm.active_contexts

    def test_destroy_removes_context(self) -> None:
        cm = ContextManager()
        ctx = cm.provision(_make_manifest())
        cm.destroy(ctx.context_id)
        assert ctx.is_active is False
        assert ctx.context_id not in cm.active_contexts

    def test_destroy_unknown_id_is_noop(self) -> None:
        cm = ContextManager()
        cm.destroy("nonexistent")  # Should not raise

    def test_multiple_contexts_isolated(self) -> None:
        cm = ContextManager()
        ctx1 = cm.provision(_make_manifest("plugin-a"))
        ctx2 = cm.provision(_make_manifest("plugin-b"))
        assert ctx1.context_id != ctx2.context_id
        assert len(cm.active_contexts) == 2

    def test_denied_isolation_raises(self) -> None:
        class DenyAll:
            def authorize(
                self,
                manifest: PluginManifest,
                resources: list[str],
            ) -> bool:
                return False

        cm = ContextManager(isolation_service=DenyAll())
        with pytest.raises(PermissionError, match="denied"):
            cm.provision(_make_manifest())


class TestDefaultIsolationService:
    def test_grants_all_requests(self) -> None:
        svc = DefaultIsolationService()
        assert svc.authorize(_make_manifest(), ["file:/tmp"]) is True
