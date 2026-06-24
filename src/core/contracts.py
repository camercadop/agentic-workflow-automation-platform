"""Abstract plugin contracts (ADR-003, ADR-005).

Defines the base plugin interface and typed subclasses for
Trigger, Condition, Transformer, and Action plugins.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.core.manifest import PluginManifest


class PluginBase(ABC):
    """Base contract for all plugins.

    Lifecycle hooks are optional (ADR-003): override only the ones you need.
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin's manifest metadata."""

    # Optional lifecycle hooks (ADR-003)
    def on_activate(self) -> None:  # noqa: B027
        """Called when transitioning to Activated state."""

    def on_deactivate(self) -> None:  # noqa: B027
        """Called when transitioning to Deactivated state."""

    def on_cleanup(self) -> None:  # noqa: B027
        """Called when transitioning to Cleaned Up state."""


class TriggerPlugin(PluginBase):
    """Plugin that initiates workflow execution in response to events."""

    @abstractmethod
    def check(self) -> dict[str, Any]:
        """Check for trigger condition; return trigger payload if fired."""


class ConditionPlugin(PluginBase):
    """Plugin that evaluates data to determine processing paths."""

    @abstractmethod
    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate condition against input data."""


class TransformerPlugin(PluginBase):
    """Plugin that modifies data as it flows through the workflow."""

    @abstractmethod
    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform input data and return modified output."""


class ActionPlugin(PluginBase):
    """Plugin that performs external operations or produces outcomes."""

    @abstractmethod
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute action with input data; return result."""
