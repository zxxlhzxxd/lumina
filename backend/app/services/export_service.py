"""Export a Project to a .pptx file, with pre-export validation."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from app.core.errors import AppError, ExportError
from app.domain.project import Project
from app.domain.sections import (
    CoverSection,
    MediaSection,
    ResponsiveReadingSection,
    ScriptureSection,
)
from app.pptx.builder import build_pptx
from app.services import media_store
from app.services.bible_service import bible_service
from app.services.generation import build_slides

AUDIO_EXPORT_EXTS = {".mp3", ".wav"}


def validate_project(
    project: Project,
    media_root: Optional[Path] = None,
) -> List[dict]:
    """Return a list of {level, section_id, message} issues (non-fatal warnings)."""
    issues: List[dict] = []
    for section in project.sections:
        if not section.enabled:
            continue
        if isinstance(section, (ResponsiveReadingSection, ScriptureSection)):
            ref = section.reference.strip()
            if not ref:
                issues.append(
                    {
                        "level": "warning",
                        "section_id": section.id,
                        "message": f"段落「{section.title or section.type.value}」未填写经文引用",
                    }
                )
                continue
            try:
                bible_service.parse_reference(ref)
            except AppError as e:
                issues.append(
                    {
                        "level": "error",
                        "section_id": section.id,
                        "message": f"经文引用无效: {ref} — {e.message}",
                    }
                )
        if isinstance(section, CoverSection) and not section.main_title.strip():
            issues.append(
                {
                    "level": "warning",
                    "section_id": section.id,
                    "message": "封面/标题页未填写标题",
                }
            )
        if isinstance(section, MediaSection) and section.audio_ref:
            if media_root is None:
                issues.append(
                    {
                        "level": "error",
                        "section_id": section.id,
                        "message": "音频导出需要先保存工程",
                    }
                )
                continue
            try:
                path = media_store.media_path(media_root, section.audio_ref)
            except AppError as e:
                issues.append(
                    {
                        "level": "error",
                        "section_id": section.id,
                        "message": f"音频路径无效: {e.message}",
                    }
                )
                continue
            if path is None or not path.exists():
                issues.append(
                    {
                        "level": "error",
                        "section_id": section.id,
                        "message": f"音频文件不存在: {section.audio_ref}",
                    }
                )
                continue
            if path.suffix.lower() not in AUDIO_EXPORT_EXTS:
                issues.append(
                    {
                        "level": "error",
                        "section_id": section.id,
                        "message": "音频导出仅支持 mp3 / wav，请重新选择音频文件",
                    }
                )
    return issues


def export_project(
    project: Project,
    out_path: Path,
    media_root: Optional[Path] = None,
) -> Path:
    try:
        issues = validate_project(project, media_root=media_root)
        errors = [issue for issue in issues if issue.get("level") == "error"]
        if errors:
            raise ExportError(errors[0]["message"], details={"issues": errors})
        slides = build_slides(project)
        return build_pptx(slides, out_path, project.slide_size, media_root=media_root)
    except AppError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ExportError(f"生成 PPTX 失败: {e}") from e
