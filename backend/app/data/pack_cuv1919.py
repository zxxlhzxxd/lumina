"""Pack an existing Simplified 1919 CUV Shen TeX corpus into `.lumina-bible`.

This is a maintainer tool. It strips TeX wrappers only and does not convert
characters, wording, punctuation, or 神/上帝.

Source layout (Urantiapedia `input/tex/bible-zh`):

    \\chapter{1}
    \\par 1 起初，神创造天地。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from app.data.books import BOOKS, OSIS_BY_ID

CHAPTER_RE = re.compile(r"^\\chapter\{(\d+)\}\s*$")
VERSE_RE = re.compile(r"^\\par\s+(\d+)\s+(.*)$")

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "cuv-1919-shen-hans.lumina-bible"

SOURCE_NAME = "Urantiapedia bible-zh（简体和合本神版电子文本）"
SOURCE_URL = (
    "https://github.com/JanHerca/urantiapedia/tree/master/input/tex/bible-zh"
)


def _parse_book(path: Path) -> List[Dict[str, Any]]:
    chapters: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip("\n")
        ch = CHAPTER_RE.match(line)
        if ch:
            current = {"chapter": int(ch.group(1)), "verses": []}
            chapters.append(current)
            continue
        verse = VERSE_RE.match(line)
        if verse:
            if current is None:
                raise ValueError(f"{path.name}:{line_no} 节出现在章标题之前")
            current["verses"].append(
                {"verse": int(verse.group(1)), "text": verse.group(2).strip()}
            )
            continue
    if not chapters:
        raise ValueError(f"{path.name} 未解析到任何章")
    for chapter in chapters:
        if not chapter["verses"]:
            raise ValueError(f"{path.name} 第 {chapter['chapter']} 章没有经文")
    return chapters


def pack(source_dir: Path, output: Path, source_revision: str) -> Path:
    files = sorted(source_dir.glob("*.tex"))
    if len(files) != 66:
        raise ValueError(f"期望 66 个 .tex，实际 {len(files)}: {source_dir}")

    books: List[Dict[str, Any]] = []
    chapter_total = 0
    verse_total = 0
    for index, (book_id, name, shorts) in enumerate(BOOKS):
        path = files[index]
        prefix = f"{book_id:03d}_"
        if not path.name.startswith(prefix):
            raise ValueError(
                f"书卷文件名与 id 不对齐: id={book_id} file={path.name}"
            )
        chapters = _parse_book(path)
        chapter_total += len(chapters)
        verse_total += sum(len(ch["verses"]) for ch in chapters)
        books.append(
            {
                "id": book_id,
                "osis": OSIS_BY_ID[book_id],
                "name": name,
                "short_names": list(shorts),
                "chapters": chapters,
            }
        )

    payload = {
        "format": "lumina-bible",
        "format_version": 1,
        "translation": {
            "id": "cuv-1919-shen-hans",
            "name": "和合本1919（神版）",
            "short_name": "和合本1919神版",
            "language": "zh-Hans",
            "year": 1919,
            "god_term": "shen",
            "license": "public-domain",
            "license_note": (
                "1919 官话和合本神版，公有领域。简体电子文本，未经本仓库繁简转换。"
            ),
            "source_name": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "source_revision": source_revision,
        },
        "canon": "protestant-66",
        "stats": {
            "books": len(books),
            "chapters": chapter_total,
            "verses": verse_total,
        },
        "books": books,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(
        f"写入 {output} （书卷 {len(books)}, 章 {chapter_total}, 节 {verse_total}）"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将现成简体 1919 神版 TeX 打包为 .lumina-bible（不改汉字）"
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="含 001_Genesis.tex … 的目录（现成简体源，本脚本不转换汉字）",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source-revision",
        default="",
        help="上游 git commit，写入 translation.source_revision",
    )
    args = parser.parse_args()
    pack(args.source_dir, args.output, args.source_revision.strip())


if __name__ == "__main__":
    main()
