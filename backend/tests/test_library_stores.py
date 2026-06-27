"""Tests for hymn / liturgy library stores and project-save library sync."""
import json
import sqlite3

import pytest

from app.core.config import settings
from app.core.errors import AppError
from app.domain.library import Hymn, HymnLyricSection, LiturgyText
from app.domain.sections import HymnSection, LiturgyTextSection
from app.services.hymn_store import HymnStore
from app.services.liturgy_store import LiturgyStore
from app.services.project_store import ProjectStore
from app.services import project_store as project_store_module


def test_hymn_library_starts_empty_and_crud(temp_data_dir):
    store = HymnStore()
    assert store.search() == []

    created = store.create(
        Hymn(title="自建诗歌", sections=[HymnLyricSection(order=0, text="第一句")])
    )
    assert "builtin" not in created.model_dump()
    fetched = store.get(created.id)
    assert fetched.title == "自建诗歌"
    fetched.title = "改名"
    updated = store.update(created.id, fetched)
    assert updated.title == "改名"
    copy = store.duplicate(created.id)
    assert copy.title == "改名 副本"
    store.delete(created.id)


def test_hymn_rejects_blank_title(temp_data_dir):
    store = HymnStore()
    with pytest.raises(AppError):
        store.create(Hymn(title="  "))


def test_hymn_migrates_old_builtin_rows_and_merges_duplicate_titles(
    temp_data_dir,
):
    conn = sqlite3.connect(settings.library_db_path)
    conn.executescript(
        """
        CREATE TABLE hymns (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT '',
            number TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            builtin INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE hymn_sections (
            hymn_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            label TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (hymn_id, seq)
        );
        """
    )
    conn.execute(
        "INSERT INTO hymns (id, title, author, number, source, builtin) "
        "VALUES ('old', '同名诗歌', '旧作者', '', '', 1)"
    )
    conn.execute(
        "INSERT INTO hymn_sections (hymn_id, seq, text) VALUES ('old', 0, '旧歌词')"
    )
    conn.execute(
        "INSERT INTO hymns (id, title, author, number, source, builtin) "
        "VALUES ('new', ' 同名诗歌 ', '新作者', '', '', 0)"
    )
    conn.execute(
        "INSERT INTO hymn_sections (hymn_id, seq, text) VALUES ('new', 0, '新歌词')"
    )
    conn.commit()
    conn.close()

    store = HymnStore()
    hymns = store.search()
    assert len(hymns) == 1
    assert hymns[0].id == "new"
    assert hymns[0].title == "同名诗歌"
    assert hymns[0].author == "新作者"
    assert hymns[0].sections[0].text == "新歌词"
    assert "builtin" not in hymns[0].model_dump()
    columns = {
        row["name"]
        for row in store._connect().execute("PRAGMA table_info(hymns)").fetchall()
    }
    assert "builtin" not in columns


def test_hymn_library_export_import_upserts_by_title(temp_data_dir, tmp_path):
    store = HymnStore()
    created = store.create(
        Hymn(
            title="可分享诗歌",
            author="作者",
            number="12",
            sections=[HymnLyricSection(order=0, label="第一节", text="第一句")],
        )
    )

    out = tmp_path / "hymns.lumina-hymn"
    saved, count = store.export_library(out)
    assert saved == out
    assert count == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["kind"] == "hymn_library"
    assert "builtin" not in payload["items"][0]

    old_payload = {
        "kind": "hymn_library",
        "schema_version": 1,
        "items": [
            {
                "id": "legacy",
                "title": "可分享诗歌",
                "author": "新作者",
                "number": "13",
                "source": "",
                "builtin": True,
                "sections": [{"order": 0, "label": "", "text": "更新歌词"}],
            }
        ],
    }
    out.write_text(json.dumps(old_payload, ensure_ascii=False), encoding="utf-8")
    imported = store.import_library(out)
    assert len(imported) == 1
    assert imported[0].id == created.id
    assert imported[0].author == "新作者"
    assert store.get(created.id).sections[0].text == "更新歌词"
    assert len(store.search()) == 1


def test_hymn_library_import_invalid_file_is_all_or_nothing(
    temp_data_dir, tmp_path
):
    store = HymnStore()
    before = len(store.search())
    bad = tmp_path / "bad.lumina-hymn"
    bad.write_text(
        json.dumps(
            {
                "kind": "hymn_library",
                "schema_version": 1,
                "items": [
                    {"title": "不应导入", "sections": [{"order": 0, "text": "A"}]},
                    "bad-item",
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(AppError):
        store.import_library(bad)

    assert len(store.search()) == before


def test_liturgy_library_starts_empty_and_crud(temp_data_dir):
    store = LiturgyStore()
    assert store.list() == []

    created = store.create(LiturgyText(title="自定礼文", paragraphs=["一段"]))
    assert "builtin" not in created.model_dump()
    copy = store.duplicate(created.id)
    assert copy.title == "自定礼文 副本"
    created.paragraphs = ["二段"]
    assert store.update(created.id, created).paragraphs == ["二段"]
    store.delete(created.id)


def test_liturgy_migrates_old_builtin_rows_and_merges_duplicate_titles(
    temp_data_dir,
):
    conn = sqlite3.connect(settings.library_db_path)
    conn.executescript(
        """
        CREATE TABLE liturgy_texts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            paragraphs TEXT NOT NULL DEFAULT '[]',
            builtin INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.execute(
        "INSERT INTO liturgy_texts (id, title, paragraphs, builtin) "
        "VALUES ('old', '同名礼文', '[\"旧段\"]', 1)"
    )
    conn.execute(
        "INSERT INTO liturgy_texts (id, title, paragraphs, builtin) "
        "VALUES ('new', ' 同名礼文 ', '[\"新段\"]', 0)"
    )
    conn.commit()
    conn.close()

    store = LiturgyStore()
    texts = store.list()
    assert len(texts) == 1
    assert texts[0].id == "new"
    assert texts[0].title == "同名礼文"
    assert texts[0].paragraphs == ["新段"]
    assert "builtin" not in texts[0].model_dump()
    columns = {
        row["name"]
        for row in store._connect()
        .execute("PRAGMA table_info(liturgy_texts)")
        .fetchall()
    }
    assert "builtin" not in columns


def test_liturgy_library_export_import_upserts_by_title(temp_data_dir, tmp_path):
    store = LiturgyStore()
    created = store.create(LiturgyText(title="可分享礼文", paragraphs=["一段"]))

    out = tmp_path / "liturgy.lumina-liturgy"
    saved, count = store.export_library(out)
    assert saved == out
    assert count == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["kind"] == "liturgy_library"
    assert "builtin" not in payload["items"][0]

    old_payload = {
        "kind": "liturgy_library",
        "schema_version": 1,
        "items": [
            {
                "id": "legacy",
                "title": "可分享礼文",
                "builtin": True,
                "paragraphs": ["更新段"],
            }
        ],
    }
    out.write_text(json.dumps(old_payload, ensure_ascii=False), encoding="utf-8")
    imported = store.import_library(out)
    assert len(imported) == 1
    assert imported[0].id == created.id
    assert store.get(created.id).paragraphs == ["更新段"]
    assert len(store.list()) == 1


def test_liturgy_library_rejects_wrong_kind(temp_data_dir, tmp_path):
    store = LiturgyStore()
    before = len(store.list())
    bad = tmp_path / "bad.lumina-liturgy"
    bad.write_text(
        json.dumps(
            {"kind": "hymn_library", "schema_version": 1, "items": []},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(AppError):
        store.import_library(bad)

    assert len(store.list()) == before


def test_project_save_upserts_hymns_and_liturgy_by_title(temp_data_dir):
    project_store_module.hymn_store._conn = None
    project_store_module.liturgy_store._conn = None
    store = ProjectStore()
    project = store.create(name="同步测试")
    project.sections = [
        HymnSection(song_title="同题诗歌", author="旧", lyrics=["旧歌词"]),
        LiturgyTextSection(slide_title="同题礼文", paragraphs=["旧段"]),
        HymnSection(song_title="同题诗歌", author="新", lyrics=["新歌词"]),
        LiturgyTextSection(slide_title="同题礼文", paragraphs=["新段"]),
    ]

    saved = store.replace(project.id, project)

    hymns = project_store_module.hymn_store.search()
    assert len(hymns) == 1
    assert hymns[0].title == "同题诗歌"
    assert hymns[0].author == "新"
    assert hymns[0].sections[0].text == "新歌词"
    assert saved.sections[0].hymn_id == hymns[0].id
    assert saved.sections[2].hymn_id == hymns[0].id

    texts = project_store_module.liturgy_store.list()
    assert len(texts) == 1
    assert texts[0].title == "同题礼文"
    assert texts[0].paragraphs == ["新段"]
    assert saved.sections[1].liturgy_id == texts[0].id
    assert saved.sections[3].liturgy_id == texts[0].id
