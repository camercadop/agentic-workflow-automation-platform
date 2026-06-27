"""Generic CRUD repository implementation."""

from types import get_original_bases
from typing import get_args

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.repositories.base.repository import BaseRepository


class CrudRepository[T](BaseRepository[T]):
    """Provides default CRUD implementations.

    Subclasses only need to declare the type parameter; the SQLAlchemy model
    class is resolved automatically at instantiation via PEP 695 introspection.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session)

        # Walk the MRO's original generic bases to extract the concrete model
        # class bound to T, avoiding the need for explicit model declarations
        # in each subclass.
        for base in get_original_bases(type(self)):
            args = get_args(base)
            if args:
                self._model = args[0]
                break

    def get(self, entity_id: str) -> T | None:
        return self.session.get(self._model, entity_id)

    def list(self) -> list[T]:
        return list(self.session.execute(select(self._model)).scalars().all())

    def create(self, entity: T) -> T:
        """Persist entity and refresh to populate server-generated fields."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

    def update(self, entity: T) -> T:
        """Merge, commit, and refresh the entity."""
        merged = self.session.merge(entity)
        self.session.commit()
        self.session.refresh(merged)

        return merged

    def delete(self, entity_id: str) -> None:
        """Delete entity by ID. Raises if not found."""
        entity = self.session.get(self._model, entity_id)
        if entity is None:
            raise ValueError(f"{self._model.__name__} with id '{entity_id}' not found.")
        self.session.delete(entity)
        self.session.commit()
