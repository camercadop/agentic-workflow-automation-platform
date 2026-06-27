"""Base repository infrastructure."""

from src.repositories.base.crud import CrudRepository
from src.repositories.base.repository import BaseRepository

__all__ = ["BaseRepository", "CrudRepository"]
