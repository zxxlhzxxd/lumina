"""Application error types and stable error codes.

The frontend depends on these codes (not on messages) for behaviour, so keep
them stable across refactors.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BIBLE_NOT_AVAILABLE = "BIBLE_NOT_AVAILABLE"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    EXPORT_FAILED = "EXPORT_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    http_status: int = 400
    code: ErrorCode = ErrorCode.VALIDATION_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: Optional[ErrorCode] = None,
        http_status: Optional[int] = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        self.details = details


class NotFoundError(AppError):
    http_status = 404
    code = ErrorCode.NOT_FOUND


class InvalidReferenceError(AppError):
    http_status = 422
    code = ErrorCode.INVALID_REFERENCE


class BibleNotAvailableError(AppError):
    http_status = 503
    code = ErrorCode.BIBLE_NOT_AVAILABLE


class ExportError(AppError):
    http_status = 500
    code = ErrorCode.EXPORT_FAILED
