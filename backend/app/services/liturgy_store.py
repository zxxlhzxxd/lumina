"""Liturgy-text library backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.domain.library import LiturgyText

SCHEMA = """
CREATE TABLE IF NOT EXISTS liturgy_texts (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    paragraphs  TEXT NOT NULL DEFAULT '[]'
);
"""


def _new_id() -> str:
    return uuid4().hex


def _clean_title(title: str) -> str:
    return (title or "").strip()


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
            self._migrate_schema()
        return self._conn

    def _migrate_schema(self) -> None:
        assert self._conn is not None
        conn = self._conn
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(liturgy_texts)")
        }
        self._merge_duplicate_titles()
        if "builtin" in columns:
            conn.execute("ALTER TABLE liturgy_texts RENAME TO liturgy_texts_old")
            conn.execute(
                """
                CREATE TABLE liturgy_texts (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    paragraphs  TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            conn.execute(
                "INSERT INTO liturgy_texts (id, title, paragraphs) "
                "SELECT id, title, paragraphs FROM liturgy_texts_old"
            )
            conn.execute("DROP TABLE liturgy_texts_old")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_liturgy_texts_title_unique "
            "ON liturgy_texts(title) WHERE title <> ''"
        )
        conn.commit()

    def _merge_duplicate_titles(self) -> None:
        assert self._conn is not None
        conn = self._conn
        rows = conn.execute(
            "SELECT rowid, id, title FROM liturgy_texts ORDER BY rowid"
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
                    conn.execute("DELETE FROM liturgy_texts WHERE id=?", (row["id"],))
                else:
                    conn.execute(
                        "UPDATE liturgy_texts SET title=? WHERE id=?",
                        (title, row["id"]),
                    )

    def _row_to_text(self, row: sqlite3.Row) -> LiturgyText:
        try:
            paragraphs = json.loads(row["paragraphs"])
        except (json.JSONDecodeError, TypeError):
            paragraphs = []
        return LiturgyText(
            id=row["id"],
            title=row["title"],
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
                "ORDER BY title",
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM liturgy_texts ORDER BY title"
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
            "INSERT INTO liturgy_texts (id, title, paragraphs) VALUES (?, ?, ?)",
            (
                text.id,
                text.title,
                json.dumps(text.paragraphs, ensure_ascii=False),
            ),
        )

    def create(self, text: LiturgyText) -> LiturgyText:
        with self._lock:
            text = text.model_copy(deep=True)
            text.title = _clean_title(text.title)
            if not text.title:
                raise AppError("请填写礼文标题")
            text.id = _new_id()
            conn = self._connect()
            try:
                self._insert(text)
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise AppError("礼文标题已存在") from exc
        return text

    def update(self, text_id: str, text: LiturgyText) -> LiturgyText:
        with self._lock:
            self.get(text_id)
            conn = self._connect()
            text = text.model_copy(deep=True)
            text.title = _clean_title(text.title)
            if not text.title:
                raise AppError("请填写礼文标题")
            text.id = text_id
            try:
                conn.execute(
                    "UPDATE liturgy_texts SET title=?, paragraphs=? WHERE id=?",
                    (
                        text.title,
                        json.dumps(text.paragraphs, ensure_ascii=False),
                        text_id,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise AppError("礼文标题已存在") from exc
        return text

    def delete(self, text_id: str) -> None:
        with self._lock:
            self.get(text_id)
            conn = self._connect()
            conn.execute("DELETE FROM liturgy_texts WHERE id=?", (text_id,))
            conn.commit()

    def duplicate(self, text_id: str) -> LiturgyText:
        source = self.get(text_id)
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
        while conn.execute(
            "SELECT 1 FROM liturgy_texts WHERE title=?", (candidate,)
        ).fetchone():
            candidate = f"{base} {index}"
            index += 1
        return candidate

    def upsert_by_title(self, text: LiturgyText) -> LiturgyText:
        title = _clean_title(text.title)
        if not title:
            raise AppError("请填写礼文标题")
        conn = self._connect()
        existing = conn.execute(
            "SELECT id FROM liturgy_texts WHERE title=?", (title,)
        ).fetchone()
        text = text.model_copy(deep=True)
        text.title = title
        if existing is None:
            return self.create(text)
        return self.update(existing["id"], text)

    # ---- import / export -------------------------------------------------
    def export_library(self, out_path: Path) -> tuple[Path, int]:
        """Export liturgy texts to a portable JSON file."""
        items = self.list()
        payload = {
            "kind": "liturgy_library",
            "schema_version": 1,
            "items": [t.model_dump() for t in items],
        }
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out_path, len(items)

    def import_library(self, in_path: Path) -> List[LiturgyText]:
        """Import a liturgy library file as new editable copies."""
        payload = self._read_library_payload(in_path)
        try:
            texts = [LiturgyText.model_validate(item) for item in payload["items"]]
        except Exception as exc:
            raise AppError("无效的礼文库文件：条目格式错误") from exc
        imported: List[LiturgyText] = []
        for text in texts:
            if not _clean_title(text.title):
                raise AppError("无效的礼文库文件：礼文标题不能为空")
            imported.append(text)

        with self._lock:
            conn = self._connect()
            try:
                saved = [self._upsert_by_title_unlocked(text) for text in imported]
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return saved

    def _upsert_by_title_unlocked(self, text: LiturgyText) -> LiturgyText:
        assert self._conn is not None
        title = _clean_title(text.title)
        if not title:
            raise AppError("请填写礼文标题")
        conn = self._conn
        existing = conn.execute(
            "SELECT id FROM liturgy_texts WHERE title=?", (title,)
        ).fetchone()
        text = text.model_copy(deep=True)
        text.title = title
        text.id = existing["id"] if existing is not None else _new_id()
        conn.execute("DELETE FROM liturgy_texts WHERE id=?", (text.id,))
        self._insert(text)
        return text

    def _read_library_payload(self, in_path: Path) -> dict[str, Any]:
        in_path = Path(in_path)
        if not in_path.exists():
            raise AppError(f"礼文库文件不存在: {in_path}")
        try:
            payload = json.loads(in_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AppError("无效的礼文库文件") from exc
        if not isinstance(payload, dict):
            raise AppError("无效的礼文库文件")
        if payload.get("kind") != "liturgy_library":
            raise AppError("无效的礼文库文件：类型不匹配")
        if payload.get("schema_version") != 1:
            raise AppError("不支持的礼文库文件版本")
        if not isinstance(payload.get("items"), list):
            raise AppError("无效的礼文库文件：缺少 items")
        return payload


liturgy_store = LiturgyStore()
