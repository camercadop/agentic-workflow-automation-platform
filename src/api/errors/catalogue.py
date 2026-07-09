"""API error catalogue."""

from enum import StrEnum
from typing import NoReturn

from fastapi import HTTPException
from starlette import status


class ErrorCode(StrEnum):
    """Enumeration of all API error codes."""

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class ErrorDetail:
    """Structured error payload returned in API responses."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        """Initialize error detail with code and message."""
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        """Serialize to the API error response format."""
        return {"code": self.code, "message": self.message}


def raise_not_found(message: str) -> NoReturn:
    """Raise a 404 HTTPException with a RESOURCE_NOT_FOUND error code."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorDetail(ErrorCode.RESOURCE_NOT_FOUND, message).to_dict(),
    )


def raise_conflict(message: str = "Resource already exists") -> NoReturn:
    """Raise a 409 HTTPException with a RESOURCE_ALREADY_EXISTS error code."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorDetail(ErrorCode.RESOURCE_ALREADY_EXISTS, message).to_dict(),
    )


def raise_validation_error(errors: list[str]) -> NoReturn:
    """Raise a 422 HTTPException with validation errors."""
    raise HTTPException(
        status_code=422,
        detail=ErrorDetail(
            ErrorCode.VALIDATION_ERROR,
            "; ".join(errors),
        ).to_dict(),
    )
