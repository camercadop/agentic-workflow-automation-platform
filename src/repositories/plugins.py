"""Plugin repository implementation using SQLModel."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.plugin import Plugin
from src.repositories.base import BaseRepository


class PluginRepository(BaseRepository[Plugin]):
    """Plugin repository implementation."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.session = session

    def get(self, identity_id: str) -> Plugin | None:
        """Get plugin by ID."""

        return self.session.get(Plugin, identity_id)

    def list(self) -> list[Plugin]:
        """List all plugins."""

        stmt = select(Plugin)

        return list(self.session.execute(stmt).scalars().all())

    def create(self, plugin: Plugin) -> Plugin:
        """Create new plugin in database."""

        self.session.add(plugin)
        self.session.commit()
        self.session.refresh(plugin)

        return plugin
