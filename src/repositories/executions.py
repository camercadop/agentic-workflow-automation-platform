"""Workflow execution repository implementation."""

from src.models.execution import WorkflowExecution
from src.repositories.base import CrudRepository


class WorkflowExecutionRepository(CrudRepository[WorkflowExecution]):
    """Workflow execution repository."""
