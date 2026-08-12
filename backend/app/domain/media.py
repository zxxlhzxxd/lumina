"""Media resource-library domain models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

MediaKind = Literal["image", "audio", "video"]


def _new_id() -> str:
    return uuid4().hex


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MediaAsset(BaseModel):
    id: str = Field(default_factory=_new_id)
    kind: MediaKind
    name: str = ""
    ref: str
    created_at: str = Field(default_factory=_now)


class MediaImportFailure(BaseModel):
    source_path: str
    code: str
    message: str


class MediaBatchImportResult(BaseModel):
    assets: List[MediaAsset] = Field(default_factory=list)
    failed: List[MediaImportFailure] = Field(default_factory=list)
