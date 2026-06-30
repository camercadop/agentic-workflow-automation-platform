"""Pipeline gate errors.

Custom exceptions raised when pipeline quality gates fail,
preventing the orchestrator from advancing to the next step.
"""

from __future__ import annotations


class PipelineGateError(Exception):
    """Raised when one or more pipeline guards fail at a step boundary.

    Attributes:
        step: The pipeline step where the failure occurred.
        errors: List of human-readable error descriptions.
    """

    def __init__(self, step: str, errors: list[str]) -> None:
        """Initialize with step name and list of error messages."""
        self.step = step
        self.errors = errors
        joined = "; ".join(errors)
        super().__init__(f"Pipeline gate failed at '{step}': {joined}")
