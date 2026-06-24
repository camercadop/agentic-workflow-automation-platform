from typing import Any

import pytest
from src.core.contracts import ActionPlugin, TriggerPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import (
    clear_collected,
    get_collected_plugins,
    register_plugin,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_collected()
    yield
    clear_collected()


class TestRegisterPlugin:
    def test_registers_plugin(self) -> None:
        @register_plugin
        class MyAction(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="my-action", version="1.0.0", plugin_type=PluginType.ACTION
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return data

        collected = get_collected_plugins()
        assert "my-action:action" in collected
        assert collected["my-action:action"] is MyAction

    def test_duplicate_raises(self) -> None:
        @register_plugin
        class First(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="dup", version="1.0.0", plugin_type=PluginType.ACTION
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return data

        with pytest.raises(ValueError, match="Duplicate plugin registration"):

            @register_plugin
            class Second(ActionPlugin):
                @property
                def manifest(self) -> PluginManifest:
                    return PluginManifest(
                        name="dup", version="1.0.0", plugin_type=PluginType.ACTION
                    )

                def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                    return data

    def test_same_name_different_type_allowed(self) -> None:
        @register_plugin
        class AsAction(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="multi", version="1.0.0", plugin_type=PluginType.ACTION
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return data

        @register_plugin
        class AsTrigger(TriggerPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="multi", version="1.0.0", plugin_type=PluginType.TRIGGER
                )

            def check(self) -> dict[str, Any]:
                return {}

        collected = get_collected_plugins()
        assert "multi:action" in collected
        assert "multi:trigger" in collected

    def test_rejects_non_plugin_class(self) -> None:
        with pytest.raises(TypeError, match="requires a PluginBase subclass"):
            register_plugin(str)  # type: ignore[arg-type]

    def test_clear_resets(self) -> None:
        @register_plugin
        class Temp(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="temp", version="1.0.0", plugin_type=PluginType.ACTION
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return data

        assert len(get_collected_plugins()) == 1
        clear_collected()
        assert len(get_collected_plugins()) == 0
