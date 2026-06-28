"""Log action plugin — outputs received data to the logger."""

import logging
from typing import Any

from src.core.contracts import ActionPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class LogAction(ActionPlugin):
    """Action that logs the incoming data and returns it unchanged."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="log-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            permissions=[],
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Log and return the received data."""
        logger.info("LogAction received: %s", data)
        return data
