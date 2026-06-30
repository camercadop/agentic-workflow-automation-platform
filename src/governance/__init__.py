"""Build-Time Governance & Validation Framework (ADR-009).

Provides validation gates that enforce architectural compliance
before plugin artifacts enter the Static Registry, and pipeline
guards that prevent hallucinated implementations from advancing.
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
from src.governance.pipeline_errors import PipelineGateError
from src.governance.pipeline_guards import (
    run_all_guards_for_step,
    run_developer_guards,
    run_reviewer_guards,
    run_tester_guards,
    verify_artifacts_exist,
    verify_paths_valid,
    verify_report_matches_git,
    verify_reviewer_precondition,
    verify_syntax,
    verify_tests_pass,
)

__all__ = [
    "ContractValidationGate",
    "ExecutionContextValidationGate",
    "ManifestValidationGate",
    "PipelineGateError",
    "SecurityValidationGate",
    "ValidationEngine",
    "ValidationGate",
    "ValidationReport",
    "ValidationResult",
    "WorkflowValidationGate",
    "run_all_guards_for_step",
    "run_developer_guards",
    "run_reviewer_guards",
    "run_tester_guards",
    "verify_artifacts_exist",
    "verify_paths_valid",
    "verify_report_matches_git",
    "verify_reviewer_precondition",
    "verify_syntax",
    "verify_tests_pass",
]
