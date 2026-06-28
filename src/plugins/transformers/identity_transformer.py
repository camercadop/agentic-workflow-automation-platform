"""Passthrough transformer plugin."""

from typing import Any

from src.core.contracts import TransformerPlugin
from src.core.manifest import PluginManifest, PluginType


class IdentityTransformer(TransformerPlugin):
    """Transformer that returns the input data unchanged (identity function)."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="identity-transformer",
            version="1.0.0",
            description="Returns input data unchanged (identity function).",
            plugin_type=PluginType.TRANSFORMER,
        )

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of the input data unchanged."""
        return dict(data)
