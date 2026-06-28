"""Manual trigger plugin for testing and workflow entry."""

from typing import Any

from src.core.contracts import TriggerPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin


@register_plugin
class ManualTrigger(TriggerPlugin):
    """Simple trigger that returns a configurable static payload.

    Ideal for testing without external I/O dependencies.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize with optional static configuration."""
        self._config = config or {}

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="manual-trigger",
            version="1.0.0",
            plugin_type=PluginType.TRIGGER,
            permissions=[],
        )

    def check(self) -> dict[str, Any]:
        """Return a static event payload."""
        return {"event": "manual", "payload": self._config.get("data", {})}
