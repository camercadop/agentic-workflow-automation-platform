"""Base repository class for database operations."""

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class BaseRepository[T](ABC):
    """Base repository class."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @abstractmethod
    def get(self, entity_id: str) -> T | None:
        """Get entity by ID."""
        pass

    @abstractmethod
    def list(self) -> list[T]:
        """List all entities."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        pass
