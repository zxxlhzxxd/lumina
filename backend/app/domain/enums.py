"""Shared enums for the domain model."""
from __future__ import annotations

from enum import Enum


class SectionType(str, Enum):
    COVER = "cover"
    RESPONSIVE_READING = "responsive_reading"
    SCRIPTURE = "scripture"
    HYMN = "hymn"
    LITURGY_TEXT = "liturgy_text"
    ANNOUNCEMENT = "announcement"
    MEDIA = "media"


class SectionCategory(str, Enum):
    RESPONSIVE = "responsive"
    HYMN = "hymn"
    SCRIPTURE = "scripture"
    LITURGY = "liturgy"
    MEDIA = "media"
    OTHER = "other"


# Default category mapping per section type.
TYPE_TO_CATEGORY = {
    SectionType.COVER: SectionCategory.OTHER,
    SectionType.RESPONSIVE_READING: SectionCategory.RESPONSIVE,
    SectionType.SCRIPTURE: SectionCategory.SCRIPTURE,
    SectionType.HYMN: SectionCategory.HYMN,
    SectionType.LITURGY_TEXT: SectionCategory.LITURGY,
    SectionType.ANNOUNCEMENT: SectionCategory.OTHER,
    SectionType.MEDIA: SectionCategory.MEDIA,
}


class ReadingRole(str, Enum):
    """Who reads a given verse in responsive reading."""

    QI = "qi"   # 启 — leader
    YING = "ying"  # 应 — congregation


class PlayMode(str, Enum):
    ONCE = "once"
    LOOP = "loop"


class SlideSize(str, Enum):
    WIDE = "16:9"
    STANDARD = "4:3"
