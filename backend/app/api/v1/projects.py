"""Project endpoints: CRUD, duplicate, media, preview, export.

Stateless `preview` / `export` operate on a posted Project so the editor can
preview/export unsaved edits. The stored-project routes handle persistence and
own the project's media working directory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.responses import ok
from app.domain.project import Project
from app.services import media_store
from app.services.export_service import export_project, validate_project
from app.services.generation import build_slides
from app.services.project_store import project_store

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectBody(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    template_id: Optional[str] = None


class ExportBody(BaseModel):
    project: Project
    path: Optional[str] = None


class ImportMediaBody(BaseModel):
    source_path: str


def _safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
    return cleaned or "lumina"


# ---- stateless operations (declared before /{id} routes) -----------------
@router.post("/preview")
def preview(project: Project) -> dict:
    slides = build_slides(project)
    return ok({"slides": [s.model_dump() for s in slides], "count": len(slides)})


@router.post("/validate")
def validate(project: Project) -> dict:
    media_root = project_store.media_root(project.id) if project.id else None
    return ok({"issues": validate_project(project, media_root=media_root)})


@router.post("/export")
def export(body: ExportBody) -> dict:
    project = body.project
    if body.path:
        out = Path(body.path)
    else:
        settings.ensure_dirs()
        out = settings.exports_dir / f"{_safe_filename(project.name)}.pptx"
    media_root = project_store.media_root(project.id) if project.id else None
    saved = export_project(project, out, media_root=media_root)
    issues = validate_project(project, media_root=media_root)
    return ok({"path": str(saved), "issues": issues})


# ---- stored projects -----------------------------------------------------
@router.post("")
def create_project(body: CreateProjectBody) -> dict:
    project = project_store.create(
        name=body.name,
        date=body.date,
        template_id=body.template_id,
    )
    return ok(project.model_dump())


@router.get("")
def list_projects() -> dict:
    return ok(project_store.list())


@router.get("/{project_id}")
def get_project(project_id: str) -> dict:
    return ok(project_store.get(project_id).model_dump())


@router.put("/{project_id}")
def update_project(project_id: str, project: Project) -> dict:
    saved = project_store.replace(project_id, project)
    return ok(saved.model_dump())


@router.delete("/{project_id}")
def delete_project(project_id: str) -> dict:
    project_store.delete(project_id)
    return ok({"deleted": project_id})


@router.post("/{project_id}/duplicate")
def duplicate_project(project_id: str) -> dict:
    return ok(project_store.duplicate(project_id).model_dump())


@router.post("/{project_id}/sections/{section_id}/duplicate")
def duplicate_section(project_id: str, section_id: str) -> dict:
    return ok(project_store.duplicate_section(project_id, section_id).model_dump())


@router.post("/{project_id}/save")
def save_to_disk(project_id: str) -> dict:
    project = project_store.get(project_id)
    path = project_store.write_file(project)
    return ok({"path": str(path)})


# ---- media ---------------------------------------------------------------
@router.post("/{project_id}/media")
def import_media(project_id: str, body: ImportMediaBody) -> dict:
    ref = project_store.import_media(project_id, body.source_path)
    return ok({"ref": ref})


@router.get("/{project_id}/media/{filename}")
def get_media(project_id: str, filename: str):
    path = media_store.media_path(project_store.work_dir(project_id), filename)
    if path is None or not path.exists():
        raise NotFoundError(f"媒体不存在: {filename}")
    return FileResponse(str(path))


@router.get("/{project_id}/export/download")
def export_download(project_id: str):
    project = project_store.get(project_id)
    settings.ensure_dirs()
    out = settings.exports_dir / f"{_safe_filename(project.name)}.pptx"
    saved = export_project(
        project, out, media_root=project_store.media_root(project_id)
    )
    return FileResponse(
        str(saved),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=saved.name,
    )
