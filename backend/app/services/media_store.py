"""Per-working-directory media management.

Every project/template working directory has a `media/` subfolder. Media is
referenced from the domain model by container-relative paths of the form
`media/<file>`. This module owns importing files into that folder, resolving
refs back to absolute paths, and collecting/rewriting refs across a section list.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from app.core.errors import AppError, NotFoundError

MEDIA_DIRNAME = "media"
MEDIA_PREFIX = "media/"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}
ALLOWED_EXTS = IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS


def media_dir(work_dir: Path) -> Path:
    d = work_dir / MEDIA_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_name(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
    return cleaned or "media"


def import_media(work_dir: Path, source_path: str) -> str:
    """Copy a local file into `work_dir/media/`, returning its `media/<file>` ref."""
    src = Path(source_path).expanduser()
    if not src.exists() or not src.is_file():
        raise NotFoundError(f"媒体文件不存在: {source_path}")
    ext = src.suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise AppError(f"不支持的媒体格式: {ext or '未知'}")
    dest_dir = media_dir(work_dir)
    name = _safe_name(src.name)
    dest = dest_dir / name
    if dest.exists():
        # Avoid clobbering a different file with the same name.
        name = f"{uuid4().hex[:8]}_{name}"
        dest = dest_dir / name
    shutil.copy2(src, dest)
    return f"{MEDIA_PREFIX}{name}"


def media_path(work_dir: Path, ref: str) -> Optional[Path]:
    """Resolve a `media/<file>` ref to an absolute path inside `work_dir`.

    Returns None for empty refs; raises on path traversal attempts.
    """
    if not ref:
        return None
    rel = ref
    if rel.startswith(MEDIA_PREFIX):
        rel = rel[len(MEDIA_PREFIX):]
    candidate = (work_dir / MEDIA_DIRNAME / rel).resolve()
    base = (work_dir / MEDIA_DIRNAME).resolve()
    if base not in candidate.parents and candidate != base:
        raise AppError("非法的媒体路径")
    return candidate


def _section_refs(section) -> List[str]:
    refs: List[str] = []
    style = getattr(section, "style", None)
    if style is not None:
        for attr in ("background_image", "background_video"):
            value = getattr(style, attr, None)
            if value:
                refs.append(value)
    audio = getattr(section, "audio_ref", None)
    if audio:
        refs.append(audio)
    return refs


def collect_media_refs(sections: Iterable) -> List[str]:
    """Distinct media refs referenced by a list of sections (preserving order)."""
    seen: List[str] = []
    for section in sections:
        for ref in _section_refs(section):
            if ref.startswith(MEDIA_PREFIX) and ref not in seen:
                seen.append(ref)
    return seen


def rewrite_media_refs(sections: Iterable, mapping: Dict[str, str]) -> None:
    """Replace media refs in-place according to `mapping` (old ref -> new ref)."""
    for section in sections:
        style = getattr(section, "style", None)
        if style is not None:
            for attr in ("background_image", "background_video"):
                value = getattr(style, attr, None)
                if value and value in mapping:
                    setattr(style, attr, mapping[value])
        audio = getattr(section, "audio_ref", None)
        if audio and audio in mapping:
            section.audio_ref = mapping[audio]


def copy_media(
    src_work_dir: Path, dest_work_dir: Path, refs: Iterable[str]
) -> Dict[str, str]:
    """Copy referenced media files from one working dir to another.

    Returns a mapping of old ref -> new ref (names may change on collision).
    """
    mapping: Dict[str, str] = {}
    dest_dir = media_dir(dest_work_dir)
    for ref in refs:
        src = media_path(src_work_dir, ref)
        if src is None or not src.exists():
            continue
        name = src.name
        dest = dest_dir / name
        if dest.exists() and dest.stat().st_size != src.stat().st_size:
            name = f"{uuid4().hex[:8]}_{name}"
            dest = dest_dir / name
        if not dest.exists():
            shutil.copy2(src, dest)
        mapping[ref] = f"{MEDIA_PREFIX}{name}"
    return mapping
