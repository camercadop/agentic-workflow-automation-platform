"""String condition plugins — abstract base and concrete implementations."""

import re
from abc import abstractmethod
from typing import Any

from src.core.contracts import ConditionPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin


class StringCondition(ConditionPlugin):
    """Base class for conditions that perform string operations on a key's value."""

    def __init__(self, key: str = "", value: str = "") -> None:
        """Initialize with key to extract from data and the target string value."""
        self._key = key
        self._value = value

    @abstractmethod
    def compare(self, actual: str, expected: str) -> bool:
        """Perform the string comparison."""

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate the condition against the data."""
        actual_value = data.get(self._key)
        if not isinstance(actual_value, str):
            return False
        return self.compare(actual_value, self._value)


@register_plugin
class StringContains(StringCondition):
    """Condition that passes if key's value contains the target substring."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="string-contains-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: str, expected: str) -> bool:
        """Return True if expected is in actual."""
        return expected in actual


@register_plugin
class StringStartsWith(StringCondition):
    """Condition that passes if key's value starts with the target prefix."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="string-starts-with-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: str, expected: str) -> bool:
        """Return True if actual starts with expected."""
        return actual.startswith(expected)


@register_plugin
class StringEndsWith(StringCondition):
    """Condition that passes if key's value ends with the target suffix."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="string-ends-with-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: str, expected: str) -> bool:
        """Return True if actual ends with expected."""
        return actual.endswith(expected)


@register_plugin
class StringRegexMatch(StringCondition):
    """Condition that passes if key's value matches the target regex pattern."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="string-regex-match-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: str, expected: str) -> bool:
        """Return True if actual matches the regex pattern expected."""
        try:
            return bool(re.search(expected, actual))
        except re.error:
            return False
