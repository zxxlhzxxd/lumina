"""Project, Theme and ServiceTemplate models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.enums import SlideSize
from app.domain.sections import Section
from app.domain.style import SectionStyle

SectionUnion = Annotated[Section, Field(discriminator="type")]

# Bump when the on-disk schema changes in a non-backward-compatible way.
SCHEMA_VERSION = 1


def _new_id() -> str:
    return uuid4().hex


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Theme(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "默认主题"
    builtin: bool = False
    default_style: Optional[SectionStyle] = None
    # Optional per-section-type default styles keyed by SectionType value.
    type_styles: dict[str, SectionStyle] = Field(default_factory=dict)


class ProjectMeta(BaseModel):
    pastor: str = ""
    theme_scripture: str = ""
    notes: str = ""


class Project(BaseModel):
    schema_version: int = SCHEMA_VERSION
    id: str = Field(default_factory=_new_id)
    name: str = "未命名礼拜"
    date: Optional[str] = None  # ISO date string
    slide_size: SlideSize = SlideSize.WIDE
    theme_id: Optional[str] = None
    sections: List[SectionUnion] = Field(default_factory=list)
    meta: ProjectMeta = Field(default_factory=ProjectMeta)
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class ServiceTemplate(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "主日崇拜"
    builtin: bool = False
    description: str = ""
    slide_size: SlideSize = SlideSize.WIDE
    # Skeleton sections (typically empty content placeholders).
    sections: List[SectionUnion] = Field(default_factory=list)
