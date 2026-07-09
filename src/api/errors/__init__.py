"""API error handling."""

from src.api.errors.catalogue import (
    ErrorCode,
    ErrorDetail,
    raise_conflict,
    raise_not_found,
    raise_validation_error,
)

__all__ = [
    "ErrorCode",
    "ErrorDetail",
    "raise_conflict",
    "raise_not_found",
    "raise_validation_error",
]
