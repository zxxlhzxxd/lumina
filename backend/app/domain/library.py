"""Content-library models: Hymn (赞美诗) and LiturgyText (礼文)."""
from __future__ import annotations

from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid4().hex


class HymnLyricSection(BaseModel):
    """A logical lyric block within a hymn (a verse or chorus)."""

    order: int = 0
    label: str = ""  # e.g. "副歌", "第一节"
    text: str = ""   # one or more lines, newline-separated


class Hymn(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = ""
    author: str = ""
    number: str = ""  # hymnal number, kept as string (may contain letters)
    source: str = ""  # provenance / hymnal name
    sections: List[HymnLyricSection] = Field(default_factory=list)

    def lyric_blocks(self) -> List[str]:
        """Flatten lyric sections into the `lyrics: List[str]` shape used by
        `HymnSection` (one string per block)."""
        return [s.text for s in sorted(self.sections, key=lambda x: x.order)]


class LiturgyText(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = ""
    paragraphs: List[str] = Field(default_factory=list)


class HymnSummary(BaseModel):
    id: str
    title: str
    author: str
    number: str


class LiturgyTextSummary(BaseModel):
    id: str
    title: str
    paragraph_count: int


def hymn_summary(h: Hymn) -> HymnSummary:
    return HymnSummary(id=h.id, title=h.title, author=h.author, number=h.number)


def liturgy_summary(t: LiturgyText) -> LiturgyTextSummary:
    return LiturgyTextSummary(
        id=t.id,
        title=t.title,
        paragraph_count=len(t.paragraphs),
    )
