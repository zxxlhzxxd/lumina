"""Unified response envelope.

Every successful response is `{ "data": ..., "error": null }`.
Every error response is `{ "data": null, "error": { code, message, details } }`.
"""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class Envelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[ErrorBody] = None


def ok(data: Any = None) -> dict:
    return {"data": data, "error": None}


def err(code: str, message: str, details: Any = None) -> dict:
    return {"data": None, "error": {"code": code, "message": message, "details": details}}
