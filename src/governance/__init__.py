"""Build-Time Governance & Validation Framework (ADR-009).

Provides validation gates that enforce architectural compliance
before plugin artifacts enter the Static Registry.
"""

from src.governance.engine import ValidationEngine, ValidationReport, ValidationResult
from src.governance.gates import (
    ContractValidationGate,
    ExecutionContextValidationGate,
    ManifestValidationGate,
    SecurityValidationGate,
    ValidationGate,
    WorkflowValidationGate,
)

__all__ = [
    "ContractValidationGate",
    "ExecutionContextValidationGate",
    "ManifestValidationGate",
    "SecurityValidationGate",
    "ValidationEngine",
    "ValidationGate",
    "ValidationReport",
    "ValidationResult",
    "WorkflowValidationGate",
]
