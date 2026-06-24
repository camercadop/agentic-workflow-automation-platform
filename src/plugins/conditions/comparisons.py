"""Comparison condition plugins — abstract base and concrete implementations."""

from abc import abstractmethod
from typing import Any

from src.core.contracts import ConditionPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin


class ComparisonCondition(ConditionPlugin):
    """Base class for conditions that compare a key's value against a target."""

    def __init__(self, key: str = "", value: Any = None) -> None:
        self._key = key
        self._value = value

    @abstractmethod
    def compare(self, actual: Any, expected: Any) -> bool:
        """Perform the comparison."""

    def evaluate(self, data: dict[str, Any]) -> bool:
        return self.compare(data.get(self._key), self._value)


@register_plugin
class GreaterThan(ComparisonCondition):
    """Condition that passes if key's value is greater than target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="greater-than-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual > expected)


@register_plugin
class LessThan(ComparisonCondition):
    """Condition that passes if key's value is less than target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="less-than-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual < expected)


@register_plugin
class Equal(ComparisonCondition):
    """Condition that passes if key's value equals target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="equal-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual == expected)


@register_plugin
class NotEqual(ComparisonCondition):
    """Condition that passes if key's value does not equal target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="not-equal-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual != expected)


@register_plugin
class GreaterOrEqualThan(ComparisonCondition):
    """Condition that passes if key's value is greater than or equal to target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="greater-or-equal-than-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual >= expected)


@register_plugin
class LessOrEqualThan(ComparisonCondition):
    """Condition that passes if key's value is less than or equal to target."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="less-or-equal-than-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Any, expected: Any) -> bool:
        return bool(actual <= expected)
