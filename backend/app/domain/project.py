"""Project and ServiceTemplate models."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import SlideSize
from app.domain.media import MediaAsset, MediaKind
from app.domain.sections import Section

SectionUnion = Annotated[Section, Field(discriminator="type")]

# Bump when the on-disk schema changes in a non-backward-compatible way.
SCHEMA_VERSION = 1


def _new_id() -> str:
    return uuid4().hex


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _media_kind_from_ref(ref: str, fallback: MediaKind) -> MediaKind:
    ext = Path(ref).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
        return "image"
    if ext in {".mp3", ".wav"}:
        return "audio"
    if ext in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    return fallback


def _asset_name_from_ref(ref: str) -> str:
    return Path(ref).name or ref


def _append_asset(
    assets: list[MediaAsset], seen: set[str], ref: Optional[str], fallback: MediaKind
) -> None:
    if not ref or not ref.startswith("media/") or ref in seen:
        return
    seen.add(ref)
    assets.append(
        MediaAsset(
            kind=_media_kind_from_ref(ref, fallback),
            name=_asset_name_from_ref(ref),
            ref=ref,
        )
    )


def _ensure_media_assets_from_sections(data: dict) -> dict:
    sections = data.get("sections")
    if not isinstance(sections, list):
        return data
    raw_assets = data.get("media_assets") or []
    if not isinstance(raw_assets, list):
        raw_assets = []
    assets = [
        MediaAsset.model_validate(asset)
        for asset in raw_assets
        if isinstance(asset, (dict, MediaAsset))
    ]
    seen = {asset.ref for asset in assets}
    for section in sections:
        if not isinstance(section, dict):
            continue
        style = section.get("style")
        if isinstance(style, dict):
            _append_asset(assets, seen, style.get("background_image"), "image")
            _append_asset(assets, seen, style.get("background_video"), "video")
        _append_asset(assets, seen, section.get("audio_ref"), "audio")
        _append_asset(assets, seen, section.get("video_ref"), "video")
    data["media_assets"] = [asset.model_dump() for asset in assets]
    return data


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
    sections: List[SectionUnion] = Field(default_factory=list)
    media_assets: List[MediaAsset] = Field(default_factory=list)
    meta: ProjectMeta = Field(default_factory=ProjectMeta)
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)

    @model_validator(mode="before")
    @classmethod
    def migrate_media_assets(cls, data):
        if isinstance(data, dict):
            return _ensure_media_assets_from_sections(dict(data))
        return data


class ServiceTemplate(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "主日崇拜"
    builtin: bool = False
    description: str = ""
    slide_size: SlideSize = SlideSize.WIDE
    # Skeleton sections (typically empty content placeholders).
    sections: List[SectionUnion] = Field(default_factory=list)
    media_assets: List[MediaAsset] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrate_media_assets(cls, data):
        if isinstance(data, dict):
            return _ensure_media_assets_from_sections(dict(data))
        return data
