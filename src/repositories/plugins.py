"""Plugin repository implementation."""

from src.models.plugin import Plugin
from src.repositories.base import CrudRepository


class PluginRepository(CrudRepository[Plugin]):
    """Plugin repository."""
