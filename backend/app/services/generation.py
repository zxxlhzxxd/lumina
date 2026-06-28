"""Section -> slide expansion.

Produces a normalized, renderer-agnostic list of `SlideModel` objects. The
PPTX engine and the (approximate) preview both consume this same output, so
what you preview matches what you export.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from pydantic import BaseModel

from app.domain.bible import BibleReference, Verse
from app.domain.enums import ReadingRole, SectionType
from app.domain.project import Project
from app.domain.sections import (
    AnnouncementSection,
    CoverSection,
    HymnSection,
    LiturgyTextSection,
    MediaSection,
    ResponsiveReadingSection,
    ScriptureSection,
    Section,
)
from app.services.bible_service import bible_service
from app.services.styling import resolve_style

# (raw_ref) -> (reference, verses)
PassageResolver = Callable[[str], Tuple[BibleReference, List[Verse]]]


class SlideModel(BaseModel):
    kind: str
    section_id: str
    section_type: str
    index: int = 0  # index within the section
    title: Optional[str] = None
    subtitle: Optional[str] = None
    label: Optional[str] = None  # 启 / 应
    reference: Optional[str] = None
    body: Optional[str] = None
    rich_body: Optional[List[List[dict]]] = None
    audio_ref: Optional[str] = None
    play_mode: Optional[str] = None
    audio_trigger: Optional[str] = None
    # Resolved (cascaded) style for this slide; consumed by preview + PPTX.
    style: Optional[dict] = None


_ROLE_LABEL = {ReadingRole.QI: "启", ReadingRole.YING: "应"}


def _cover_slides(s: CoverSection) -> List[SlideModel]:
    return [
        SlideModel(
            kind="cover",
            section_id=s.id,
            section_type=s.type.value,
            title=s.main_title,
            subtitle=s.sub_title,
            body=s.extra or None,
        )
    ]


def _responsive_slides(s: ResponsiveReadingSection, resolve: PassageResolver) -> List[SlideModel]:
    if not s.reference.strip():
        return []
    ref, verses = resolve(s.reference)
    slides: List[SlideModel] = []
    role = s.start_role
    for i, v in enumerate(verses):
        ref_line = None
        if s.show_reference:
            ref_line = f"{ref.book_name} {v.chapter}:{v.verse}"
        body = v.text
        if s.show_verse_number and not s.show_reference:
            body = f"{v.verse}. {v.text}"
        label = "合" if i == len(verses) - 1 else _ROLE_LABEL[role]
        slides.append(
            SlideModel(
                kind="responsive_verse",
                section_id=s.id,
                section_type=s.type.value,
                index=i,
                label=label,
                reference=ref_line,
                body=body,
            )
        )
        role = ReadingRole.YING if role == ReadingRole.QI else ReadingRole.QI
    return slides


def _paginate_units(units: List[str], capacity: int) -> List[List[str]]:
    """Pack whole text units into pages without exceeding `capacity` chars.

    A unit larger than capacity gets its own page (overflow allowed).
    """
    pages: List[List[str]] = []
    current: List[str] = []
    current_len = 0
    for unit in units:
        unit_len = len(unit)
        if current and current_len + unit_len > capacity:
            pages.append(current)
            current = []
            current_len = 0
        current.append(unit)
        current_len += unit_len
    if current:
        pages.append(current)
    return pages


def _join_rich_units(units: List[List[dict]], separator: str) -> List[dict]:
    runs: List[dict] = []
    for i, unit in enumerate(units):
        if i > 0 and separator:
            runs.append({"text": separator})
        runs.extend(unit)
    return runs


def _scripture_slides(s: ScriptureSection, resolve: PassageResolver) -> List[SlideModel]:
    if not s.reference.strip():
        return []
    ref, verses = resolve(s.reference)
    slides: List[SlideModel] = []
    idx = 0
    if s.include_title_slide:
        slides.append(
            SlideModel(
                kind="scripture_title",
                section_id=s.id,
                section_type=s.type.value,
                index=idx,
                title=ref.book_name,
                subtitle=ref.display,
            )
        )
        idx += 1

    units = []
    rich_units = []
    for v in verses:
        units.append(f"{v.verse} {v.text}" if s.show_verse_number else v.text)
        if s.show_verse_number:
            rich_units.append(
                [
                    {"text": str(v.verse), "superscript": True},
                    {"text": f" {v.text}"},
                ]
            )
    capacity = max(20, s.chars_per_slide)
    if s.verse_layout == "line_per_verse":
        separator = "\n"
    else:
        separator = " " if s.show_verse_number else ""
    cursor = 0
    for page_units in _paginate_units(units, capacity):
        rich_body = None
        if s.show_verse_number:
            page_rich_units = rich_units[cursor : cursor + len(page_units)]
            rich_body = (
                page_rich_units
                if s.verse_layout == "line_per_verse"
                else [_join_rich_units(page_rich_units, separator)]
            )
        cursor += len(page_units)
        slides.append(
            SlideModel(
                kind="scripture",
                section_id=s.id,
                section_type=s.type.value,
                index=idx,
                reference=ref.display,
                body=separator.join(page_units),
                rich_body=rich_body,
            )
        )
        idx += 1
    return slides


def _page_blocks_by_blank_lines(blocks: List[str]) -> List[List[str]]:
    pages: List[List[str]] = []
    current: List[str] = []
    previous_nonblank = False
    for block_index, block in enumerate(blocks):
        if block_index > 0 and previous_nonblank:
            pages.append(current)
            current = []
            previous_nonblank = False
        for line in block.split("\n"):
            if not line.strip() and previous_nonblank:
                pages.append(current)
                current = []
                previous_nonblank = False
                continue
            current.append(line)
            previous_nonblank = bool(line.strip())
    if any(line.strip() for line in current):
        pages.append(current)
    return pages


def _liturgy_slides(s: LiturgyTextSection) -> List[SlideModel]:
    slides: List[SlideModel] = []
    title = s.slide_title or None
    for i, page in enumerate(_page_blocks_by_blank_lines(s.paragraphs)):
        slides.append(
            SlideModel(
                kind="liturgy",
                section_id=s.id,
                section_type=s.type.value,
                index=i,
                title=title if i == 0 else None,
                body="\n".join(page),
            )
        )
    if not slides:
        slides.append(
            SlideModel(
                kind="liturgy",
                section_id=s.id,
                section_type=s.type.value,
                title=title,
                body="",
            )
        )
    return slides


def _hymn_slides(s: HymnSection) -> List[SlideModel]:
    slides: List[SlideModel] = []
    idx = 0
    if s.include_title_slide:
        sub = " ".join(x for x in [s.hymn_number, s.author] if x) or None
        slides.append(
            SlideModel(
                kind="hymn_title",
                section_id=s.id,
                section_type=s.type.value,
                index=idx,
                title=s.song_title,
                subtitle=sub,
            )
        )
        idx += 1

    for page in _page_blocks_by_blank_lines(s.lyrics):
        slides.append(
            SlideModel(
                kind="hymn_lyric",
                section_id=s.id,
                section_type=s.type.value,
                index=idx,
                body="\n".join(page),
            )
        )
        idx += 1
    return slides


def _announcement_slides(s: AnnouncementSection) -> List[SlideModel]:
    text_blocks = ["\n".join(s.items)] if s.items else []
    pages = _page_blocks_by_blank_lines(text_blocks)
    if not pages:
        return [
            SlideModel(
                kind="announcement",
                section_id=s.id,
                section_type=s.type.value,
                title=s.heading or "家事报告",
                body=None,
            )
        ]
    return [
        SlideModel(
            kind="announcement",
            section_id=s.id,
            section_type=s.type.value,
            index=i,
            title=(s.heading or "家事报告") if i == 0 else None,
            body="\n".join(page),
        )
        for i, page in enumerate(pages)
    ]


def _media_slides(s: MediaSection) -> List[SlideModel]:
    return [
        SlideModel(
            kind="media",
            section_id=s.id,
            section_type=s.type.value,
            title=s.slide_title or None,
            body=s.body or None,
            audio_ref=s.audio_ref,
            play_mode=s.play_mode.value,
            audio_trigger=s.audio_trigger.value,
        )
    ]


def build_section_slides(section: Section, resolve: Optional[PassageResolver] = None) -> List[SlideModel]:
    resolve = resolve or bible_service.get_passage
    if isinstance(section, CoverSection):
        return _cover_slides(section)
    if isinstance(section, ResponsiveReadingSection):
        return _responsive_slides(section, resolve)
    if isinstance(section, ScriptureSection):
        return _scripture_slides(section, resolve)
    if isinstance(section, LiturgyTextSection):
        return _liturgy_slides(section)
    if isinstance(section, HymnSection):
        return _hymn_slides(section)
    if isinstance(section, AnnouncementSection):
        return _announcement_slides(section)
    if isinstance(section, MediaSection):
        return _media_slides(section)
    return []


def build_slides(
    project: Project,
    resolve: Optional[PassageResolver] = None,
) -> List[SlideModel]:
    resolve = resolve or bible_service.get_passage
    slides: List[SlideModel] = []
    for section in project.sections:
        if not section.enabled:
            continue
        section_slides = build_section_slides(section, resolve)
        style = resolve_style(section).model_dump(exclude_none=True)
        for sm in section_slides:
            sm.style = style
        slides.extend(section_slides)
    return slides
