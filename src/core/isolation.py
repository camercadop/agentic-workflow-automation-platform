"""Isolation service implementations (ADR-004).

Implements the authorization authority for execution context provisioning
as mandated by ADR-006. Validates resource access requests against the
plugin's declared manifest permissions.
"""

from __future__ import annotations

from typing import Protocol

from src.core.manifest import PluginManifest


class IsolationService(Protocol):
    """Authorization authority for execution context provisioning (ADR-004)."""

    def authorize(self, manifest: PluginManifest, resources: list[str]) -> bool:
        """Evaluate whether the plugin is allowed the requested resources."""
        ...


class PolicyIsolationService:
    """Manifest-based isolation service enforcing per-plugin access control.

    Validates that each requested resource is declared in the plugin's
    manifest permissions. Undeclared resources are denied.
    """

    def authorize(self, manifest: PluginManifest, resources: list[str]) -> bool:
        """Validate each requested resource against the manifest permissions."""
        return all(resource in manifest.permissions for resource in resources)


class DefaultIsolationService:
    """Permissive isolation service for development/testing.

    Grants all requests. Production implementations should use PolicyIsolationService.
    """

    def authorize(self, manifest: PluginManifest, resources: list[str]) -> bool:  # noqa: ARG002
        """Grant all authorization requests (permissive for dev/testing)."""
        return True
