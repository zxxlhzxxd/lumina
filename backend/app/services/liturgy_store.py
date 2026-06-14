"""Liturgy-text library backed by SQLite (built-in + user entries).

Shares the `library.db` file with the hymn store. Paragraphs are stored as a
JSON array column. Built-in texts are read-only but duplicable.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.data.liturgy_seed import builtin_liturgy_texts
from app.domain.library import LiturgyText

SCHEMA = """
CREATE TABLE IF NOT EXISTS liturgy_texts (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    paragraphs  TEXT NOT NULL DEFAULT '[]',
    builtin     INTEGER NOT NULL DEFAULT 0
);
"""


def _new_id() -> str:
    return uuid4().hex


class LiturgyStore:
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
            "SELECT COUNT(*) FROM liturgy_texts WHERE builtin=1"
        ).fetchone()
        if count:
            return
        for text in builtin_liturgy_texts():
            self._insert(text)
        self._conn.commit()

    def _row_to_text(self, row: sqlite3.Row) -> LiturgyText:
        try:
            paragraphs = json.loads(row["paragraphs"])
        except (json.JSONDecodeError, TypeError):
            paragraphs = []
        return LiturgyText(
            id=row["id"],
            title=row["title"],
            builtin=bool(row["builtin"]),
            paragraphs=paragraphs,
        )

    # ---- read ------------------------------------------------------------
    def list(self, query: str = "") -> List[LiturgyText]:
        conn = self._connect()
        q = (query or "").strip()
        if q:
            like = f"%{q}%"
            rows = conn.execute(
                "SELECT * FROM liturgy_texts WHERE title LIKE ? OR paragraphs LIKE ? "
                "ORDER BY builtin DESC, title",
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM liturgy_texts ORDER BY builtin DESC, title"
            ).fetchall()
        return [self._row_to_text(r) for r in rows]

    def get(self, text_id: str) -> LiturgyText:
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM liturgy_texts WHERE id=?", (text_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"礼文不存在: {text_id}")
        return self._row_to_text(row)

    # ---- write -----------------------------------------------------------
    def _insert(self, text: LiturgyText) -> None:
        conn = self._connect()
        conn.execute(
            "INSERT INTO liturgy_texts (id, title, paragraphs, builtin) VALUES (?, ?, ?, ?)",
            (
                text.id,
                text.title,
                json.dumps(text.paragraphs, ensure_ascii=False),
                1 if text.builtin else 0,
            ),
        )

    def create(self, text: LiturgyText) -> LiturgyText:
        with self._lock:
            text = text.model_copy(deep=True)
            text.id = _new_id()
            text.builtin = False
            self._insert(text)
            self._connect().commit()
        return text

    def update(self, text_id: str, text: LiturgyText) -> LiturgyText:
        with self._lock:
            existing = self.get(text_id)
            if existing.builtin:
                raise AppError("内置礼文为只读，请先复制后再编辑")
            conn = self._connect()
            text = text.model_copy(deep=True)
            text.id = text_id
            text.builtin = False
            conn.execute(
                "UPDATE liturgy_texts SET title=?, paragraphs=? WHERE id=?",
                (text.title, json.dumps(text.paragraphs, ensure_ascii=False), text_id),
            )
            conn.commit()
        return text

    def delete(self, text_id: str) -> None:
        with self._lock:
            existing = self.get(text_id)
            if existing.builtin:
                raise AppError("内置礼文不可删除")
            conn = self._connect()
            conn.execute("DELETE FROM liturgy_texts WHERE id=?", (text_id,))
            conn.commit()

    def duplicate(self, text_id: str) -> LiturgyText:
        source = self.get(text_id)
        copy = source.model_copy(deep=True)
        copy.id = _new_id()
        copy.builtin = False
        copy.title = f"{source.title} 副本"
        with self._lock:
            self._insert(copy)
            self._connect().commit()
        return copy


liturgy_store = LiturgyStore()
