"""Base repository class for database operations."""

import uuid
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class BaseRepository[T](ABC):
    """Generic repository abstraction that decouples domain logic from persistence.

    Type parameter T represents the domain entity managed by the concrete repository.
    Subclasses are responsible for mapping between domain entities and ORM models.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with a database session.

        Args:
            session: The SQLAlchemy session for database operations.
        """
        self.session = session

    @abstractmethod
    def get(self, entity_id: uuid.UUID) -> T | None:
        """Retrieve entity by ID.

        Args:
            entity_id: The entity's UUID.
        """
        ...

    @abstractmethod
    def list(self) -> list[T]:
        """Return all entities."""
        ...

    @abstractmethod
    def create(self, entity: T) -> T:
        """Persist a new entity.

        Args:
            entity: The entity to persist.
        """
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: The entity with updated fields.
        """
        ...

    @abstractmethod
    def delete(self, entity_id: uuid.UUID) -> None:
        """Delete entity by ID.

        Args:
            entity_id: The entity's UUID.
        """
        ...
