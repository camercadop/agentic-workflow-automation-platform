"""Workflow repository implementation."""

from src.models.workflow import Workflow
from src.repositories.base import CrudRepository


class WorkflowRepository(CrudRepository[Workflow]):
    """Workflow repository."""
