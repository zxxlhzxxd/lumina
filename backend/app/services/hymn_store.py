"""Hymn library backed by SQLite (built-in + user entries, unified search).

Built-in hymns are seeded on first run with `builtin=1` and are read-only:
they cannot be edited or deleted, but may be duplicated into editable copies.
"""
from __future__ import annotations

import sqlite3
import threading
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.data.hymn_seed import builtin_hymns
from app.domain.library import Hymn, HymnLyricSection

SCHEMA = """
CREATE TABLE IF NOT EXISTS hymns (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    author   TEXT NOT NULL DEFAULT '',
    number   TEXT NOT NULL DEFAULT '',
    source   TEXT NOT NULL DEFAULT '',
    builtin  INTEGER NOT NULL DEFAULT 0
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
            self._seed_if_empty()
        return self._conn

    def _seed_if_empty(self) -> None:
        assert self._conn is not None
        (count,) = self._conn.execute(
            "SELECT COUNT(*) FROM hymns WHERE builtin=1"
        ).fetchone()
        if count:
            return
        for hymn in builtin_hymns():
            self._insert(hymn)
        self._conn.commit()

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
            builtin=bool(row["builtin"]),
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
                "SELECT * FROM hymns ORDER BY builtin DESC, title"
            ).fetchall()
            return [self._row_to_hymn(r) for r in rows]
        like = f"%{q}%"
        rows = conn.execute(
            "SELECT DISTINCT h.* FROM hymns h "
            "LEFT JOIN hymn_sections s ON s.hymn_id = h.id "
            "WHERE h.title LIKE ? OR h.author LIKE ? OR h.number LIKE ? OR s.text LIKE ? "
            "ORDER BY h.builtin DESC, h.title",
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
            "INSERT INTO hymns (id, title, author, number, source, builtin) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                hymn.id,
                hymn.title,
                hymn.author,
                hymn.number,
                hymn.source,
                1 if hymn.builtin else 0,
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
            hymn.id = _new_id()
            hymn.builtin = False
            self._insert(hymn)
            self._connect().commit()
        return hymn

    def update(self, hymn_id: str, hymn: Hymn) -> Hymn:
        with self._lock:
            existing = self.get(hymn_id)
            if existing.builtin:
                raise AppError("内置赞美诗为只读，请先复制后再编辑")
            conn = self._connect()
            hymn = hymn.model_copy(deep=True)
            hymn.id = hymn_id
            hymn.builtin = False
            conn.execute("DELETE FROM hymn_sections WHERE hymn_id=?", (hymn_id,))
            conn.execute("DELETE FROM hymns WHERE id=?", (hymn_id,))
            self._insert(hymn)
            conn.commit()
        return hymn

    def delete(self, hymn_id: str) -> None:
        with self._lock:
            existing = self.get(hymn_id)
            if existing.builtin:
                raise AppError("内置赞美诗不可删除")
            conn = self._connect()
            conn.execute("DELETE FROM hymn_sections WHERE hymn_id=?", (hymn_id,))
            conn.execute("DELETE FROM hymns WHERE id=?", (hymn_id,))
            conn.commit()

    def duplicate(self, hymn_id: str) -> Hymn:
        source = self.get(hymn_id)
        copy = source.model_copy(deep=True)
        copy.id = _new_id()
        copy.builtin = False
        copy.title = f"{source.title} 副本"
        with self._lock:
            self._insert(copy)
            self._connect().commit()
        return copy


hymn_store = HymnStore()
