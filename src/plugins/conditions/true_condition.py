"""Always true condition plugin."""

from typing import Any

from src.core.contracts import ConditionPlugin
from src.core.manifest import PluginManifest, PluginType


class TrueCondition(ConditionPlugin):
    """Condition that always evaluates to True."""

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Always returns True."""
        return True

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="true-condition",
            version="1.0.0",
            description="Always returns True.",
            plugin_type=PluginType.CONDITION,
        )
