"""Application bootstrap — builds a live PluginRegistry at startup (ADR-002)."""

import importlib
import pkgutil

import src.plugins
from src.core.context import ContextManager
from src.core.registration import get_collected_plugins
from src.core.registry import PluginRegistry


def _discover_plugin_modules() -> None:
    """Import all plugin submodules to trigger @register_plugin collection."""
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        src.plugins.__path__, prefix="src.plugins."
    ):
        importlib.import_module(modname)


def build_registry() -> tuple[PluginRegistry, ContextManager]:
    """Discover plugins, instantiate, register, and activate them.

    Returns a fully-populated PluginRegistry and ContextManager ready for use.
    """
    _discover_plugin_modules()

    registry = PluginRegistry()
    for _key, cls in get_collected_plugins().items():
        instance = cls()
        registry.register(instance)
        name = instance.manifest.name
        registry.activate(name)
        registry.mark_active(name)

    return registry, ContextManager()
