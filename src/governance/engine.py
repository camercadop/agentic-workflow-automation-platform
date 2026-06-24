"""Validation Engine — orchestrates gates and produces reports (ADR-009).

The Validation Engine is a build-time component executed during CI/CD.
It runs all validation gates against plugin artifacts and workflows,
producing a report that determines registry inclusion eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contracts import PluginBase
    from src.core.workflow import WorkflowDefinition
    from src.governance.gates import ValidationGate


class ValidationResult(StrEnum):
    """Outcome of a single validation gate."""

    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True)
class GateResult:
    """Result from a single validation gate execution."""

    gate_name: str
    result: ValidationResult
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationReport:
    """Aggregated report from all validation gates."""

    artifact_name: str
    gate_results: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(gr.result == ValidationResult.PASSED for gr in self.gate_results)

    @property
    def errors(self) -> list[str]:
        errs: list[str] = []
        for gr in self.gate_results:
            errs.extend(gr.errors)
        return errs


class ValidationEngine:
    """Runs validation gates against artifacts and produces reports.

    Gates cannot be bypassed — all registered gates are executed for
    every artifact (ADR-009 mandatory rule).
    """

    def __init__(self, gates: list[ValidationGate] | None = None) -> None:
        from src.governance.gates import (
            ContractValidationGate,
            ExecutionContextValidationGate,
            ManifestValidationGate,
            SecurityValidationGate,
        )

        self._gates: list[ValidationGate] = gates or [
            ManifestValidationGate(),
            ContractValidationGate(),
            SecurityValidationGate(),
            ExecutionContextValidationGate(),
        ]

    def validate_plugin(self, plugin: PluginBase) -> ValidationReport:
        """Validate a plugin against all gates. All gates are always run."""
        results: list[GateResult] = []
        for gate in self._gates:
            errors = gate.validate_plugin(plugin)
            status = (
                ValidationResult.PASSED
                if not errors
                else ValidationResult.FAILED
            )
            results.append(
                GateResult(
                    gate_name=gate.name,
                    result=status,
                    errors=errors,
                )
            )
        return ValidationReport(
            artifact_name=plugin.manifest.name,
            gate_results=results,
        )

    def validate_workflow(
        self,
        workflow: WorkflowDefinition,
        registered_plugins: dict[str, PluginBase],
    ) -> ValidationReport:
        """Validate a workflow definition against workflow-aware gates."""
        from src.governance.gates import WorkflowValidationGate

        gate = WorkflowValidationGate()
        errors = gate.validate_workflow(workflow, registered_plugins)
        status = (
            ValidationResult.PASSED
            if not errors
            else ValidationResult.FAILED
        )
        return ValidationReport(
            artifact_name=workflow.name,
            gate_results=[
                GateResult(
                    gate_name=gate.name,
                    result=status,
                    errors=errors,
                )
            ],
        )
