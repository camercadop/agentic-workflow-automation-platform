"""Unit tests for ReplaceWithTransformer plugin."""

from typing import Any, Dict

from src.plugins.transformers.replace_with_transformer import ReplaceWithTransformer
from src.core.manifest import PluginType


class TestReplaceWithTransformer:
    """Tests for ReplaceWithTransformer plugin behavior."""

    def test_transform_replaces_known_value(self) -> None:
        transformer = ReplaceWithTransformer(
            field="status",
            mapping={200: "success", 404: "not_found"},
            default="unknown",
        )
        data: Dict[str, Any] = {"status": 200, "id": 123}
        result = transformer.transform(data)
        assert result["status"] == "success"
        assert result["id"] == 123  # Other fields unchanged

    def test_transform_uses_default_for_unknown_value(self) -> None:
        transformer = ReplaceWithTransformer(
            field="status", mapping={200: "success"}, default="unknown"
        )
        data: Dict[str, Any] = {"status": 500}
        result = transformer.transform(data)
        assert result["status"] == "unknown"

    def test_transform_skips_missing_field(self) -> None:
        transformer = ReplaceWithTransformer(
            field="status", mapping={200: "success"}, default="unknown"
        )
        data: Dict[str, Any] = {"id": 123}  # No 'status' field
        result = transformer.transform(data)
        assert result == data  # Unchanged

    def test_manifest_metadata(self) -> None:
        transformer = ReplaceWithTransformer(field="test", mapping={}, default=None)
        manifest = transformer.manifest
        assert manifest.name == "replace-with-transformer"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.TRANSFORMER
