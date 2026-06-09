"""Unit tests for the reference parser (no database needed)."""
import pytest

from app.core.errors import InvalidReferenceError
from app.services import reference_parser


def fake_matcher(text: str):
    # Pretend any text starting with a known book prefix matches.
    books = {"以西结书": (26, "以西结书"), "结": (26, "以西结书"), "创世记": (1, "创世记")}
    for alias in sorted(books, key=len, reverse=True):
        if text.startswith(alias):
            bid, name = books[alias]
            return bid, name, text[len(alias):]
    return None


def test_simple_range():
    r = reference_parser.parse("以西结书4:1-5", fake_matcher)
    assert r.book_id == 26
    assert len(r.ranges) == 1
    rng = r.ranges[0]
    assert (rng.start_chapter, rng.start_verse) == (4, 1)
    assert (rng.end_chapter, rng.end_verse) == (4, 5)


def test_abbreviation_and_fullwidth():
    r = reference_parser.parse("结４：１-５", fake_matcher)
    assert r.ranges[0].start_verse == 1
    assert r.ranges[0].end_verse == 5


def test_cross_chapter():
    r = reference_parser.parse("创世记1:1-2:3", fake_matcher)
    rng = r.ranges[0]
    assert (rng.start_chapter, rng.start_verse) == (1, 1)
    assert (rng.end_chapter, rng.end_verse) == (2, 3)


def test_multi_segment_carry_chapter():
    r = reference_parser.parse("以西结书4:1-5,7", fake_matcher)
    assert len(r.ranges) == 2
    assert (r.ranges[1].start_chapter, r.ranges[1].start_verse) == (4, 7)


def test_whole_chapter():
    r = reference_parser.parse("创世记1", fake_matcher)
    rng = r.ranges[0]
    assert rng.start_verse is None  # whole chapter sentinel


def test_unknown_book_raises():
    with pytest.raises(InvalidReferenceError):
        reference_parser.parse("xyz1:1", fake_matcher)


def test_empty_raises():
    with pytest.raises(InvalidReferenceError):
        reference_parser.parse("", fake_matcher)
