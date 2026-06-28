"""Hymn library backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.domain.library import Hymn, HymnLyricSection

SCHEMA = """
CREATE TABLE IF NOT EXISTS hymns (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    author   TEXT NOT NULL DEFAULT '',
    number   TEXT NOT NULL DEFAULT '',
    source   TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS hymn_sections (
    hymn_id  TEXT NOT NULL,
    seq      INTEGER NOT NULL,
    label    TEXT NOT NULL DEFAULT '',
    text     TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (hymn_id, seq)
);
"""


def _new_id() -> str:
    return uuid4().hex


def _clean_title(title: str) -> str:
    return (title or "").strip()


class HymnStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            settings.ensure_dirs()
            self._conn = sqlite3.connect(
                str(settings.library_db_path), check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(SCHEMA)
            self._migrate_schema()
        return self._conn

    def _migrate_schema(self) -> None:
        assert self._conn is not None
        conn = self._conn
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(hymns)")}
        self._merge_duplicate_titles()
        if "builtin" in columns:
            conn.execute("ALTER TABLE hymns RENAME TO hymns_old")
            conn.execute(
                """
                CREATE TABLE hymns (
                    id       TEXT PRIMARY KEY,
                    title    TEXT NOT NULL,
                    author   TEXT NOT NULL DEFAULT '',
                    number   TEXT NOT NULL DEFAULT '',
                    source   TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                "INSERT INTO hymns (id, title, author, number, source) "
                "SELECT id, title, author, number, source FROM hymns_old"
            )
            conn.execute("DROP TABLE hymns_old")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_hymns_title_unique "
            "ON hymns(title) WHERE title <> ''"
        )
        conn.commit()

    def _merge_duplicate_titles(self) -> None:
        assert self._conn is not None
        conn = self._conn
        rows = conn.execute(
            "SELECT rowid, id, title FROM hymns ORDER BY rowid"
        ).fetchall()
        keep_by_title: dict[str, sqlite3.Row] = {}
        for row in rows:
            title = _clean_title(row["title"])
            if title:
                keep_by_title[title] = row

        keep_ids = {row["id"] for row in keep_by_title.values()}
        for row in rows:
            title = _clean_title(row["title"])
            if title:
                if row["id"] not in keep_ids:
                    conn.execute(
                        "DELETE FROM hymn_sections WHERE hymn_id=?", (row["id"],)
                    )
                    conn.execute("DELETE FROM hymns WHERE id=?", (row["id"],))
                else:
                    conn.execute(
                        "UPDATE hymns SET title=? WHERE id=?", (title, row["id"])
                    )

    # ---- read ------------------------------------------------------------
    def _row_to_hymn(self, row: sqlite3.Row) -> Hymn:
        conn = self._connect()
        secs = conn.execute(
            "SELECT seq, label, text FROM hymn_sections WHERE hymn_id=? ORDER BY seq",
            (row["id"],),
        ).fetchall()
        return Hymn(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            number=row["number"],
            source=row["source"],
            sections=[
                HymnLyricSection(order=s["seq"], label=s["label"], text=s["text"])
                for s in secs
            ],
        )

    def search(self, query: str = "") -> List[Hymn]:
        conn = self._connect()
        q = (query or "").strip()
        if not q:
            rows = conn.execute(
                "SELECT * FROM hymns ORDER BY title"
            ).fetchall()
            return [self._row_to_hymn(r) for r in rows]
        like = f"%{q}%"
        rows = conn.execute(
            "SELECT DISTINCT h.* FROM hymns h "
            "LEFT JOIN hymn_sections s ON s.hymn_id = h.id "
            "WHERE h.title LIKE ? OR h.author LIKE ? OR h.number LIKE ? OR s.text LIKE ? "
            "ORDER BY h.title",
            (like, like, like, like),
        ).fetchall()
        return [self._row_to_hymn(r) for r in rows]

    def get(self, hymn_id: str) -> Hymn:
        conn = self._connect()
        row = conn.execute("SELECT * FROM hymns WHERE id=?", (hymn_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"赞美诗不存在: {hymn_id}")
        return self._row_to_hymn(row)

    # ---- write -----------------------------------------------------------
    def _insert(self, hymn: Hymn) -> None:
        conn = self._connect()
        conn.execute(
            "INSERT INTO hymns (id, title, author, number, source) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                hymn.id,
                hymn.title,
                hymn.author,
                hymn.number,
                hymn.source,
            ),
        )
        for i, sec in enumerate(sorted(hymn.sections, key=lambda s: s.order)):
            conn.execute(
                "INSERT INTO hymn_sections (hymn_id, seq, label, text) VALUES (?, ?, ?, ?)",
                (hymn.id, i, sec.label, sec.text),
            )

    def create(self, hymn: Hymn) -> Hymn:
        with self._lock:
            hymn = hymn.model_copy(deep=True)
            hymn.title = _clean_title(hymn.title)
            if not hymn.title:
                raise AppError("请填写诗歌名")
            hymn.id = _new_id()
            conn = self._connect()
            try:
                self._insert(hymn)
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise AppError("诗歌名已存在") from exc
        return hymn

    def update(self, hymn_id: str, hymn: Hymn) -> Hymn:
        with self._lock:
            self.get(hymn_id)
            conn = self._connect()
            hymn = hymn.model_copy(deep=True)
            hymn.title = _clean_title(hymn.title)
            if not hymn.title:
                raise AppError("请填写诗歌名")
            hymn.id = hymn_id
            try:
                conn.execute("DELETE FROM hymn_sections WHERE hymn_id=?", (hymn_id,))
                conn.execute("DELETE FROM hymns WHERE id=?", (hymn_id,))
                self._insert(hymn)
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise AppError("诗歌名已存在") from exc
        return hymn

    def delete(self, hymn_id: str) -> None:
        with self._lock:
            self.get(hymn_id)
            conn = self._connect()
            conn.execute("DELETE FROM hymn_sections WHERE hymn_id=?", (hymn_id,))
            conn.execute("DELETE FROM hymns WHERE id=?", (hymn_id,))
            conn.commit()

    def duplicate(self, hymn_id: str) -> Hymn:
        source = self.get(hymn_id)
        copy = source.model_copy(deep=True)
        copy.id = _new_id()
        copy.title = self._copy_title(source.title)
        with self._lock:
            conn = self._connect()
            self._insert(copy)
            conn.commit()
        return copy

    def _copy_title(self, title: str) -> str:
        conn = self._connect()
        base = f"{_clean_title(title)} 副本".strip()
        candidate = base
        index = 2
        while conn.execute("SELECT 1 FROM hymns WHERE title=?", (candidate,)).fetchone():
            candidate = f"{base} {index}"
            index += 1
        return candidate

    def upsert_by_title(self, hymn: Hymn) -> Hymn:
        title = _clean_title(hymn.title)
        if not title:
            raise AppError("请填写诗歌名")
        conn = self._connect()
        existing = conn.execute("SELECT id FROM hymns WHERE title=?", (title,)).fetchone()
        hymn = hymn.model_copy(deep=True)
        hymn.title = title
        if existing is None:
            return self.create(hymn)
        return self.update(existing["id"], hymn)

    # ---- import / export -------------------------------------------------
    def export_library(self, out_path: Path) -> tuple[Path, int]:
        """Export hymns to a portable JSON library file."""
        items = self.search()
        payload = {
            "kind": "hymn_library",
            "schema_version": 1,
            "items": [h.model_dump() for h in items],
        }
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out_path, len(items)

    def import_library(self, in_path: Path) -> List[Hymn]:
        """Import a portable hymn library file as new editable copies."""
        payload = self._read_library_payload(in_path)
        try:
            hymns = [Hymn.model_validate(item) for item in payload["items"]]
        except Exception as exc:
            raise AppError("无效的歌词库文件：条目格式错误") from exc
        imported: List[Hymn] = []
        for hymn in hymns:
            if not _clean_title(hymn.title):
                raise AppError("无效的歌词库文件：诗歌名不能为空")
            imported.append(hymn)

        with self._lock:
            conn = self._connect()
            try:
                saved = [self._upsert_by_title_unlocked(hymn) for hymn in imported]
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return saved

    def _upsert_by_title_unlocked(self, hymn: Hymn) -> Hymn:
        assert self._conn is not None
        title = _clean_title(hymn.title)
        if not title:
            raise AppError("请填写诗歌名")
        conn = self._conn
        existing = conn.execute("SELECT id FROM hymns WHERE title=?", (title,)).fetchone()
        hymn = hymn.model_copy(deep=True)
        hymn.title = title
        hymn.id = existing["id"] if existing is not None else _new_id()
        conn.execute("DELETE FROM hymn_sections WHERE hymn_id=?", (hymn.id,))
        conn.execute("DELETE FROM hymns WHERE id=?", (hymn.id,))
        self._insert(hymn)
        return hymn

    def _read_library_payload(self, in_path: Path) -> dict[str, Any]:
        in_path = Path(in_path)
        if not in_path.exists():
            raise AppError(f"歌词库文件不存在: {in_path}")
        try:
            payload = json.loads(in_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AppError("无效的歌词库文件") from exc
        if not isinstance(payload, dict):
            raise AppError("无效的歌词库文件")
        if payload.get("kind") != "hymn_library":
            raise AppError("无效的歌词库文件：类型不匹配")
        if payload.get("schema_version") != 1:
            raise AppError("不支持的歌词库文件版本")
        if not isinstance(payload.get("items"), list):
            raise AppError("无效的歌词库文件：缺少 items")
        return payload


hymn_store = HymnStore()
