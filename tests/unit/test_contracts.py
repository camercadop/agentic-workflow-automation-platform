"""Unit tests for plugin contracts and manifest model."""

from typing import Any

import pytest
from pydantic import ValidationError
from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    PluginBase,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.manifest import PluginManifest, PluginType, PortSchema


class TestPluginBaseAbstract:
    """Verify abstract classes cannot be instantiated directly."""

    def test_plugin_base_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            PluginBase()  # type: ignore[abstract]

    def test_trigger_plugin_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            TriggerPlugin()  # type: ignore[abstract]

    def test_condition_plugin_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            ConditionPlugin()  # type: ignore[abstract]

    def test_transformer_plugin_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            TransformerPlugin()  # type: ignore[abstract]

    def test_action_plugin_not_instantiable(self) -> None:
        with pytest.raises(TypeError):
            ActionPlugin()  # type: ignore[abstract]


class TestConcretePlugin:
    """Verify concrete implementations work correctly."""

    def test_concrete_trigger(self) -> None:
        class MyTrigger(TriggerPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="my-trigger",
                    version="1.0.0",
                    plugin_type=PluginType.TRIGGER,
                    contract_version="1.0.0",
                )

            def check(self) -> dict[str, Any]:
                return {"fired": True}

        t = MyTrigger()
        assert t.check() == {"fired": True}
        assert t.manifest.plugin_type == PluginType.TRIGGER

    def test_concrete_condition(self) -> None:
        class MyCondition(ConditionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="my-condition",
                    version="1.0.0",
                    plugin_type=PluginType.CONDITION,
                    contract_version="1.0.0",
                )

            def evaluate(self, data: dict[str, Any]) -> bool:
                return data.get("priority") == "high"

        c = MyCondition()
        assert c.evaluate({"priority": "high"}) is True
        assert c.evaluate({"priority": "low"}) is False

    def test_concrete_transformer(self) -> None:
        class MyTransformer(TransformerPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="my-transformer",
                    version="1.0.0",
                    plugin_type=PluginType.TRANSFORMER,
                    contract_version="1.0.0",
                )

            def transform(self, data: dict[str, Any]) -> dict[str, Any]:
                return {**data, "transformed": True}

        t = MyTransformer()
        assert t.transform({"x": 1}) == {"x": 1, "transformed": True}

    def test_concrete_action(self) -> None:
        class MyAction(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="my-action",
                    version="1.0.0",
                    plugin_type=PluginType.ACTION,
                    contract_version="1.0.0",
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return {"status": "done"}

        a = MyAction()
        assert a.execute({}) == {"status": "done"}


class TestPluginManifest:
    """Verify manifest validation."""

    def test_valid_manifest(self) -> None:
        m = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            contract_version="1.0.0",
            capabilities=["send-email"],
            inputs=[PortSchema(name="payload", data_type="dict")],
            outputs=[PortSchema(name="result", data_type="dict")],
        )
        assert m.name == "test-plugin"
        assert m.plugin_type == PluginType.ACTION
        assert len(m.inputs) == 1

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PluginManifest(
                name="",
                version="1.0.0",
                plugin_type=PluginType.ACTION,
                contract_version="1.0.0",
            )

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            PluginManifest()  # type: ignore[call-arg]

    def test_invalid_plugin_type(self) -> None:
        with pytest.raises(ValidationError):
            PluginManifest(
                name="test",
                version="1.0.0",
                plugin_type="invalid",  # type: ignore[arg-type]
                contract_version="1.0.0",
            )
