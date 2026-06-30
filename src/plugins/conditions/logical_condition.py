"""Logical condition plugins — base class and logical operators."""

from abc import ABC, abstractmethod
from typing import Any

from src.core.contracts import ConditionPlugin
from src.core.manifest import PluginManifest, PluginType

__all__ = ["LogicalCondition", "AndCondition", "OrCondition", "NotCondition"]


class LogicalCondition(ConditionPlugin, ABC):
    """Base class for logical operations (AND, OR, NOT)."""

    @abstractmethod
    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate the logical condition against input data."""
        raise NotImplementedError


class AndCondition(LogicalCondition):
    """Condition that passes if all sub-conditions pass."""

    def __init__(self, conditions: list[ConditionPlugin] | None = None) -> None:
        """Initialize with a list of conditions to AND together.

        Args:
            conditions: A list of ConditionPlugin instances to evaluate.
        """
        self._conditions = conditions or []

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="and-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Return True if all conditions evaluate to True.

        Args:
            data: The input payload to evaluate.

        Returns:
            True if all sub-conditions are True, or if no conditions are provided.
        """
        return all(condition.evaluate(data) for condition in self._conditions)


class OrCondition(LogicalCondition):
    """Condition that passes if any sub-condition passes."""

    def __init__(self, conditions: list[ConditionPlugin] | None = None) -> None:
        """Initialize with a list of conditions to OR together.

        Args:
            conditions: A list of ConditionPlugin instances to evaluate.
        """
        self._conditions = conditions or []

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="or-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Return True if any condition evaluates to True.

        Args:
            data: The input payload to evaluate.

        Returns:
            True if at least one sub-condition is True, False otherwise.
        """
        return any(condition.evaluate(data) for condition in self._conditions)


class NotCondition(LogicalCondition):
    """Condition that passes if the wrapped condition fails."""

    def __init__(self, condition: ConditionPlugin | None = None) -> None:
        """Initialize with a single condition to negate.

        Args:
            condition: The ConditionPlugin instance to negate.
        """
        self._condition = condition

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="not-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Return True if the wrapped condition evaluates to False.

        Args:
            data: The input payload to evaluate.

        Returns:
            True if the wrapped condition is False or None, False otherwise.
        """
        if self._condition is None:
            return True
        return not self._condition.evaluate(data)
