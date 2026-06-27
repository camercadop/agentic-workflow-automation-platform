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
        self.session = session

    @abstractmethod
    def get(self, entity_id: uuid.UUID) -> T | None: ...

    @abstractmethod
    def list(self) -> list[T]: ...

    @abstractmethod
    def create(self, entity: T) -> T: ...

    @abstractmethod
    def update(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, entity_id: uuid.UUID) -> None: ...
