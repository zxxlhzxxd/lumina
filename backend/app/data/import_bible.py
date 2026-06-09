"""Build the local Bible SQLite database (Chinese Union Version, Simplified).

Source: midvash/bible-data `cuvs` (public domain, 1919 Chinese Union Version,
Simplified script). The single-file JSON has the schema:

    { "books": [ { "bookId": int, "chapters": [ { "chapter": int,
                  "verses": [ { "number": int, "text": str } ] } ] } ] }

Usage:
    python -m app.data.import_bible                 # download + build
    python -m app.data.import_bible path/to/cuvs.json   # build from local file

The generated `bible.sqlite` is intentionally NOT committed to git; run this
script once per machine/build.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import urllib.request
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.data.books import BOOKS, ID_TO_NAME, ID_TO_SHORTS

SOURCE_URL = "https://raw.githubusercontent.com/midvash/bible-data/main/versions/zh/cuvs/cuvs.json"

EXPECTED_BOOKS = 66
EXPECTED_CHAPTERS = 1189
EXPECTED_VERSES = 31021

SCHEMA = """
CREATE TABLE books (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    short_names   TEXT NOT NULL,   -- comma-separated aliases
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


def _load_source(path: Optional[str]) -> dict:
    if path:
        print(f"读取本地数据: {path}")
        return json.loads(Path(path).read_text(encoding="utf-8"))
    print(f"下载和合本(简体)数据: {SOURCE_URL}")
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def build(path: Optional[str] = None, db_path: Optional[Path] = None) -> Path:
    data = _load_source(path)
    books = data["books"]

    db_path = db_path or settings.bible_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)

        chapter_total = 0
        verse_total = 0
        for book in books:
            bid = int(book["bookId"])
            if bid not in ID_TO_NAME:
                raise ValueError(f"未知 bookId: {bid}")
            chapters = book["chapters"]
            chapter_count = len(chapters)
            chapter_total += chapter_count
            conn.execute(
                "INSERT INTO books (id, name, short_names, book_order, chapter_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    bid,
                    ID_TO_NAME[bid],
                    ",".join(ID_TO_SHORTS[bid]),
                    bid,
                    chapter_count,
                ),
            )
            rows = []
            for ch in chapters:
                cnum = int(ch["chapter"])
                for v in ch["verses"]:
                    rows.append((bid, cnum, int(v["number"]), v["text"]))
            conn.executemany(
                "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
                rows,
            )
            verse_total += len(rows)

        conn.commit()
    finally:
        conn.close()

    _verify(db_path, chapter_total, verse_total)
    print(
        f"完成: {db_path} (书卷 {len(books)}, 章 {chapter_total}, 节 {verse_total})"
    )
    return db_path


def _verify(db_path: Path, chapters: int, verses: int) -> None:
    conn = sqlite3.connect(db_path)
    try:
        (n_books,) = conn.execute("SELECT COUNT(*) FROM books").fetchone()
        (n_verses,) = conn.execute("SELECT COUNT(*) FROM verses").fetchone()
    finally:
        conn.close()

    problems = []
    if n_books != EXPECTED_BOOKS:
        problems.append(f"书卷数={n_books} 期望={EXPECTED_BOOKS}")
    if chapters != EXPECTED_CHAPTERS:
        problems.append(f"章数={chapters} 期望={EXPECTED_CHAPTERS}")
    if n_verses != EXPECTED_VERSES:
        problems.append(f"节数={n_verses} 期望={EXPECTED_VERSES}")
    if len(BOOKS) != EXPECTED_BOOKS:
        problems.append(f"元数据书卷数={len(BOOKS)} 期望={EXPECTED_BOOKS}")
    if problems:
        # Warn but don't fail hard — source counts can differ slightly by edition.
        print("警告: 完整性校验未完全匹配:\n  " + "\n  ".join(problems))


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else None
    build(path)


if __name__ == "__main__":
    main()
