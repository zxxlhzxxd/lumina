"""Section models — a discriminated union keyed by `type`.

All section types share the common fields defined on `SectionBase`. Type-specific
content lives directly on each subclass.
"""
from __future__ import annotations

from typing import List, Literal, Optional, Union
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, Field

from app.domain.enums import AudioTrigger, PlayMode, ReadingRole, SectionType
from app.domain.style import SectionStyle


def _new_id() -> str:
    return uuid4().hex


class SectionBase(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = ""
    enabled: bool = True
    style: Optional[SectionStyle] = None
    notes: str = ""


class CoverSection(SectionBase):
    type: Literal[SectionType.COVER] = SectionType.COVER
    main_title: str = ""
    sub_title: str = ""
    extra: str = ""  # optional reference / pastor / date line


class ResponsiveReadingSection(SectionBase):
    type: Literal[SectionType.RESPONSIVE_READING] = SectionType.RESPONSIVE_READING
    reference: str = ""  # raw reference string, e.g. "以西结书4:1-5"
    start_role: ReadingRole = ReadingRole.QI
    show_verse_number: bool = True
    show_reference: bool = True


class ScriptureSection(SectionBase):
    type: Literal[SectionType.SCRIPTURE] = SectionType.SCRIPTURE
    reference: str = ""
    show_verse_number: bool = True
    include_title_slide: bool = True
    # 'auto' = paginate by capacity, 'manual' = use explicit page breaks (phase 2)
    pagination_mode: Literal["auto", "manual"] = "auto"
    chars_per_slide: int = 140  # capacity hint for auto pagination


class HymnSection(SectionBase):
    type: Literal[SectionType.HYMN] = SectionType.HYMN
    hymn_id: Optional[str] = None
    song_title: str = ""
    author: str = ""
    hymn_number: str = ""
    # Each entry is a logical lyric block (e.g. a verse or chorus).
    lyrics: List[str] = Field(default_factory=list)
    lines_per_slide: int = 2
    include_title_slide: bool = True


class LiturgyTextSection(SectionBase):
    type: Literal[SectionType.LITURGY_TEXT] = SectionType.LITURGY_TEXT
    liturgy_id: Optional[str] = None
    paragraphs: List[str] = Field(default_factory=list)
    chars_per_slide: int = 160


class AnnouncementSection(SectionBase):
    type: Literal[SectionType.ANNOUNCEMENT] = SectionType.ANNOUNCEMENT
    heading: str = ""
    items: List[str] = Field(default_factory=list)


class MediaSection(SectionBase):
    type: Literal[SectionType.MEDIA] = SectionType.MEDIA
    body: str = Field(default="", validation_alias=AliasChoices("body", "caption"))
    audio_ref: Optional[str] = None  # media ref inside project
    play_mode: PlayMode = PlayMode.ONCE
    audio_trigger: AudioTrigger = AudioTrigger.CLICK
    video_ref: Optional[str] = None  # phase 3


Section = Union[
    CoverSection,
    ResponsiveReadingSection,
    ScriptureSection,
    HymnSection,
    LiturgyTextSection,
    AnnouncementSection,
    MediaSection,
]

# Annotated discriminated union for use as a field type.
SectionField = Field(discriminator="type")
