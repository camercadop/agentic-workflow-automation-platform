"""Build-time validation gates (ADR-009).

This module defines the five governance gates that every plugin and workflow
must pass before entering the registry:

- ManifestValidationGate: Ensures manifest metadata is complete and well-formed.
- ContractValidationGate: Verifies a plugin subclasses the correct contract type.
- SecurityValidationGate: Checks permission declarations for format and uniqueness.
- ExecutionContextValidationGate: Validates declared resource requirements.
- WorkflowValidationGate: Validates DAG structure and port/type compatibility.

Each gate returns a list of error strings; an empty list means the gate passed.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.manifest import PluginType

if TYPE_CHECKING:
    from src.core.contracts import PluginBase
    from src.core.workflow import WorkflowDefinition

# Semver pattern
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Expected contract base class per plugin type
_TYPE_CONTRACT_MAP: dict[PluginType, type] = {
    PluginType.TRIGGER: TriggerPlugin,
    PluginType.CONDITION: ConditionPlugin,
    PluginType.TRANSFORMER: TransformerPlugin,
    PluginType.ACTION: ActionPlugin,
}


class ValidationGate(ABC):
    """Abstract base for all validation gates."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable gate name."""

    @abstractmethod
    def validate_plugin(self, plugin: PluginBase) -> list[str]:
        """Validate a plugin; return list of errors (empty = pass)."""


class ManifestValidationGate(ValidationGate):
    """Validates plugin manifest schema and metadata completeness (ADR-002)."""

    @property
    def name(self) -> str:
        """Human-readable gate name."""
        return "Manifest Validation Gate"

    def validate_plugin(self, plugin: PluginBase) -> list[str]:
        """Check manifest fields for completeness and format."""
        errors: list[str] = []
        manifest = plugin.manifest

        if not manifest.name.strip():
            errors.append("Manifest 'name' must not be empty or blank.")

        if not _SEMVER_RE.match(manifest.version):
            errors.append(
                f"Manifest 'version' must be semver (got '{manifest.version}')."
            )

        if not manifest.plugin_type:
            errors.append("Manifest 'plugin_type' is required.")

        return errors


class ContractValidationGate(ValidationGate):
    """Validates plugin contract compliance (ADR-003, ADR-005)."""

    @property
    def name(self) -> str:
        """Human-readable gate name."""
        return "Contract Validation Gate"

    def validate_plugin(self, plugin: PluginBase) -> list[str]:
        """Verify plugin subclasses the correct contract type."""
        errors: list[str] = []
        manifest = plugin.manifest

        # Plugin must subclass the correct contract type
        expected_cls = _TYPE_CONTRACT_MAP.get(manifest.plugin_type)
        if expected_cls and not isinstance(plugin, expected_cls):
            errors.append(
                f"Plugin declares type '{manifest.plugin_type}' but does not "
                f"subclass {expected_cls.__name__}."
            )

        return errors


class SecurityValidationGate(ValidationGate):
    """Validates permission declarations and isolation compliance (ADR-004)."""

    @property
    def name(self) -> str:
        """Human-readable gate name."""
        return "Security Validation Gate"

    def validate_plugin(self, plugin: PluginBase) -> list[str]:
        """Check permission format and uniqueness."""
        errors: list[str] = []
        manifest = plugin.manifest

        # Permissions must be well-formed (colon-separated descriptors)
        for i, perm in enumerate(manifest.permissions):
            if not perm.strip():
                errors.append(f"Permission at index {i} must not be blank.")
            elif ":" not in perm:
                errors.append(f"Permission '{perm}' must use 'scope:resource' format.")

        # Plugins must not declare conflicting permissions
        seen: set[str] = set()
        for perm in manifest.permissions:
            if perm in seen:
                errors.append(f"Duplicate permission declared: '{perm}'.")
            seen.add(perm)

        return errors


class ExecutionContextValidationGate(ValidationGate):
    """Validates declared execution context requirements (ADR-006)."""

    @property
    def name(self) -> str:
        """Human-readable gate name."""
        return "Execution Context Validation Gate"

    def validate_plugin(self, plugin: PluginBase) -> list[str]:
        """Validate resource requirement declarations in metadata."""
        errors: list[str] = []
        manifest = plugin.manifest

        # If plugin declares resource requirements in metadata, validate them
        resources = manifest.metadata.get("resource_requirements", {})
        if not isinstance(resources, dict):
            errors.append("'resource_requirements' in metadata must be a dict.")
            return errors

        max_memory = resources.get("max_memory_mb")
        if max_memory is not None and (
            not isinstance(max_memory, int | float) or max_memory <= 0
        ):
            errors.append("'max_memory_mb' must be a positive number.")

        max_threads = resources.get("max_threads")
        if max_threads is not None and (
            not isinstance(max_threads, int) or max_threads <= 0
        ):
            errors.append("'max_threads' must be a positive integer.")

        timeout_seconds = resources.get("timeout_seconds")
        if timeout_seconds is not None and (
            not isinstance(timeout_seconds, int | float) or timeout_seconds <= 0
        ):
            errors.append("'timeout_seconds' must be a positive number.")

        return errors


class WorkflowValidationGate:
    """Validates workflow DAG structure and plugin compatibility (ADR-007)."""

    @property
    def name(self) -> str:
        """Human-readable gate name."""
        return "Workflow Validation Gate"

    def validate_workflow(
        self,
        workflow: WorkflowDefinition,
        registered_plugins: dict[str, PluginBase],
    ) -> list[str]:
        """Validate workflow against registered plugins.

        Args:
            workflow: The workflow definition to validate.
            registered_plugins: Available plugins keyed by name.

        Returns:
            A list of error strings (empty means valid).
        """
        errors: list[str] = []

        # Plugin existence check
        for node in workflow.nodes:
            if node.plugin_name not in registered_plugins:
                errors.append(
                    f"Node '{node.node_id}' references unregistered plugin "
                    f"'{node.plugin_name}'."
                )

        # Port compatibility check on edges
        for edge in workflow.edges:
            source_node = next(
                (n for n in workflow.nodes if n.node_id == edge.source_node), None
            )
            target_node = next(
                (n for n in workflow.nodes if n.node_id == edge.target_node), None
            )
            if not source_node or not target_node:
                continue

            source_plugin = registered_plugins.get(source_node.plugin_name)
            target_plugin = registered_plugins.get(target_node.plugin_name)
            if not source_plugin or not target_plugin:
                continue

            # Validate source port exists in outputs
            source_ports = {p.name for p in source_plugin.manifest.outputs}
            if source_ports and edge.source_port not in source_ports:
                errors.append(
                    f"Edge source port '{edge.source_port}' not declared in "
                    f"plugin '{source_node.plugin_name}' outputs."
                )

            # Validate target port exists in inputs
            target_ports = {p.name for p in target_plugin.manifest.inputs}
            if target_ports and edge.target_port not in target_ports:
                errors.append(
                    f"Edge target port '{edge.target_port}' not declared in "
                    f"plugin '{target_node.plugin_name}' inputs."
                )

            # Type compatibility check
            if edge.data_type != "any" and source_plugin and target_plugin:
                src_schema = next(
                    (
                        p
                        for p in source_plugin.manifest.outputs
                        if p.name == edge.source_port
                    ),
                    None,
                )
                tgt_schema = next(
                    (
                        p
                        for p in target_plugin.manifest.inputs
                        if p.name == edge.target_port
                    ),
                    None,
                )
                if (
                    src_schema
                    and tgt_schema
                    and src_schema.data_type != tgt_schema.data_type
                ):
                    errors.append(
                        f"Type mismatch on edge "
                        f"{edge.source_node}.{edge.source_port}"
                        f" -> {edge.target_node}"
                        f".{edge.target_port}: "
                        f"'{src_schema.data_type}' != "
                        f"'{tgt_schema.data_type}'."
                    )

        return errors
