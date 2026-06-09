"""Bible reference parser.

Parses human-typed references such as:
    以西结书4:1-5        结 4:1-5         约翰福音 3:16
    创世记1:1-2:3        诗篇23           诗篇23-24
    以西结书4:1-5,7

Tolerant of full/half-width punctuation and digits, and extra whitespace.

Book matching is delegated to a caller-supplied matcher so this module stays
free of any database dependency and is unit-testable in isolation. The parser
produces *raw* ranges (verse may be None to mean "whole chapter"); a higher
layer resolves whole-chapter ranges and validates against actual data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from app.core.errors import InvalidReferenceError

# Full-width -> half-width normalization for digits and punctuation.
_TRANSLATION = {
    ord("："): ":",
    ord("，"): ",",
    ord("、"): ",",
    ord("－"): "-",
    ord("—"): "-",
    ord("–"): "-",
    ord("～"): "-",
    ord("~"): "-",
    ord("　"): " ",  # ideographic space
}
for _i in range(10):
    _TRANSLATION[ord("０") + _i] = chr(ord("0") + _i)


@dataclass
class RawRange:
    start_chapter: int
    start_verse: Optional[int]  # None => whole chapter
    end_chapter: int
    end_verse: Optional[int]  # None => end of end_chapter


@dataclass
class ParsedReference:
    book_id: int
    book_name: str
    ranges: List[RawRange]


# matcher: (normalized_text) -> (book_id, book_name, remainder) or None
BookMatcher = Callable[[str], Optional[Tuple[int, str, str]]]


def normalize(raw: str) -> str:
    return raw.translate(_TRANSLATION).strip()


def _clean_locations(s: str) -> str:
    # Drop Chinese chapter/verse markers that may appear in the locations part.
    s = s.replace("第", "").replace("章", ":").replace("节", "").replace("篇", "")
    s = s.replace(" ", "")
    return s


def _parse_int(text: str) -> int:
    if not text or not text.isdigit():
        raise InvalidReferenceError(f"无法识别的数字: '{text}'")
    return int(text)


def _parse_endpoint(token: str, current_chapter: Optional[int]) -> Tuple[int, Optional[int]]:
    """Parse 'C:V' or bare 'V'. Returns (chapter, verse_or_None)."""
    if ":" in token:
        c_str, v_str = token.split(":", 1)
        chapter = _parse_int(c_str)
        verse: Optional[int] = None if v_str == "" else _parse_int(v_str)
        return chapter, verse
    # bare number
    if current_chapter is None:
        # no chapter context yet -> the number is a chapter (whole chapter)
        return _parse_int(token), None
    return current_chapter, _parse_int(token)


def parse(raw: str, match_book: BookMatcher) -> ParsedReference:
    if not raw or not raw.strip():
        raise InvalidReferenceError("经文引用不能为空")

    text = normalize(raw)
    matched = match_book(text)
    if matched is None:
        raise InvalidReferenceError(f"无法识别书卷名: '{raw}'")
    book_id, book_name, remainder = matched

    remainder = _clean_locations(remainder)
    if remainder == "":
        raise InvalidReferenceError(f"缺少章节信息: '{raw}'")

    has_colon = ":" in remainder
    segments = [s for s in remainder.split(",") if s != ""]
    if not segments:
        raise InvalidReferenceError(f"缺少章节信息: '{raw}'")

    ranges: List[RawRange] = []
    current_chapter: Optional[int] = None

    for seg in segments:
        if "-" in seg:
            left, right = seg.split("-", 1)
        else:
            left, right = seg, None

        # In chapter-only mode (no colon anywhere), bare numbers are chapters.
        ctx = None if not has_colon else current_chapter
        s_chapter, s_verse = _parse_endpoint(left, ctx)
        current_chapter = s_chapter

        if right is None:
            e_chapter, e_verse = s_chapter, s_verse
        else:
            e_chapter, e_verse = _parse_endpoint(right, current_chapter if has_colon else None)
            current_chapter = e_chapter

        ranges.append(
            RawRange(
                start_chapter=s_chapter,
                start_verse=s_verse,
                end_chapter=e_chapter,
                end_verse=e_verse,
            )
        )

    return ParsedReference(book_id=book_id, book_name=book_name, ranges=ranges)
