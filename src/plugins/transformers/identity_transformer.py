"""Passthrough transformer plugin."""

from typing import Any

from src.core.contracts import TransformerPlugin
from src.core.manifest import PluginManifest, PluginType


class IdentityTransformer(TransformerPlugin):
    """Transformer that returns the input data unchanged (identity function)."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="identity-transformer",
            version="1.0.0",
            description="Returns input data unchanged (identity function).",
            plugin_type=PluginType.TRANSFORMER,
        )

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        # Return a copy to avoid accidental mutation of the original data.
        return dict(data)
