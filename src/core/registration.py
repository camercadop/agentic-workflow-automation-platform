"""Decorator-based plugin registration (ADR-002 — inline annotations)."""

from src.core.contracts import PluginBase

_COLLECTED: dict[str, type[PluginBase]] = {}


def register_plugin(cls: type[PluginBase]) -> type[PluginBase]:
    """Mark a PluginBase subclass for build-time registry collection.

    Args:
        cls: The plugin class to register.

    Returns:
        The same class, unmodified.

    Raises:
        TypeError: If cls is not a PluginBase subclass.
        ValueError: If a plugin with the same name and type is already registered.
    """
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
