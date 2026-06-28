"""API error handling."""

from src.api.errors.catalogue import (
    ErrorCode,
    ErrorDetail,
    raise_conflict,
    raise_not_found,
)

__all__ = [
    "ErrorCode",
    "ErrorDetail",
    "raise_conflict",
    "raise_not_found",
]
