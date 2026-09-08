"""`.lumina-bible` format, 1919 gold probes, and sqlite import."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data.import_bible import build
from app.data.lumina_bible import (
    DEFAULT_SOURCE,
    DEFAULT_TRANSLATION_ID,
    LuminaBibleError,
    gold_probe_cuv1919_shen,
    load_lumina_bible,
    validate_structure,
)
from app.services.bible_service import BibleService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_bundled_source_exists_and_has_expected_stats():
    data = load_lumina_bible(DEFAULT_SOURCE)
    chapters, verses = validate_structure(data)
    assert data["translation"]["id"] == DEFAULT_TRANSLATION_ID
    assert chapters == 1189
    assert verses == 31101
    assert len(data["books"]) == 66


def test_bundled_source_matches_1919_shen_gold_probes():
    data = load_lumina_bible(DEFAULT_SOURCE)
    assert gold_probe_cuv1919_shen(data) == []


def test_invalid_format_is_rejected():
    data = load_lumina_bible(FIXTURES / "invalid-format.lumina-bible")
    with pytest.raises(LuminaBibleError, match="format 必须是"):
        validate_structure(data)


def test_wrong_book_count_is_rejected(tmp_path):
    payload = {
        "format": "lumina-bible",
        "format_version": 1,
        "translation": {"id": "mini", "name": "mini"},
        "canon": "protestant-66",
        "books": [
            {
                "id": 1,
                "osis": "Gen",
                "name": "创世记",
                "short_names": ["创"],
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [{"verse": 1, "text": "起初，神创造天地。"}],
                    }
                ],
            }
        ],
    }
    path = tmp_path / "mini.lumina-bible"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(LuminaBibleError, match="书卷数必须为 66"):
        build(path, tmp_path / "bible.sqlite", apply_gold=False)


def test_import_bundled_source_writes_meta_and_gold_verses(tmp_path):
    db_path = tmp_path / "bible.sqlite"
    build(DEFAULT_SOURCE, db_path)
    original = None
    from app.core.config import settings

    original = settings.bible_db_path
    settings.bible_db_path = db_path
    service = BibleService()
    try:
        info = service.get_info()
        assert info["id"] == DEFAULT_TRANSLATION_ID
        assert "1919" in info["name"]
        _, gen = service.get_passage("创世记2:22")
        assert "领他到那人跟前" in gen[0].text
        assert "她" not in gen[0].text
        _, acts = service.get_passage("徒9:2")
        assert "大马色" in acts[0].text
        assert "大马士革" not in acts[0].text
    finally:
        if service._conn is not None:
            service._conn.close()
        settings.bible_db_path = original
