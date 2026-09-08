"""Load and validate Lumina `.lumina-bible` files.

The interchange format is UTF-8 JSON with `format: lumina-bible`. Import maps
book ids 1–66 onto `books.py` names so reference parsing stays stable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from app.data.books import BOOKS, ID_TO_NAME

FORMAT_NAME = "lumina-bible"
SUPPORTED_FORMAT_VERSIONS = {1}
PROTESTANT_BOOK_COUNT = 66
DEFAULT_SOURCE = Path(__file__).resolve().parent / "cuv-1919-shen-hans.lumina-bible"
DEFAULT_TRANSLATION_ID = "cuv-1919-shen-hans"

GOLD_CUV1919_SHEN = [
    # (book_id, chapter, verse, must_contain, must_not_contain)
    (1, 2, 22, "领他到那人跟前", "领她"),
    (44, 9, 2, "大马色", "大马士革"),
    (1, 1, 26, "形像", "形象"),
    (43, 3, 16, "不至灭亡", "不致灭亡"),
]
GOLD_CUV1919_CHAPTERS = 1189
GOLD_CUV1919_VERSES = 31101


class LuminaBibleError(ValueError):
    """Invalid `.lumina-bible` contents or 1919 gold-probe failure."""


def load_lumina_bible(path: Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise LuminaBibleError(f"找不到圣经源文件: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LuminaBibleError(f"不是合法 JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LuminaBibleError("圣经源根节点必须是对象")
    return data


def _require(mapping: Mapping[str, Any], key: str, ctx: str) -> Any:
    if key not in mapping:
        raise LuminaBibleError(f"{ctx}缺少字段 `{key}`")
    return mapping[key]


def validate_structure(data: Mapping[str, Any]) -> Tuple[int, int]:
    """Return (chapter_total, verse_total). Raises on structural errors."""
    if data.get("format") != FORMAT_NAME:
        raise LuminaBibleError(
            f"format 必须是 `{FORMAT_NAME}`，实际: {data.get('format')!r}"
        )
    version = data.get("format_version")
    if version not in SUPPORTED_FORMAT_VERSIONS:
        raise LuminaBibleError(f"不支持的 format_version: {version!r}")
    if data.get("canon") not in (None, "protestant-66"):
        raise LuminaBibleError(f"v1 仅支持 canon=protestant-66，实际: {data.get('canon')!r}")

    translation = _require(data, "translation", "根对象")
    if not isinstance(translation, dict):
        raise LuminaBibleError("translation 必须是对象")
    _require(translation, "id", "translation")
    _require(translation, "name", "translation")

    books = _require(data, "books", "根对象")
    if not isinstance(books, list):
        raise LuminaBibleError("books 必须是数组")
    if len(books) != PROTESTANT_BOOK_COUNT:
        raise LuminaBibleError(
            f"书卷数必须为 {PROTESTANT_BOOK_COUNT}，实际 {len(books)}"
        )

    seen_ids = set()
    chapter_total = 0
    verse_total = 0
    expected_ids = {bid for bid, _, _ in BOOKS}
    for book in books:
        if not isinstance(book, dict):
            raise LuminaBibleError("books 中的每一项必须是对象")
        bid = _require(book, "id", "book")
        if not isinstance(bid, int) or bid not in expected_ids:
            raise LuminaBibleError(f"非法 book.id: {bid!r}")
        if bid in seen_ids:
            raise LuminaBibleError(f"重复的 book.id: {bid}")
        seen_ids.add(bid)
        chapters = _require(book, "chapters", f"book {bid}")
        if not isinstance(chapters, list) or not chapters:
            raise LuminaBibleError(f"book {bid} 至少需要一章")
        chapter_total += len(chapters)
        seen_chapters = set()
        for chapter in chapters:
            if not isinstance(chapter, dict):
                raise LuminaBibleError(f"book {bid} 的 chapters 项必须是对象")
            cnum = _require(chapter, "chapter", f"book {bid}")
            if not isinstance(cnum, int) or cnum < 1:
                raise LuminaBibleError(f"book {bid} 非法 chapter: {cnum!r}")
            if cnum in seen_chapters:
                raise LuminaBibleError(f"book {bid} 重复章号 {cnum}")
            seen_chapters.add(cnum)
            verses = _require(chapter, "verses", f"book {bid} ch {cnum}")
            if not isinstance(verses, list) or not verses:
                raise LuminaBibleError(f"book {bid} 第 {cnum} 章没有经文")
            seen_verses = set()
            for verse in verses:
                if not isinstance(verse, dict):
                    raise LuminaBibleError(
                        f"book {bid} {cnum} 章 verses 项必须是对象"
                    )
                vnum = _require(verse, "verse", f"book {bid} {cnum}")
                if not isinstance(vnum, int) or vnum < 1:
                    raise LuminaBibleError(
                        f"book {bid} {cnum} 章非法节号: {vnum!r}"
                    )
                if vnum in seen_verses:
                    raise LuminaBibleError(
                        f"book {bid} {cnum}:{vnum} 重复"
                    )
                seen_verses.add(vnum)
                text = _require(verse, "text", f"book {bid} {cnum}:{vnum}")
                if not isinstance(text, str) or not text.strip():
                    raise LuminaBibleError(
                        f"book {bid} {cnum}:{vnum} 经文为空"
                    )
                verse_total += 1
    missing = expected_ids - seen_ids
    if missing:
        raise LuminaBibleError(f"缺少书卷 id: {sorted(missing)}")
    return chapter_total, verse_total


def iter_verse_texts(data: Mapping[str, Any]) -> Iterable[str]:
    for book in data.get("books", []):
        for chapter in book.get("chapters", []):
            for verse in chapter.get("verses", []):
                text = verse.get("text")
                if isinstance(text, str):
                    yield text


def get_verse_text(
    data: Mapping[str, Any], book_id: int, chapter: int, verse: int
) -> Optional[str]:
    for book in data.get("books", []):
        if book.get("id") != book_id:
            continue
        for ch in book.get("chapters", []):
            if ch.get("chapter") != chapter:
                continue
            for item in ch.get("verses", []):
                if item.get("verse") == verse:
                    text = item.get("text")
                    return text if isinstance(text, str) else None
    return None


def gold_probe_cuv1919_shen(data: Mapping[str, Any]) -> List[str]:
    """Wording probes that distinguish 1919 神版 from 新标点 / mixed dumps."""
    problems: List[str] = []
    for book_id, chapter, verse, must, must_not in GOLD_CUV1919_SHEN:
        text = get_verse_text(data, book_id, chapter, verse)
        label = f"{ID_TO_NAME.get(book_id, book_id)} {chapter}:{verse}"
        if text is None:
            problems.append(f"{label} 缺失")
            continue
        if must not in text:
            problems.append(f"{label} 应包含 {must!r}，实际: {text}")
        if must_not in text:
            problems.append(f"{label} 不应包含 {must_not!r}，实际: {text}")

    joined = "".join(iter_verse_texts(data))
    for token, label in (("她", "她"), ("上帝", "上帝")):
        count = joined.count(token)
        if count:
            problems.append(f"全库出现 {count} 次「{label}」，1919 神版应为 0")

    chapter_total = 0
    verse_total = 0
    for book in data.get("books", []):
        chapters = book.get("chapters") or []
        chapter_total += len(chapters)
        for chapter in chapters:
            verse_total += len(chapter.get("verses") or [])
    if chapter_total != GOLD_CUV1919_CHAPTERS:
        problems.append(
            f"章数={chapter_total} 期望={GOLD_CUV1919_CHAPTERS}"
        )
    if verse_total != GOLD_CUV1919_VERSES:
        problems.append(
            f"节数={verse_total} 期望={GOLD_CUV1919_VERSES}"
        )
    return problems


def translation_meta(data: Mapping[str, Any]) -> Dict[str, str]:
    translation = data.get("translation") or {}
    stats = data.get("stats") or {}
    fields = {
        "id": translation.get("id"),
        "name": translation.get("name"),
        "short_name": translation.get("short_name") or translation.get("name"),
        "language": translation.get("language"),
        "year": translation.get("year"),
        "god_term": translation.get("god_term"),
        "license": translation.get("license"),
        "license_note": translation.get("license_note"),
        "source_name": translation.get("source_name"),
        "source_url": translation.get("source_url"),
        "source_revision": translation.get("source_revision"),
        "canon": data.get("canon"),
        "format_version": data.get("format_version"),
        "books": stats.get("books"),
        "chapters": stats.get("chapters"),
        "verses": stats.get("verses"),
    }
    return {key: "" if value is None else str(value) for key, value in fields.items()}
