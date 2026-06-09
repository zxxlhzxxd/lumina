"""Project lifecycle: in-memory registry + .lumina persistence.

Phase 1 stores projects as a JSON `.lumina` file (a container; media bundling
is phase 2/3). Projects are also cached in memory for the running session.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import NotFoundError
from app.domain.project import Project
from app.services.template_store import template_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex


class ProjectStore:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    # ---- helpers ---------------------------------------------------------
    def _path(self, project_id: str) -> Path:
        settings.ensure_dirs()
        return settings.projects_dir / f"{project_id}.lumina"

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
        else:
            project = Project(name=name or "未命名礼拜", date=date)
        self._projects[project.id] = project
        return project

    def list(self) -> List[dict]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "date": p.date,
                "section_count": len(p.sections),
                "updated_at": p.updated_at,
            }
            for p in self._projects.values()
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
        project.updated_at = _now()
        self._projects[project_id] = project
        return project

    def delete(self, project_id: str) -> None:
        if project_id not in self._projects:
            raise NotFoundError(f"工程不存在: {project_id}")
        del self._projects[project_id]
        path = self._path(project_id)
        if path.exists():
            path.unlink()

    def duplicate(self, project_id: str) -> Project:
        source = self.get(project_id)
        copy = source.model_copy(deep=True)
        self._reassign_ids(copy)
        copy.name = f"{source.name} 副本"
        copy.created_at = _now()
        copy.updated_at = _now()
        self._projects[copy.id] = copy
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

    # ---- persistence -----------------------------------------------------
    def write_file(self, project: Project, path: Optional[Path] = None) -> Path:
        path = path or self._path(project.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return path

    def open_file(self, path: Path) -> Project:
        if not path.exists():
            raise NotFoundError(f"文件不存在: {path}")
        project = Project.model_validate_json(path.read_text(encoding="utf-8"))
        self._projects[project.id] = project
        return project


project_store = ProjectStore()
