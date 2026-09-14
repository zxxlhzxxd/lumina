"""Build the local Bible SQLite database from a `.lumina-bible` source.

Default source is the bundled 1919 和合本神版 (Simplified, public domain).
Do not download Bible text at import time.

Usage:
    python -m app.data.import_bible
    python -m app.data.import_bible --source path/to/file.lumina-bible
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings
from app.data.books import ID_TO_NAME, ID_TO_SHORTS
from app.data.lumina_bible import (
    DEFAULT_SOURCE,
    DEFAULT_TRANSLATION_ID,
    LuminaBibleError,
    gold_probe_cuv1919_shen,
    load_lumina_bible,
    translation_meta,
    validate_structure,
)

SCHEMA = """
CREATE TABLE bible_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
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
CREATE INDEX idx_verses_book_chapter ON verses (book_id, chapter);
"""


def write_sqlite(data: dict, db_path: Path) -> Tuple[int, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    chapter_total, verse_total = validate_structure(data)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        meta = translation_meta(data)
        meta["chapters"] = str(chapter_total)
        meta["verses"] = str(verse_total)
        meta["books"] = str(len(data["books"]))
        conn.executemany(
            "INSERT INTO bible_meta (key, value) VALUES (?, ?)",
            list(meta.items()),
        )
        for book in data["books"]:
            bid = int(book["id"])
            chapters = book["chapters"]
            conn.execute(
                "INSERT INTO books (id, name, short_names, book_order, chapter_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    bid,
                    ID_TO_NAME[bid],
                    ",".join(ID_TO_SHORTS[bid]),
                    bid,
                    len(chapters),
                ),
            )
            rows = []
            for chapter in chapters:
                cnum = int(chapter["chapter"])
                for verse in chapter["verses"]:
                    rows.append(
                        (bid, cnum, int(verse["verse"]), verse["text"])
                    )
            conn.executemany(
                "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
                rows,
            )
        conn.commit()
    finally:
        conn.close()
    return chapter_total, verse_total


def build(
    source: Optional[Path] = None,
    db_path: Optional[Path] = None,
    *,
    apply_gold: Optional[bool] = None,
) -> Path:
    source_path = Path(source) if source else DEFAULT_SOURCE
    db_path = db_path or settings.bible_db_path
    data = load_lumina_bible(source_path)
    translation_id = str((data.get("translation") or {}).get("id") or "")
    if apply_gold is None:
        apply_gold = translation_id == DEFAULT_TRANSLATION_ID
    if apply_gold:
        problems = gold_probe_cuv1919_shen(data)
        if problems:
            raise LuminaBibleError(
                "1919 神版探针失败:\n  " + "\n  ".join(problems)
            )

    print(f"读取圣经源: {source_path}")
    chapter_total, verse_total = write_sqlite(data, db_path)
    print(
        f"完成: {db_path} (书卷 {len(data['books'])}, "
        f"章 {chapter_total}, 节 {verse_total})"
    )
    if translation_id and translation_id != DEFAULT_TRANSLATION_ID:
        print(
            f"译本: {translation_id}。"
            "自制源未套用 1919 神版用字探针；请确认你有权分发该文本。"
        )
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 .lumina-bible 生成 bible.sqlite"
    )
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        default=None,
        help="圣经源文件（.lumina-bible）。省略则使用捆绑的 1919 神版",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="输出 sqlite 路径，默认 backend/app/data/bible.sqlite",
    )
    args = parser.parse_args()
    try:
        build(args.source, args.db)
    except LuminaBibleError as exc:
        raise SystemExit(f"导入失败: {exc}") from exc


if __name__ == "__main__":
    main()
