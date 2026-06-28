"""Execution Context strategy (ADR-006).

Provides per-plugin-instance isolation boundaries. The ContextManager provisions
and destroys contexts, delegating authorization to the IsolationService.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.core.isolation import IsolationService, PolicyIsolationService
from src.core.manifest import PluginManifest


class DefaultIsolationService:
    """Permissive isolation service for development/testing.

    Grants all requests. Production implementations should enforce policy.
    """

    def authorize(self, manifest: PluginManifest, resources: list[str]) -> bool:  # noqa: ARG002
        """Grant all authorization requests (permissive for dev/testing)."""
        return True


@dataclass(slots=True)
class ExecutionContext:
    """Per-plugin-instance execution boundary (ADR-006).

    Encapsulates the isolated runtime scope for a single plugin execution.
    Destroyed immediately after execution completes.
    """

    context_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    plugin_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    _active: bool = field(default=False, repr=False)

    @property
    def is_active(self) -> bool:
        """Whether this context is currently active."""
        return self._active

    def activate(self) -> None:
        """Mark this context as active."""
        self._active = True

    def destroy(self) -> None:
        """Deactivate and clear all metadata."""
        self._active = False
        self.metadata.clear()


class ContextManager:
    """Provisions and manages execution contexts (ADR-006).

    Single entry point for context requests; delegates authorization
    to the IsolationService before provisioning.
    """

    def __init__(self, isolation_service: IsolationService | None = None) -> None:
        """Initialize with an optional custom isolation service."""
        self._isolation_service: IsolationService = (
            isolation_service or PolicyIsolationService()
        )
        self._active_contexts: dict[str, ExecutionContext] = {}

    @property
    def active_contexts(self) -> dict[str, ExecutionContext]:
        """Return a snapshot of currently active contexts."""
        return dict(self._active_contexts)

    def provision(self, manifest: PluginManifest) -> ExecutionContext:
        """Request and provision an execution context for a plugin instance.

        Args:
            manifest: The plugin's manifest for authorization.

        Returns:
            An activated execution context.

        Raises:
            PermissionError: If the IsolationService denies authorization.
        """
        if not self._isolation_service.authorize(manifest, manifest.permissions):
            raise PermissionError(
                f"IsolationService denied context for plugin '{manifest.name}'."
            )

        ctx = ExecutionContext(plugin_name=manifest.name)
        ctx.activate()
        self._active_contexts[ctx.context_id] = ctx
        return ctx

    def destroy(self, context_id: str) -> None:
        """Destroy an execution context immediately after execution completes.

        Args:
            context_id: The ID of the context to destroy.
        """
        ctx = self._active_contexts.pop(context_id, None)
        if ctx is not None:
            ctx.destroy()
