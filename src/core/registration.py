"""Decorator-based plugin registration (ADR-002 — inline annotations)."""

from src.core.contracts import PluginBase

_COLLECTED: dict[str, type[PluginBase]] = {}


def register_plugin(cls: type[PluginBase]) -> type[PluginBase]:
    """Mark a PluginBase subclass for build-time registry collection."""
    if not (isinstance(cls, type) and issubclass(cls, PluginBase)):
        raise TypeError(f"@register_plugin requires a PluginBase subclass, got {cls}")
    manifest = cls().manifest
    key = f"{manifest.name}:{manifest.plugin_type}"
    if key in _COLLECTED:
        raise ValueError(f"Duplicate plugin registration: '{key}'")
    _COLLECTED[key] = cls
    return cls


def get_collected_plugins() -> dict[str, type[PluginBase]]:
    """Return all decorator-collected plugin classes (used by Registry Builder)."""
    return dict(_COLLECTED)


def clear_collected() -> None:
    """Reset collected plugins (for testing)."""
    _COLLECTED.clear()
