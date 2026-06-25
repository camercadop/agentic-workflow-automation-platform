from typing import Any

from src.core.contracts import TransformerPlugin
from src.core.manifest import PluginManifest, PluginType


class ReplaceWithTransformer(TransformerPlugin):
    """Replaces a field's value using a lookup dictionary."""

    def __init__(self, field: str, mapping: dict[str, Any], default: Any = None):
        self.field = field
        self.mapping = mapping
        self.default = default

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="replace-with-transformer",
            version="1.0.0",
            description=f"Replaces values in '{self.field}' using lookup map",
            plugin_type=PluginType.TRANSFORMER,
        )

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Replace field value with mapped value from lookup dictionary."""
        # Work on a copy to avoid mutating original data
        result = dict(data)

        # Only transform if field exists in data
        if self.field in result:
            original_value = result[self.field]
            # Use mapping if value exists, otherwise use default
            result[self.field] = self.mapping.get(original_value, self.default)

        return result
