"""BibleService presents verses through the display pipeline."""

import sqlite3
from pathlib import Path

import pytest

from app.core.config import settings
from app.domain.sections import ResponsiveReadingSection, ScriptureSection
from app.services.bible_service import BibleService
from app.services.generation import build_section_slides
from app.services.text_transform import TransformPipeline

SCHEMA = """
CREATE TABLE books (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    short_names   TEXT NOT NULL,
    book_order    INTEGER NOT NULL,
    chapter_count INTEGER NOT NULL
);
CREATE TABLE verses (
    book_id  INTEGER NOT NULL,
    chapter  INTEGER NOT NULL,
    verse    INTEGER NOT NULL,
    text     TEXT NOT NULL,
    PRIMARY KEY (book_id, chapter, verse)
);
"""


def _write_fixture(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO books (id, name, short_names, book_order, chapter_count) "
            "VALUES (1, '创世记', '创', 1, 2)"
        )
        conn.executemany(
            "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
            [
                (1, 1, 1, "起初，　神创造天地。"),
                (1, 1, 3, "神说：「要有光」，就有了光。"),
                (
                    1,
                    1,
                    18,
                    "耶和华对亚伯拉罕说：「撒拉为什么暗笑，说：『我既已年老，果真能生养吗？』",
                ),
                (1, 2, 7, "他就成了有灵的活人，[名叫 亚当]。"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def bible_service(tmp_path):
    db_path = tmp_path / "bible.sqlite"
    _write_fixture(db_path)
    original = settings.bible_db_path
    settings.bible_db_path = db_path
    service = BibleService()
    try:
        yield service
    finally:
        if service._conn is not None:
            service._conn.close()
        settings.bible_db_path = original


def test_get_passage_normalizes_quotes_and_keeps_wording(bible_service):
    _, verses = bible_service.get_passage("创世记1:3")
    assert verses[0].text == "神说：“要有光”，就有了光。"


def test_get_passage_normalizes_nested_quotes(bible_service):
    _, verses = bible_service.get_passage("创世记1:18")
    assert verses[0].text == (
        "耶和华对亚伯拉罕说：“撒拉为什么暗笑，说：‘我既已年老，果真能生养吗？’"
    )


def test_get_passage_strips_shen_spacing_and_keeps_added_words(bible_service):
    _, first = bible_service.get_passage("创世记1:1")
    _, adam = bible_service.get_passage("创世记2:7")
    assert first[0].text == "起初，神创造天地。"
    assert adam[0].text == "他就成了有灵的活人，[名叫 亚当]。"


def test_identity_pipeline_returns_source_punctuation(tmp_path):
    db_path = tmp_path / "bible.sqlite"
    _write_fixture(db_path)
    original = settings.bible_db_path
    settings.bible_db_path = db_path
    service = BibleService(display_pipeline=TransformPipeline([]))
    try:
        _, verses = service.get_passage("创世记1:3")
        assert verses[0].text == "神说：「要有光」，就有了光。"
    finally:
        if service._conn is not None:
            service._conn.close()
        settings.bible_db_path = original


def test_scripture_and_responsive_slides_use_displayed_quotes(bible_service):
    scripture = build_section_slides(
        ScriptureSection(
            reference="创世记1:3",
            include_title_slide=False,
            show_verse_number=False,
        ),
        bible_service.get_passage,
    )
    responsive = build_section_slides(
        ResponsiveReadingSection(
            reference="创世记1:3",
            show_reference=False,
            show_verse_number=False,
        ),
        bible_service.get_passage,
    )
    assert scripture[0].body == "神说：“要有光”，就有了光。"
    assert responsive[0].body == "神说：“要有光”，就有了光。"
    assert "「" not in scripture[0].body
    assert "「" not in responsive[0].body
