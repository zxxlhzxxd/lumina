"""Media resource-library domain models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
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
