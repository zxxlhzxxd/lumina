"""Structured Bible reference and verse models."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class VerseRef(BaseModel):
    """A single chapter:verse location."""

    chapter: int
    verse: int


class RangeRef(BaseModel):
    """A contiguous span within one book, possibly crossing chapters."""

    start: VerseRef
    end: VerseRef


class BibleReference(BaseModel):
    """A parsed, normalized reference such as 以西结书 4:1-5,7."""

    book_id: int
    book_name: str
    ranges: List[RangeRef]
    # Human-readable normalized form, e.g. "以西结书 4:1-5,7"
    display: str


class Verse(BaseModel):
    book_id: int
    book_name: str
    chapter: int
    verse: int
    text: str


class Book(BaseModel):
    id: int
    name: str
    short_names: List[str]
    order: int
    chapter_count: int
