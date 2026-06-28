"""Service (worship-flow) templates: built-in (read-only) + user templates.

User templates live in `templates/<id>/` (template.json + media/) and can be
created, edited, duplicated, saved from a project, and imported/exported as a
`.lumina` zip container bundling all referenced media.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.data.liturgy_seed import APOSTLES_CREED, GLORIA, LORDS_PRAYER
from app.domain.enums import PlayMode, SlideSize
from app.domain.project import Project, ServiceTemplate
from app.domain.sections import (
    AnnouncementSection,
    CoverSection,
    HymnSection,
    LiturgyTextSection,
    MediaSection,
    ResponsiveReadingSection,
    ScriptureSection,
)
from app.services import container, media_store

logger = logging.getLogger(__name__)

TEMPLATE_JSON = "template.json"
BUILTIN_SUNDAY_ID = "builtin-sunday"


def _new_id() -> str:
    return uuid4().hex


def _default_sunday_template() -> ServiceTemplate:
    sections = [
        CoverSection(title="礼拜封面", main_title="主日崇拜", sub_title=""),
        MediaSection(
            title="媒体：起立默祷",
            slide_title="起立默祷",
            body="请起立默祷",
            play_mode=PlayMode.ONCE,
        ),
        ResponsiveReadingSection(title="启应经文", reference=""),
        LiturgyTextSection(
            title="礼文：使徒信经",
            slide_title="使徒信经",
            liturgy_id="builtin-apostles-creed",
            paragraphs=list(APOSTLES_CREED),
        ),
        HymnSection(title="赞美诗（一）", song_title=""),
        HymnSection(title="赞美诗（二）", song_title=""),
        HymnSection(title="赞美诗（三）", song_title=""),
        LiturgyTextSection(title="礼文：祷告", slide_title="祷告", paragraphs=[]),
        LiturgyTextSection(
            title="礼文：荣耀颂",
            slide_title="荣耀颂",
            liturgy_id="builtin-gloria",
            paragraphs=list(GLORIA),
        ),
        ScriptureSection(title="证道经文", reference=""),
        CoverSection(title="证道题目", main_title=""),
        LiturgyTextSection(title="礼文：回应祷告", slide_title="回应祷告", paragraphs=[]),
        HymnSection(title="回应诗歌", song_title=""),
        AnnouncementSection(title="家事报告", heading="家事报告", items=[]),
        HymnSection(title="结束诗歌", song_title=""),
        LiturgyTextSection(
            title="礼文：主祷文",
            slide_title="主祷文",
            liturgy_id="builtin-lords-prayer",
            paragraphs=list(LORDS_PRAYER),
        ),
        MediaSection(
            title="媒体：阿门颂",
            slide_title="阿门颂",
            body="",
            play_mode=PlayMode.ONCE,
        ),
    ]
    return ServiceTemplate(
        id=BUILTIN_SUNDAY_ID,
        name="主日崇拜（默认）",
        builtin=True,
        description="标准主日崇拜流程模板",
        slide_size=SlideSize.WIDE,
        sections=sections,
    )


class TemplateStore:
    def __init__(self) -> None:
        self._builtin_ids = {BUILTIN_SUNDAY_ID}

    # ---- working dirs ----------------------------------------------------
    def work_dir(self, template_id: str) -> Optional[Path]:
        """Working dir for a user template, or None for built-ins."""
        if template_id in self._builtin_ids:
            return None
        settings.ensure_dirs()
        d = settings.templates_dir / template_id
        return d if d.exists() else None

    def _ensure_work_dir(self, template_id: str) -> Path:
        settings.ensure_dirs()
        d = settings.templates_dir / template_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _json_path(self, template_id: str) -> Path:
        return self._ensure_work_dir(template_id) / TEMPLATE_JSON

    def _build_builtin(self, template_id: str) -> Optional[ServiceTemplate]:
        if template_id == BUILTIN_SUNDAY_ID:
            return _default_sunday_template()
        return None

    # ---- read ------------------------------------------------------------
    def _load_users(self) -> List[ServiceTemplate]:
        settings.ensure_dirs()
        items: List[ServiceTemplate] = []
        for json_path in settings.templates_dir.glob("*/template.json"):
            try:
                tpl = ServiceTemplate.model_validate_json(
                    json_path.read_text(encoding="utf-8")
                )
                tpl.builtin = False
                items.append(tpl)
            except Exception as exc:  # noqa: BLE001
                logger.warning("跳过损坏的模板文件 %s: %s", json_path, exc)
        return items

    def list_templates(self) -> List[ServiceTemplate]:
        return [_default_sunday_template()] + self._load_users()

    def get(self, template_id: str) -> Optional[ServiceTemplate]:
        builtin = self._build_builtin(template_id)
        if builtin is not None:
            return builtin
        json_path = settings.templates_dir / template_id / TEMPLATE_JSON
        if json_path.exists():
            tpl = ServiceTemplate.model_validate_json(
                json_path.read_text(encoding="utf-8")
            )
            tpl.builtin = False
            return tpl
        return None

    @property
    def default_id(self) -> str:
        return BUILTIN_SUNDAY_ID

    # ---- write -----------------------------------------------------------
    def write_file(self, template: ServiceTemplate) -> Path:
        path = self._json_path(template.id)
        path.write_text(template.model_dump_json(indent=2), encoding="utf-8")
        return path

    def create(self, template: ServiceTemplate) -> ServiceTemplate:
        template = template.model_copy(deep=True)
        template.id = _new_id()
        template.builtin = False
        for s in template.sections:
            s.id = _new_id()
        self.write_file(template)
        return template

    def update(self, template_id: str, template: ServiceTemplate) -> ServiceTemplate:
        if template_id in self._builtin_ids:
            raise AppError("内置流程模板为只读，请先复制后再编辑")
        if self.get(template_id) is None:
            raise NotFoundError(f"流程模板不存在: {template_id}")
        template = template.model_copy(deep=True)
        template.id = template_id
        template.builtin = False
        self.write_file(template)
        return template

    def delete(self, template_id: str) -> None:
        if template_id in self._builtin_ids:
            raise AppError("内置流程模板不可删除")
        d = settings.templates_dir / template_id
        if not d.exists():
            raise NotFoundError(f"流程模板不存在: {template_id}")
        shutil.rmtree(d, ignore_errors=True)

    def duplicate(self, template_id: str) -> ServiceTemplate:
        source = self.get(template_id)
        if source is None:
            raise NotFoundError(f"流程模板不存在: {template_id}")
        copy = source.model_copy(deep=True)
        copy.id = _new_id()
        copy.builtin = False
        copy.name = f"{source.name} 副本"
        for s in copy.sections:
            s.id = _new_id()
        dest_dir = self._ensure_work_dir(copy.id)
        src_dir = self.work_dir(template_id)
        if src_dir is not None:
            refs = media_store.collect_all_media_refs(copy.sections, copy.media_assets)
            if refs:
                mapping = media_store.copy_media(src_dir, dest_dir, refs)
                media_store.rewrite_media_refs(copy.sections, mapping)
                media_store.rewrite_asset_refs(copy.media_assets, mapping)
        self.write_file(copy)
        return copy

    def from_project(
        self,
        project: Project,
        source_media_dir: Optional[Path],
        name: Optional[str] = None,
        description: str = "",
    ) -> ServiceTemplate:
        """Create a user template from a project's section skeleton + media."""
        template = ServiceTemplate(
            id=_new_id(),
            name=name or f"{project.name} 模板",
            builtin=False,
            description=description,
            slide_size=project.slide_size,
            sections=[s.model_copy(deep=True) for s in project.sections],
            media_assets=[asset.model_copy(deep=True) for asset in project.media_assets],
        )
        for s in template.sections:
            s.id = _new_id()
        dest_dir = self._ensure_work_dir(template.id)
        if source_media_dir is not None:
            refs = media_store.collect_all_media_refs(
                template.sections, template.media_assets
            )
            if refs:
                mapping = media_store.copy_media(source_media_dir, dest_dir, refs)
                media_store.rewrite_media_refs(template.sections, mapping)
                media_store.rewrite_asset_refs(template.media_assets, mapping)
        self.write_file(template)
        return template

    # ---- import / export -------------------------------------------------
    def export(self, template_id: str, out_path: Path) -> Path:
        template = self.get(template_id)
        if template is None:
            raise NotFoundError(f"流程模板不存在: {template_id}")
        work = self.work_dir(template_id)
        if work is None:
            # Built-in: materialize to a temp dir (no media) then pack.
            tmp = settings.templates_dir / f".export-{uuid4().hex[:8]}"
            tmp.mkdir(parents=True, exist_ok=True)
            try:
                (tmp / TEMPLATE_JSON).write_text(
                    template.model_dump_json(indent=2), encoding="utf-8"
                )
                return container.pack(tmp, TEMPLATE_JSON, out_path, kind="template")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        self.write_file(template)
        return container.pack(work, TEMPLATE_JSON, out_path, kind="template")

    def import_(self, container_path: Path) -> ServiceTemplate:
        tmp = settings.templates_dir / f".import-{uuid4().hex[:8]}"
        container.unpack(container_path, tmp)
        json_path = tmp / TEMPLATE_JSON
        if not json_path.exists():
            shutil.rmtree(tmp, ignore_errors=True)
            raise AppError("无效的模板容器：缺少 template.json")
        template = ServiceTemplate.model_validate_json(
            json_path.read_text(encoding="utf-8")
        )
        template.id = _new_id()
        template.builtin = False
        for s in template.sections:
            s.id = _new_id()
        target = settings.templates_dir / template.id
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        tmp.rename(target)
        # Rewrite the json with new ids (media files keep their names).
        (target / TEMPLATE_JSON).write_text(
            template.model_dump_json(indent=2), encoding="utf-8"
        )
        return template


template_store = TemplateStore()
