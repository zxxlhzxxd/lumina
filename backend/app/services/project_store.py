"""Project lifecycle: in-memory registry + working-directory persistence.

Each project lives in its own working directory `projects/<id>/` holding
`project.json` + a `media/` subfolder. The portable `.lumina` file is a zip
container produced on save-as / export and consumed on open. Legacy single-file
`<id>.lumina` JSON projects are migrated to the directory layout on load.
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import NotFoundError
from app.domain.library import Hymn, HymnLyricSection, LiturgyText
from app.domain.project import Project
from app.domain.sections import HymnSection, LiturgyTextSection
from app.services import container, media_store
from app.services.hymn_store import hymn_store
from app.services.liturgy_store import liturgy_store
from app.services.template_store import template_store

logger = logging.getLogger(__name__)

PROJECT_JSON = "project.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex


class ProjectStore:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    # ---- working dirs ----------------------------------------------------
    def work_dir(self, project_id: str) -> Path:
        settings.ensure_dirs()
        d = settings.projects_dir / project_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def media_root(self, project_id: str) -> Path:
        return self.work_dir(project_id)

    def _json_path(self, project_id: str) -> Path:
        return self.work_dir(project_id) / PROJECT_JSON

    def _reassign_ids(self, project: Project) -> Project:
        project.id = _new_id()
        for section in project.sections:
            section.id = _new_id()
        return project

    # ---- CRUD ------------------------------------------------------------
    def create(
        self,
        name: Optional[str] = None,
        date: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> Project:
        if template_id:
            template = template_store.get(template_id)
            if template is None:
                raise NotFoundError(f"流程模板不存在: {template_id}")
            project = Project(
                name=name or "未命名礼拜",
                date=date,
                slide_size=template.slide_size,
                sections=[s.model_copy(deep=True) for s in template.sections],
            )
            for section in project.sections:
                section.id = _new_id()
            # Carry template media into the project working dir.
            tpl_dir = template_store.work_dir(template_id)
            if tpl_dir is not None:
                refs = media_store.collect_media_refs(project.sections)
                if refs:
                    mapping = media_store.copy_media(
                        tpl_dir, self.work_dir(project.id), refs
                    )
                    media_store.rewrite_media_refs(project.sections, mapping)
        else:
            project = Project(name=name or "未命名礼拜", date=date)
        self._projects[project.id] = project
        self.write_file(project)
        return project

    def list(self) -> List[dict]:
        projects = sorted(
            self._projects.values(),
            key=lambda p: p.updated_at or "",
            reverse=True,
        )
        return [
            {
                "id": p.id,
                "name": p.name,
                "date": p.date,
                "section_count": len(p.sections),
                "updated_at": p.updated_at,
            }
            for p in projects
        ]

    def get(self, project_id: str) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"工程不存在: {project_id}")
        return project

    def save(self, project: Project) -> Project:
        existing = self._projects.get(project.id)
        if existing is None:
            raise NotFoundError(f"工程不存在: {project.id}")
        project.updated_at = _now()
        self._projects[project.id] = project
        return project

    def replace(self, project_id: str, project: Project) -> Project:
        if project_id not in self._projects:
            raise NotFoundError(f"工程不存在: {project_id}")
        project.id = project_id
        self._sync_content_libraries(project)
        project.updated_at = _now()
        self._projects[project_id] = project
        self.write_file(project)
        return project

    def _sync_content_libraries(self, project: Project) -> None:
        for section in project.sections:
            if isinstance(section, HymnSection):
                title = section.song_title.strip()
                if not title:
                    continue
                hymn = Hymn(
                    title=title,
                    author=section.author,
                    number=section.hymn_number,
                    sections=[
                        HymnLyricSection(order=i, text=text)
                        for i, text in enumerate(section.lyrics)
                    ],
                )
                saved = hymn_store.upsert_by_title(hymn)
                section.hymn_id = saved.id
            elif isinstance(section, LiturgyTextSection):
                title = section.slide_title.strip()
                if not title:
                    continue
                text = LiturgyText(title=title, paragraphs=section.paragraphs)
                saved = liturgy_store.upsert_by_title(text)
                section.liturgy_id = saved.id

    def delete(self, project_id: str) -> None:
        if project_id not in self._projects:
            raise NotFoundError(f"工程不存在: {project_id}")
        del self._projects[project_id]
        work = settings.projects_dir / project_id
        if work.is_dir():
            shutil.rmtree(work, ignore_errors=True)
        legacy = settings.projects_dir / f"{project_id}.lumina"
        if legacy.exists():
            legacy.unlink()

    def duplicate(self, project_id: str) -> Project:
        source = self.get(project_id)
        copy = source.model_copy(deep=True)
        src_dir = self.work_dir(project_id)
        self._reassign_ids(copy)
        copy.name = f"{source.name} 副本"
        copy.created_at = _now()
        copy.updated_at = _now()
        # Copy media into the new working dir (refs keep their names).
        src_media = src_dir / "media"
        if src_media.is_dir():
            dest_media = media_store.media_dir(self.work_dir(copy.id))
            for f in src_media.iterdir():
                if f.is_file():
                    shutil.copy2(f, dest_media / f.name)
        self._projects[copy.id] = copy
        self.write_file(copy)
        return copy

    def duplicate_section(self, project_id: str, section_id: str) -> Project:
        project = self.get(project_id)
        index = next(
            (i for i, s in enumerate(project.sections) if s.id == section_id), None
        )
        if index is None:
            raise NotFoundError(f"段落不存在: {section_id}")
        clone = project.sections[index].model_copy(deep=True)
        clone.id = _new_id()
        if clone.title:
            clone.title = f"{clone.title} 副本"
        project.sections.insert(index + 1, clone)
        project.updated_at = _now()
        return project

    # ---- media -----------------------------------------------------------
    def import_media(self, project_id: str, source_path: str) -> str:
        return media_store.import_media(self.work_dir(project_id), source_path)

    # ---- persistence -----------------------------------------------------
    def write_file(self, project: Project, path: Optional[Path] = None) -> Path:
        path = path or self._json_path(project.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return path

    def export_container(self, project_id: str, out_path: Path) -> Path:
        """Pack the project working dir into a `.lumina` zip container."""
        project = self.get(project_id)
        self.write_file(project)
        return container.pack(
            self.work_dir(project_id), PROJECT_JSON, out_path, kind="project"
        )

    def open_file(self, path: Path) -> Project:
        """Open a `.lumina` container (zip) or legacy single-file JSON."""
        path = Path(path)
        if not path.exists():
            raise NotFoundError(f"文件不存在: {path}")
        try:
            return self._open_legacy_json(path)
        except Exception:
            pass
        # Treat as a zip container.
        project = Project.model_validate_json(
            self._unpack_to_workdir(path).read_text(encoding="utf-8")
        )
        self._projects[project.id] = project
        return project

    def _open_legacy_json(self, path: Path) -> Project:
        text = path.read_text(encoding="utf-8")
        project = Project.model_validate_json(text)
        self.write_file(project)
        self._projects[project.id] = project
        return project

    def _unpack_to_workdir(self, container_path: Path) -> Path:
        # Peek the id by unpacking to a temp dir, then move into projects/<id>.
        tmp = settings.projects_dir / f".import-{uuid4().hex[:8]}"
        container.unpack(container_path, tmp)
        json_path = tmp / PROJECT_JSON
        project = Project.model_validate_json(json_path.read_text(encoding="utf-8"))
        target = settings.projects_dir / project.id
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        tmp.rename(target)
        return target / PROJECT_JSON

    def load_all_from_disk(self) -> None:
        settings.ensure_dirs()
        # New layout: projects/<id>/project.json
        for json_path in settings.projects_dir.glob("*/project.json"):
            try:
                project = Project.model_validate_json(
                    json_path.read_text(encoding="utf-8")
                )
                self._projects[project.id] = project
            except Exception as exc:  # noqa: BLE001
                logger.warning("跳过损坏的工程文件 %s: %s", json_path, exc)
        # Legacy layout: projects/<id>.lumina (plain JSON) -> migrate.
        for legacy in settings.projects_dir.glob("*.lumina"):
            try:
                project = Project.model_validate_json(
                    legacy.read_text(encoding="utf-8")
                )
                self.write_file(project)
                self._projects[project.id] = project
                legacy.unlink()
            except Exception as exc:  # noqa: BLE001
                logger.warning("跳过损坏的旧工程文件 %s: %s", legacy.name, exc)


project_store = ProjectStore()
