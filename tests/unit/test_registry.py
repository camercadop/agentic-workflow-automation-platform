"""Unit tests for plugin registry and lifecycle management (ADR-002, ADR-003)."""

from typing import Any

import pytest
from src.core.contracts import ActionPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registry import (
    LifecycleError,
    LifecycleState,
    PluginRegistry,
)


class _StubAction(ActionPlugin):
    """Minimal action plugin for testing."""

    def __init__(self, name: str = "stub-action") -> None:
        self._name = name
        self.activated = False
        self.deactivated = False
        self.cleaned = False

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self._name,
            version="1.0.0",
            plugin_type=PluginType.ACTION,
        )

    def on_activate(self) -> None:
        self.activated = True

    def on_deactivate(self) -> None:
        self.deactivated = True

    def on_cleanup(self) -> None:
        self.cleaned = True

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"done": True}


class TestPluginRegistration:
    def test_register_and_get(self) -> None:
        registry = PluginRegistry()
        plugin = _StubAction()
        registry.register(plugin)

        entry = registry.get("stub-action")
        assert entry.plugin is plugin
        assert entry.state == LifecycleState.REGISTERED

    def test_duplicate_registration_raises(self) -> None:
        registry = PluginRegistry()
        registry.register(_StubAction())
        with pytest.raises(ValueError, match="already registered"):
            registry.register(_StubAction())

    def test_get_unknown_plugin_raises(self) -> None:
        registry = PluginRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_plugins_property_returns_copy(self) -> None:
        registry = PluginRegistry()
        registry.register(_StubAction())
        plugins = registry.plugins
        plugins.clear()
        assert len(registry.plugins) == 1


class TestLifecycleTransitions:
    def test_full_lifecycle(self) -> None:
        registry = PluginRegistry()
        plugin = _StubAction()
        registry.register(plugin)

        registry.activate("stub-action")
        assert registry.get("stub-action").state == LifecycleState.ACTIVATED
        assert plugin.activated is True

        registry.mark_active("stub-action")
        assert registry.get("stub-action").state == LifecycleState.ACTIVE

        registry.deactivate("stub-action")
        assert registry.get("stub-action").state == LifecycleState.DEACTIVATED
        assert plugin.deactivated is True

        registry.cleanup("stub-action")
        assert registry.get("stub-action").state == LifecycleState.CLEANED_UP
        assert plugin.cleaned is True

    def test_invalid_transition_raises(self) -> None:
        registry = PluginRegistry()
        registry.register(_StubAction())

        with pytest.raises(LifecycleError):
            registry.mark_active("stub-action")  # Must activate first

    def test_cannot_activate_twice(self) -> None:
        registry = PluginRegistry()
        registry.register(_StubAction())
        registry.activate("stub-action")

        with pytest.raises(LifecycleError):
            registry.activate("stub-action")

    def test_cannot_deactivate_from_registered(self) -> None:
        registry = PluginRegistry()
        registry.register(_StubAction())

        with pytest.raises(LifecycleError):
            registry.deactivate("stub-action")
