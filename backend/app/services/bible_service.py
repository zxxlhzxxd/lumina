"""Bible data access + reference resolution.

Owns the SQLite connection, the book-alias index used for parsing, and the
logic that turns a parsed reference into concrete verses.
"""
from __future__ import annotations

import sqlite3
import threading
from typing import List, Optional, Tuple

from app.core.config import settings
from app.core.errors import BibleNotAvailableError, InvalidReferenceError
from app.domain.bible import BibleReference, Book, RangeRef, Verse, VerseRef
from app.services import reference_parser
from app.services.reference_parser import ParsedReference, RawRange


class BibleService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        # alias (normalized) -> (book_id, canonical_name), longest alias first
        self._aliases: List[Tuple[str, int, str]] = []
        self._loaded = False

    # ---- lifecycle -------------------------------------------------------
    def is_available(self) -> bool:
        return settings.bible_db_path.exists()

    def _connect(self) -> sqlite3.Connection:
        if not self.is_available():
            raise BibleNotAvailableError(
                "圣经数据未就绪，请先运行 `python -m app.data.import_bible` 导入和合本数据。"
            )
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(settings.bible_db_path), check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_index(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            conn = self._connect()
            rows = conn.execute(
                "SELECT id, name, short_names FROM books ORDER BY book_order"
            ).fetchall()
            aliases: List[Tuple[str, int, str]] = []
            for row in rows:
                names = [row["name"]] + [
                    a for a in row["short_names"].split(",") if a
                ]
                for alias in names:
                    aliases.append((alias, row["id"], row["name"]))
            # Longest alias first so 约翰福音 wins over 约.
            aliases.sort(key=lambda t: len(t[0]), reverse=True)
            self._aliases = aliases
            self._loaded = True

    # ---- queries ---------------------------------------------------------
    def get_books(self) -> List[Book]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT id, name, short_names, book_order, chapter_count "
            "FROM books ORDER BY book_order"
        ).fetchall()
        return [
            Book(
                id=r["id"],
                name=r["name"],
                short_names=[a for a in r["short_names"].split(",") if a],
                order=r["book_order"],
                chapter_count=r["chapter_count"],
            )
            for r in rows
        ]

    def get_chapters(self, book_id: int) -> List[dict]:
        """Per-chapter verse counts for a book, ordered by chapter."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT chapter, COUNT(*) AS verse_count FROM verses "
            "WHERE book_id=? GROUP BY chapter ORDER BY chapter",
            (book_id,),
        ).fetchall()
        return [
            {"chapter": r["chapter"], "verse_count": r["verse_count"]} for r in rows
        ]

    def _match_book(self, text: str):
        self._ensure_index()
        for alias, book_id, name in self._aliases:
            if text.startswith(alias):
                return book_id, name, text[len(alias):]
        return None

    def _last_verse(self, book_id: int, chapter: int) -> Optional[int]:
        conn = self._connect()
        row = conn.execute(
            "SELECT MAX(verse) AS m FROM verses WHERE book_id=? AND chapter=?",
            (book_id, chapter),
        ).fetchone()
        return row["m"] if row and row["m"] is not None else None

    def _resolve_range(self, book_id: int, rng: RawRange) -> RangeRef:
        start_last = self._last_verse(book_id, rng.start_chapter)
        if start_last is None:
            raise InvalidReferenceError(f"章不存在: 第 {rng.start_chapter} 章")
        end_last = self._last_verse(book_id, rng.end_chapter)
        if end_last is None:
            raise InvalidReferenceError(f"章不存在: 第 {rng.end_chapter} 章")

        sv = rng.start_verse if rng.start_verse is not None else 1
        ev = rng.end_verse if rng.end_verse is not None else end_last

        if sv < 1 or sv > start_last:
            raise InvalidReferenceError(
                f"节不存在: 第 {rng.start_chapter} 章第 {sv} 节"
            )
        # Clamp the end verse to the chapter's last verse.
        ev = max(1, min(ev, end_last))

        if (rng.start_chapter, sv) > (rng.end_chapter, ev):
            raise InvalidReferenceError("引用范围起点晚于终点")

        return RangeRef(
            start=VerseRef(chapter=rng.start_chapter, verse=sv),
            end=VerseRef(chapter=rng.end_chapter, verse=ev),
        )

    @staticmethod
    def _format_ranges(book_name: str, ranges: List[RangeRef]) -> str:
        parts: List[str] = []
        for r in ranges:
            if r.start.chapter == r.end.chapter:
                if r.start.verse == r.end.verse:
                    parts.append(f"{r.start.chapter}:{r.start.verse}")
                else:
                    parts.append(
                        f"{r.start.chapter}:{r.start.verse}-{r.end.verse}"
                    )
            else:
                parts.append(
                    f"{r.start.chapter}:{r.start.verse}-{r.end.chapter}:{r.end.verse}"
                )
        return f"{book_name} {','.join(parts)}"

    def parse_reference(self, raw: str) -> BibleReference:
        parsed: ParsedReference = reference_parser.parse(raw, self._match_book)
        ranges = [self._resolve_range(parsed.book_id, r) for r in parsed.ranges]
        return BibleReference(
            book_id=parsed.book_id,
            book_name=parsed.book_name,
            ranges=ranges,
            display=self._format_ranges(parsed.book_name, ranges),
        )

    def get_verses(self, ref: BibleReference) -> List[Verse]:
        conn = self._connect()
        verses: List[Verse] = []
        for r in ref.ranges:
            rows = conn.execute(
                "SELECT chapter, verse, text FROM verses "
                "WHERE book_id=? AND "
                "( chapter>? OR (chapter=? AND verse>=?) ) AND "
                "( chapter<? OR (chapter=? AND verse<=?) ) "
                "ORDER BY chapter, verse",
                (
                    ref.book_id,
                    r.start.chapter,
                    r.start.chapter,
                    r.start.verse,
                    r.end.chapter,
                    r.end.chapter,
                    r.end.verse,
                ),
            ).fetchall()
            for row in rows:
                verses.append(
                    Verse(
                        book_id=ref.book_id,
                        book_name=ref.book_name,
                        chapter=row["chapter"],
                        verse=row["verse"],
                        text=row["text"],
                    )
                )
        return verses

    def get_passage(self, raw: str) -> Tuple[BibleReference, List[Verse]]:
        ref = self.parse_reference(raw)
        return ref, self.get_verses(ref)


bible_service = BibleService()
